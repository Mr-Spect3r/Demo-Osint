import os
import json
from telethon import TelegramClient
import asyncio

ACCOUNTS_FOLDER = 'accounts'
os.makedirs(ACCOUNTS_FOLDER, exist_ok=True)
ACCOUNTS_FILE = os.path.join(ACCOUNTS_FOLDER, 'accounts.json')

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {"accounts": []}
    with open(ACCOUNTS_FILE, 'r') as f:
        return json.load(f)

def save_accounts(data):
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def add_account():
    phone = input("Enter phone number (with +): ")
    api_id = int(input("Enter API ID: "))
    api_hash = input("Enter API Hash: ")

    session_file = f"session_{phone.replace('+','')}.json"
    client = TelegramClient(os.path.join(ACCOUNTS_FOLDER, session_file), api_id, api_hash)
    await client.start(phone)

    me = await client.get_me()

    name = me.username if me.username else me.first_name if me.first_name else "nop"

    data = load_accounts()
    accounts = data.get("accounts", [])
    for a in accounts:
        if a["phone"] == phone:
            print(f"Account {phone} already exists in accounts.json")
            await client.disconnect()
            return

    account_info = {
        "name": name,
        "id": me.id,
        "phone": phone,
        "api_id": api_id,
        "api_hash": api_hash,
        "session_file": session_file
    }

    accounts.append(account_info)
    data["accounts"] = accounts
    save_accounts(data)

    print(f"Account {phone} added with ID {me.id}, name: {name}")
    await client.disconnect()

async def list_accounts():
    data = load_accounts()
    accounts = data.get("accounts", [])
    if not accounts:
        print("No accounts found.")
        return
    for a in accounts:
        print(f"{a['phone']} - {a['name']} ({a['id']})")

async def main():
    print("1) Add account\n2) List accounts")
    choice = input("Choose: ")
    if choice == '1':
        await add_account()
    elif choice == '2':
        await list_accounts()

if __name__ == '__main__':
    asyncio.run(main())