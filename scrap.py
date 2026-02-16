import os
import json
import asyncio
import aiosqlite
from telethon import TelegramClient, events
import re

ACCOUNTS_FOLDER = 'accounts'
DB_FOLDER = 'db'
os.makedirs(DB_FOLDER, exist_ok=True)
ACCOUNTS_FILE = os.path.join(ACCOUNTS_FOLDER, 'accounts.json')
DB_FILE = os.path.join(DB_FOLDER, 'monitor.db')


async def init_db():
    conn = await aiosqlite.connect(DB_FILE)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT,
            account_phone TEXT,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            message_id INTEGER,
            message_text TEXT,
            message_link TEXT,
            group_id INTEGER,
            group_name TEXT,
            datetime TEXT,
            UNIQUE(user_id, message_id, group_id)  
        )
    ''')
    await conn.commit()
    return conn

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    with open(ACCOUNTS_FILE, 'r') as f:
        data = json.load(f)
        return data.get("accounts", [])

async def save_message(conn, account_name, account_phone, data):
    try:
        await conn.execute('''
            INSERT OR IGNORE INTO messages (
                account_name, account_phone, user_id, username, first_name, last_name, phone,
                message_id, message_text, message_link, group_id, group_name, datetime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            account_name,
            account_phone,
            data.get('user_id'),
            data.get('username'),
            data.get('first_name'),
            data.get('last_name'),
            data.get('phone'),
            data.get('message_id'),
            data.get('message_text', ''),
            data.get('message_link', ''),
            data.get('group_id'),
            data.get('group_name', ''),
            data.get('datetime')
        ))
        await conn.commit()
        print(f"[{account_name}][{account_phone}] ({data.get('group_name')}) {data.get('username')}: {data.get('message_text')}")
    except Exception as e:
        print("Error saving message:", e)

async def monitor_account(account, conn):
    client = TelegramClient(
        os.path.join(ACCOUNTS_FOLDER, account['session_file']),
        account['api_id'],
        account['api_hash']
    )
    await client.start()
    account_name = account['name']
    account_phone = account['phone']

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        chat_id = getattr(entity, 'id', None)
        chat_name = getattr(entity, 'title', getattr(entity, 'username', str(entity)))
        username = getattr(entity, 'username', None)

        if username:
            base_link = f"https://t.me/{username}"
        else:
            base_link = f"https://t.me/c/{str(chat_id)[4:]}" if str(chat_id).startswith('-100') else None

        async for msg in client.iter_messages(entity, reverse=True, limit=None):
            user = await msg.get_sender()
            message_link = f"{base_link}/{msg.id}" if base_link else f"(private/{msg.id})"

            data = {
                'user_id': getattr(user, 'id', None),
                'username': getattr(user, 'username', None),
                'first_name': getattr(user, 'first_name', None),
                'last_name': getattr(user, 'last_name', None),
                'phone': getattr(user, 'phone', None),
                'message_id': msg.id,
                'message_text': msg.text or '',
                'message_link': message_link,
                'group_id': chat_id,
                'group_name': chat_name,
                'datetime': msg.date.isoformat()
            }
            await save_message(conn, account_name, account_phone, data)

    @client.on(events.NewMessage())
    async def handler(event):
        msg = event.message
        chat = await event.get_chat()
        user = await event.get_sender()

        chat_id = getattr(chat, 'id', None)
        chat_name = getattr(chat, 'title', getattr(chat, 'username', str(chat)))
        username = getattr(chat, 'username', None)

        if username:
            base_link = f"https://t.me/{username}"
        else:
            base_link = f"https://t.me/c/{str(chat_id)[4:]}" if str(chat_id).startswith('-100') else None

        message_link = f"{base_link}/{msg.id}" if base_link else f"(private/{msg.id})"

        data = {
            'user_id': getattr(user, 'id', None),
            'username': getattr(user, 'username', None),
            'first_name': getattr(user, 'first_name', None),
            'last_name': getattr(user, 'last_name', None),
            'phone': getattr(user, 'phone', None),
            'message_id': msg.id,
            'message_text': msg.text or '',
            'message_link': message_link,
            'group_id': chat_id,
            'group_name': chat_name,
            'datetime': msg.date.isoformat()
        }
        await save_message(conn, account_name, account_phone, data)

    print(f"Monitoring started for {account_name} ({account_phone})")
    await client.run_until_disconnected()

async def main():
    conn = await init_db()
    accounts = load_accounts()
    if not accounts:
        print("No accounts found in accounts.json")
        return

    tasks = [monitor_account(acc, conn) for acc in accounts]

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())