import telebot
import sqlite3
from telebot import types

TELEGRAM_TOKEN = 'Token  Bot'
ADMIN_ID = 123456789
DB_FILE = 'db/monitor.db'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_access = {}

def check_admin_permission(user_id):
    return user_id == ADMIN_ID  

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_access:
        user_access[user_id] = user_id  

    if message.chat.type == 'private':
        markup = types.InlineKeyboardMarkup()
        help_button = types.InlineKeyboardButton("Help", callback_data="help")
        search_text_button = types.InlineKeyboardButton("Search by Text", callback_data="search_text")
        search_id_button = types.InlineKeyboardButton("Search by ID", callback_data="search_id")

        if check_admin_permission(user_id):
            panel_button = types.InlineKeyboardButton("Panel", callback_data="panel")
            markup.add(help_button, search_text_button, search_id_button, panel_button)
        else:
            markup.add(help_button, search_text_button, search_id_button)

        bot.reply_to(message, "Welcome to the Scraper Bot! Choose an option:", reply_markup=markup)
    else:
        bot.reply_to(message, "Welcome! Please use /search or /text commands to search messages.")

@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = (
        "This bot allows you to search for messages in a database.\n\n"
        "You can search by text or by user ID.\n\n"
        "Commands:\n"
        "/text <query> <limit> - Search messages by text (e.g., /text Hello 10)\n"
        "/search <@username or chat_id> <limit> - Search messages from a specific user or chat (e.g., /search @username 10)\n\n"
        "Choose an option below to start searching."
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['text'])
def search_by_text_command(message):
    try:
        parts = message.text.split(' ', 2)
        query = parts[1]
        limit = int(parts[2]) if len(parts) > 2 else 10
        results = search_text_messages(query, limit)

        if results:
            response = f"Found {len(results)} results for '{query}':\n\n"
            for idx, (username, first_name, last_name, message_text, message_link, group_name) in enumerate(results):
                user_display = username if username else (f"{first_name or ''} {last_name or ''}" if first_name or last_name else 'None')
                response += f"{idx + 1}. {user_display}: {message_text}\n"
                response += f"Link: <a href='{message_link}'>Click here</a>\nGroup: {group_name}\n\n"
            
            bot.send_message(message.chat.id, response, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, f"No results found for '{query}'.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")

@bot.message_handler(commands=['search'])
def search_by_user_command(message):
    try:
        parts = message.text.split(' ', 2)
        user_identifier = parts[1]
        limit = int(parts[2]) if len(parts) > 2 else 10
        results = search_user_messages(user_identifier, limit)

        if results:
            response = f"Found {len(results)} messages for '{user_identifier}':\n\n"
            for idx, (username, first_name, last_name, message_text, message_link, group_name) in enumerate(results):
                user_display = username if username else (f"{first_name or ''} {last_name or ''}" if first_name or last_name else 'None')
                response += f"{idx + 1}. {user_display}: {message_text}\n"
                response += f"Link: <a href='{message_link}'>Click here</a>\nGroup: {group_name}\n\n"
            
            bot.send_message(message.chat.id, response, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, f"No results found for '{user_identifier}'.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == "search_text")
def search_by_text(call):

    msg = bot.send_message(call.message.chat.id, "Enter the text you want to search for:")
    bot.register_next_step_handler(msg, handle_text_query)

def handle_text_query(message):
    query = message.text
    msg = bot.send_message(message.chat.id, "How many results would you like to see? (Default: 10)")
    bot.register_next_step_handler(msg, handle_text_limit, query)

def handle_text_limit(message, query):
    try:
        limit = int(message.text)
    except ValueError:
        limit = 10  

    results = search_text_messages(query, limit)

    if results:
        response = f"Found {len(results)} results for '{query}':\n\n"
        for idx, (username, first_name, last_name, message_text, message_link, group_name) in enumerate(results):
            user_display = username if username else (f"{first_name or ''} {last_name or ''}" if first_name or last_name else 'None')
            response += f"{idx + 1}. {user_display}: {message_text}\n"
            response += f"Link: <a href='{message_link}'>Click here</a>\nGroup: {group_name}\n\n"
        
        bot.send_message(message.chat.id, response, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, f"No results found for '{query}'.")

@bot.callback_query_handler(func=lambda call: call.data == "search_id")
def search_by_id(call):
    msg = bot.send_message(call.message.chat.id, "Enter the username (@username) or chat ID you want to search for:")
    bot.register_next_step_handler(msg, handle_id_query)

def handle_id_query(message):
    user_identifier = message.text
    msg = bot.send_message(message.chat.id, "How many results would you like to see? (Default: 10)")
    bot.register_next_step_handler(msg, handle_id_limit, user_identifier)

def handle_id_limit(message, user_identifier):
    try:
        limit = int(message.text)
    except ValueError:
        limit = 10  

    results = search_user_messages(user_identifier, limit)

    if results:
        response = f"Found {len(results)} messages for '{user_identifier}':\n\n"
        for idx, (username, first_name, last_name, message_text, message_link, group_name) in enumerate(results):
            user_display = username if username else (f"{first_name or ''} {last_name or ''}" if first_name or last_name else 'None')
            response += f"{idx + 1}. {user_display}: {message_text}\n"
            response += f"Link: <a href='{message_link}'>Click here</a>\nGroup: {group_name}\n\n"
        
        bot.send_message(message.chat.id, response, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, f"No results found for '{user_identifier}'.")

def search_text_messages(query, limit=10):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(''' 
        SELECT username, first_name, last_name, message_text, message_link, group_name
        FROM messages
        WHERE message_text LIKE ? 
        ORDER BY datetime DESC
        LIMIT ?
    ''', ('%' + query + '%', limit))

    results = cursor.fetchall()
    conn.close()
    return results

def search_user_messages(user_identifier, limit=10):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if user_identifier.startswith('@'):
        cursor.execute(''' 
            SELECT username, first_name, last_name, message_text, message_link, group_name
            FROM messages
            WHERE username = ? 
            ORDER BY datetime DESC
            LIMIT ?
        ''', (user_identifier[1:], limit))
    else:
        cursor.execute(''' 
            SELECT username, first_name, last_name, message_text, message_link, group_name
            FROM messages
            WHERE group_id = ? 
            ORDER BY datetime DESC
            LIMIT ?
        ''', (user_identifier, limit))

    results = cursor.fetchall()
    conn.close()
    return results

bot.polling(non_stop=True)

