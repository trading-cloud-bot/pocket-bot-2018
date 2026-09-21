import os
import random
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

# 2. Безопасная инициализация Telegram бота через переменную окружения
# GitHub больше не будет присылать предупреждения системы безопасности!
BOT_TOKEN = os.environ.get("BOT_TOKEN")
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
        button = types.InlineKeyboardButton(text=pair, callback_data=pair)
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

@bot.callback_query_handler(func=lambda call: True)
def process_otc_signal(call):
    try:
        pair = call.data
        
        # Убираем часики загрузки с кнопки в Telegram
        bot.answer_callback_query(call.id)
        
        # Расчет точного времени по Московскому времени (UTC+3)
        moscow_time = datetime.utcnow() + timedelta(hours=3)
        current_time = moscow_time.strftime("%H:%M:%S")

        # Случайный выбор направления и проходимости сигнала
        direction = random.choice(["ВВЕРХ (CALL) ⬆️", "ВНИЗ (PUT) ⬇️"])
        accuracy = random.randint(86, 94)
        
        # Случайный выбор времени экспирации (от 1 до 3 минут)
        exp_min = random.choice([1, 2, 3])
        
        # Формируем красивый текст сигнала
        signal_text = (
            f"🎯 **СИГНАЛ СФОРМИРОВАН** 🎯\n\n"
            f"📊 Валюта: **{pair}**\n"
            f" Направление: **{direction}**\n"
            f"⏱ Экспирация: **{exp_min} мин. 00 сек.**\n"
            f"⏳ Время выхода: **{current_time} (МСК)**\n"
            f" Проходимость: **{accuracy}%**"
        )

        # Отправляем сигнал в чат
        bot.send_message(call.message.chat.id, signal_text, parse_mode="Markdown")
        
        # Снова выводим клавиатуру для удобства следующих нажатий
        bot.send_message(
            call.message.chat.id, 
            "Выбрать следующую пару:", 
            reply_markup=get_otc_keyboard()
        )
    except Exception as e:
        print(f"Ошибка при обработке кнопки: {e}")

if __name__ == "__main__":
    # Запускаем фоновый веб-сервер для Render
    Thread(target=run_web_server).start()
    
    # ФИКС БЛОКИРОВКИ: Принудительно очищаем старые вебхуки перед стартом опроса
    try:
        print("Сброс старого вебхука...")
        bot.remove_webhook()
    except Exception as e:
        print(f"Не удалось удалить вебхук: {e}")
    
    print("Бот успешно запущен в режиме постоянного опроса!")
    bot.infinity_polling()
