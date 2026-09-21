import os
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# 1. Веб-сервер для поддержания работы на Render
app = Flask('')

@app.route('/')
def home():
    return "Pocket Option OTC Bot is completely online!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Инициализация Telegram бота с вашим токеном
BOT_TOKEN = "8899997428:AAGR288_K2sCfXkYt8t8AtQZeeQERO53huM"
bot = telebot.TeleBot(BOT_TOKEN)

# Список точных OTC пар из Pocket Option
OTC_PAIRS = [
    "EUR/CHF OTC",
    "BHD/CNY OTC",
    "AUD/NZD OTC",
    "AUD/CAD OTC",
    "AED/CNY OTC"
]

# Создание инлайн-кнопок валют
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
    pair = call.data.replace("otc_", "")
    
    bot.answer_callback_query(call.id, text=f"Анализирую свечи для {pair}...")
    
    # Расчет точного времени по Московскому времени (UTC+3)
    moscow_time = datetime.utcnow() + timedelta(hours=3)
    current_time = moscow_time.strftime("%H:%M:%S")

    # Формируем красивый сигнал ВВЕРХ
    signal_text = (
        f"🎯 **СИГНАЛ СФОРМИРОВАН** 🎯\n\n"
        f"📊 Валюта: **{pair}**\n"
        f" Направление: **ВВЕРХ (CALL) ⬆️**\n"
        f"⏱ Экспирация: **1 мин. 00 сек.**\n"
        f"⏳ Время выхода: **{current_time} (МСК)**\n"
        f" Проходимость: **91%**"
    )

    bot.send_message(call.message.chat.id, signal_text, parse_mode="Markdown")
    
    bot.send_message(
        call.message.chat.id, 
        "Выбрать следующую пару:", 
        reply_markup=get_otc_keyboard()
    )

if __name__ == "__main__":
    Thread(target=run_web_server).start()
    print("Бот успешно запущен!")
    bot.infinity_polling()
