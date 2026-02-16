import sqlite3
import os

DB_FOLDER = 'db'
DB_FILE = os.path.join(DB_FOLDER, 'monitor.db')

if not os.path.exists(DB_FILE):
    print("Database not found:", DB_FILE)
    exit(1)

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("SELECT id, account_name, account_phone, user_id, first_name, last_name, username, message_text, group_name, datetime, message_link FROM messages ORDER BY id DESC LIMIT 50")
rows = cursor.fetchall()

print(f"{'ID':<5} {'Account Name':<20} {'Account Phone':<15} {'UserID':<10} {'Sender Name':<20} {'Message':<50} {'Group':<20} {'Date':<20} {'Link'}")
print("-"*200)

for row in rows:
    _id, account_name, account_phone, user_id, first_name, last_name, username, message_text, group_name, datetime, message_link = row

    sender_name = f"{first_name} {last_name}" if first_name or last_name else username or "(Unknown)"

    msg_preview = (message_text[:45] + "...") if len(message_text) > 45 else message_text
    message_link = message_link if message_link else "(No link)"
    print(f"{_id:<5} {account_name:<20} {account_phone:<15} {user_id:<10} {sender_name:<20} {msg_preview:<50} {group_name:<20} {datetime:<20} {message_link}")

conn.close()