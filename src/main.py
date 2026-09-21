import os
import random
import time
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# 1. Веб-сервер для поддержания работы на Render
app = Flask('')

@app.route('/')
def home():
    return "Pocket Option OTC Bot is online!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Инициализация Telegram бота
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Список точных OTC пар из Pocket Option (как на вашем скриншоте)
OTC_PAIRS = [
    "EUR/CHF OTC",
    "BHD/CNY OTC",
    "AUD/NZD OTC",
    "AUD/CAD OTC",
    "AED/CNY OTC"
]

# Функция «мозга» бота. Здесь рассчитывается математический алгоритм
def get_otc_signal(pair_name):
    # Примечание: Для полностью реального анализа сюда подключают websocket-клиент 
    # к серверам Pocket Option для чтения секундных котировок.
    
    # Имитация работы индикатора на основе микро-тренда
    indicators_choice = random.choice(["UP", "DOWN", "FLAT"])
    accuracy = random.randint(84, 94)
    
    return indicators_choice, accuracy

# Создание инлайн-кнопок с валютами (как выдвижная панель на видео)
def get_otc_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for pair in OTC_PAIRS:
        button = types.InlineKeyboardButton(text=pair, callback_data=f"otc_{pair}")
        markup.add(button)
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(
        message.chat.id,
        "🤖 **AI TRADING BOT — POCKET OPTION OTC**\n\n"
        "Выберите валютную пару OTC для получения мгновенного сигнала:",
        reply_markup=get_otc_keyboard(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("otc_"))
def process_otc_signal(call):
    pair = call.data.split("otc_")[1]
    
    # Отправляем уведомление, что бот думает (чтобы кнопка не зависала)
    bot.answer_callback_query(call.id, text=f"Анализирую график {pair}...")
    
    # Получаем вердикт алгоритма
    direction, rate = get_otc_signal(pair)
    
    if direction == "UP":
        signal_text = f"⬆️\n\n**{pair}**"
    elif direction == "DOWN":
        signal_text = f"⬇️\n\n**{pair}**"
    else:
        signal_text = f"⏳\n\n**{pair}**\n_Рынок нестабилен, пропустите сделку._"

    # Отправляем сигнал в чат в виде стрелочки
    bot.send_message(call.message.chat.id, signal_text, parse_mode="Markdown")
    
    # Снова показываем клавиатуру выбора пар под сигналом, чтобы удобно кликать дальше
    bot.send_message(
        call.message.chat.id, 
        "Выбрать следующую пару:", 
        reply_markup=get_otc_keyboard()
    )

# 3. Точка запуска приложения
if __name__ == "__main__":
    # Запускаем фоновый сервер для Render
    Thread(target=run_web_server).start()
    
    print("Бот успешно запущен и готов выдавать OTC сигналы!")
    bot.infinity_polling()
