import os
import random
from datetime import datetime
import zoneinfo  # Для точного времени по МСК
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# 1. Веб-сервер для поддержания работы на Render
app = Flask('')

@app.route('/')
def home():
    return "Pocket Option OTC Bot with Timer is online!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Инициализация Telegram бота
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

# Имитация работы алгоритма
def get_otc_signal():
    direction = random.choice(["UP", "DOWN", "FLAT"])
    accuracy = random.randint(84, 95)
    return direction, accuracy

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
    
    # Отправляем уведомление в шторку Telegram, что идет расчет
    bot.answer_callback_query(call.id, text=f"Анализирую секундные свечи для {pair}...")
    
    # Получаем вердикт алгоритма
    direction, rate = get_otc_signal()
    
    # Получаем точное текущее время по Москве (часы, минуты, секунды)
    try:
        moscow_tz = zoneinfo.ZoneInfo("Europe/Moscow")
        current_time = datetime.now(moscow_tz).strftime("%H:%M:%S")
    except Exception:
        current_time = datetime.now().strftime("%H:%M:%S") # Резервный вариант, если часовой пояс не загрузился

    # Настройка случайного времени экспирации (например, 1 минута 00 секунд или 2 минуты 30 секунд)
    exp_minutes = random.choice([1, 2, 3])
    exp_seconds = random.choice([0, 30])
    
    if exp_seconds == 0:
        timeframe_str = f"{exp_minutes} мин. 00 сек."
    else:
        timeframe_str = f"{exp_minutes} мин. {exp_seconds} сек."

    # Формируем красивый сигнал
    if direction == "UP":
        signal_text = (
            f"🎯 **СИГНАЛ СФОРМИРОВАН** 🎯\n\n"
            f"📊 Валюта: **{pair}**\n"
            f" Направление: **ВВЕРХ (CALL) ⬆️**\n"
            f"⏱ Экспирация: **{timeframe_str}**\n"
            f"⏳ Время выхода: **{current_time} (МСК)**\n"
            f" Проходимость: **{rate}%**"
        )
    elif direction == "DOWN":
        signal_text = (
            f"🎯 **СИГНАЛ СФОРМИРОВАН** 🎯\n\n"
            f"📊 Валюта: **{pair}**\n"
            f" Направление: **ВНИЗ (PUT) ⬇️**\n"
            f"⏱ Экспирация: **{timeframe_str}**\n"
            f"⏳ Время выхода: **{current_time} (МСК)**\n"
            f" Проходимость: **{rate}%**"
        )
    else:
        signal_text = (
            f"📊 Валюта: **{pair}**\n"
            f"⏳ Время анализа: **{current_time}**\n"
            f"⚠️ **ВНИМАНИЕ**: Индикаторы показывают неопределенность (Флэт). Рекомендуется пропустить эту сделку!"
        )

    # Отправляем оформленный сигнал пользователю
    bot.send_message(call.message.chat.id, signal_text, parse_mode="Markdown")
    
    # Повторно выводим меню выбора пар под сигналом
    bot.send_message(
        call.message.chat.id, 
        "Выбрать следующую пару:", 
        reply_markup=get_otc_keyboard()
    )

# 3. Точка запуска приложения
if __name__ == "__main__":
    Thread(target=run_web_server).start()
    print("Бот с таймерами минут/секунд запущен!")
    bot.infinity_polling()
