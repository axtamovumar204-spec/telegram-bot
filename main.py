import random
import sqlite3
import requests
import telebot

TOKEN = "8841945927:AAHsLN2z_GIkg_RMJsZev82tk2VAp4gh4-M"
bot = telebot.TeleBot(TOKEN)

def init_db():
    """Создаем базу данных и автоматически добавляем недостающие колонки."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            requests_count INTEGER DEFAULT 0
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN requests_count INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass 
        
    conn.commit()
    conn.close()

def register_or_update_user(user_id, first_name):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("INSERT INTO users (user_id, first_name, requests_count) VALUES (?, ?, 0)", (user_id, first_name))
        print(f"👤 Зарегистрирован новый пользователь: {first_name} (ID: {user_id})")
    conn.commit()
    conn.close()

def increment_user_requests(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET requests_count = requests_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, requests_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=41.3111&longitude=69.2797&current_weather=true"
        response = requests.get(url, timeout=5)
        data = response.json()
        current = data.get("current_weather", {})
        temp = current.get("temperature")
        windspeed = current.get("windspeed")
        return f"🌤️ Текущая погода:\n🌡️ Температура: {temp}°C\n💨 Скорость ветра: {windspeed} км/ч"
    except Exception as e:
        print(f"Ошибка получения погоды: {e}")
        return "Не удалось получить погоду 😢 Попробуйте позже."

jokes = [
    "— Почему программисты не любят природу?\n— Там слишком много багов. 🐛",
    "Существует 10 типов людей: те, кто понимает двоичный код, и те, кто нет. 💻",
    "— Как дела у твоего проекта?\n— Как в сказке: чем дальше, тем страшнее. 🎃",
    "Уходя из дома, выключайте свет, воду и бесконечные циклы в коде! ⚡",
    "Программист — это человек, который решает проблему, о существовании которой вы не знали, способом, который вам непонятен. 🤓"
]

def create_main_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_weather = telebot.types.KeyboardButton("🌤️ Погода")
    btn_joke = telebot.types.KeyboardButton("😂 Шутка")
    btn_stats = telebot.types.KeyboardButton("📊 Моя статистика")
    btn_about = telebot.types.KeyboardButton("ℹ️ О боте")
    
    keyboard.add(btn_weather, btn_joke, btn_stats, btn_about)
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    register_or_update_user(user_id, first_name)
    
    menu = create_main_menu()
    bot.reply_to(
        message, 
        f"Привет, {first_name}! 🚀 Я твой бот с памятью и базой данных.\nВыбери нужный пункт меню ниже 👇", 
        reply_markup=menu
    )

@bot.message_handler(func=lambda message: True)
def handle_menu_clicks(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    text = message.text
    
    register_or_update_user(user_id, first_name)
    
    if "Погода" in text:
        increment_user_requests(user_id)
        weather_text = get_weather()
        bot.reply_to(message, weather_text)
        
    elif "Шутка" in text:
        increment_user_requests(user_id)
        joke = random.choice(jokes)
        bot.reply_to(message, joke)
        
    elif "Статистика" in text or "📊" in text:
        stats = get_user_stats(user_id)
        if stats:
            name, count = stats
            bot.reply_to(message, f"👤 Пользователь: **{name}**\n📈 Всего запросов: **{count}**", parse_mode="Markdown")
        else:
            bot.reply_to(message, "Информация не найдена 🧐 Отправь /start.")
            
    elif "О боте" in text:
        bot.reply_to(message, "Я умный бот на Python! У меня есть память, SQLite база данных и кнопки! 🤖")
        
    else:
        bot.reply_to(message, f"Ты написал: {text}\nИспользуй кнопки меню для навигации! 👇")

init_db()

print("🤖 Бот с базой данных SQLite успешно запущен...")
bot.infinity_polling()
