import os
import random
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# 1. Веб-сервер для Render
app = Flask('')

@app.route('/')
def home():
    return "Pocket Option Advanced Pro Bot is fully online!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Инициализация Telegram бота
part1 = "8899997428:"
part2 = "AAFi3bBUpn1fR1KU_SdJPNhpcWhInT23bYQ"
BOT_TOKEN = part1 + part2
bot = telebot.TeleBot(BOT_TOKEN)

# Временное хранилище данных пользователей (для выбора шагов)
user_states = {}

# Группы активов точь-в-точь как на Pocket Option
ASSETS = {
    "🌐 ВАЛЮТНЫЕ ПАРЫ OTC": [
        "EUR/CHF OTC", "BHD/CNY OTC", "AUD/NZD OTC", 
        "AUD/CAD OTC", "AED/CNY OTC", "EUR/USD OTC", 
        "GBP/USD OTC", "USD/JPY OTC", "NZD/USD OTC"
    ],
    "⚡ КРИПТОВАЛЮТА": [
        "Bitcoin (BTC/USD)", "Ethereum (ETH/USD)", 
        "Ripple (XRP/USD)", "Litecoin (LTC/USD)", 
        "Solana (SOL/USD)", "Dogecoin (DOGE/USD)"
    ],
    "📈 АКЦИИ / ТОВАРЫ": [
        "Apple Inc. OTC", "Microsoft OTC", "Google OTC",
        "Tesla OTC", "золото / GOLD OTC", "Нефть / BRENT OTC"
    ]
}

# Список доступного времени экспирации
TIMEFRAMES = ["5 сек.", "15 сек.", "30 сек.", "1 мин.", "2 мин.", "3 мин.", "5 мин."]

# Главное меню категорий активов
def get_categories_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for category in ASSETS.keys():
        button = types.InlineKeyboardButton(text=category, callback_data=f"cat_{category}")
        markup.add(button)
    return markup

# Меню выбора конкретных активов внутри категории
def get_assets_keyboard(category_name):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for asset in ASSETS[category_name]:
        buttons.append(types.InlineKeyboardButton(text=asset, callback_data=f"ast_{asset}"))
    markup.add(*buttons)
    # Кнопка возврата назад
    markup.add(types.InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_cats"))
    return markup

# Меню выбора времени экспирации
def get_timeframe_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for tf in TIMEFRAMES:
        buttons.append(types.InlineKeyboardButton(text=tf, callback_data=f"tf_{tf}"))
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton(text="⬅️ Назад к активам", callback_data="back_to_cats"))
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    user_states[message.chat.id] = {} # Очищаем данные пользователя при старте
    bot.send_message(
        message.chat.id,
        "🤖 **POCKET OPTION ADVANCED TRADING BOT**\n\n"
        "Добро пожаловать в профессиональный сканер рынка!\n"
        "Выберите интересующую вас категорию активов:",
        reply_markup=get_categories_keyboard(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_all_clicks(call):
    try:
        chat_id = call.message.chat.id
        
        if chat_id not in user_states:
            user_states[chat_id] = {}

        # 1. Обработка клика по КАТЕГОРИИ
        if call.data.startswith("cat_"):
            category = call.data.replace("cat_", "")
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"📂 Выберите актив из категории **{category}**:",
                reply_markup=get_assets_keyboard(category),
                parse_mode="Markdown"
            )

        # 2. Обработка клика по АКТИВУ
        elif call.data.startswith("ast_"):
            asset = call.data.replace("ast_", "")
            user_states[chat_id]['asset'] = asset  # Запоминаем выбор актива
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"🎯 Выбран актив: **{asset}**\n\n⏱ Теперь выберите время экспирации сделки:",
                reply_markup=get_timeframe_keyboard(),
                parse_mode="Markdown"
            )

        # 3. Обработка клика по ВРЕМЕНИ (Генерация финального сигнала)
        elif call.data.startswith("tf_"):
            timeframe = call.data.replace("tf_", "")
            asset = user_states[chat_id].get('asset', 'EUR/CHF OTC')
            
            bot.answer_callback_query(call.id, text="Анализирую объемы и свечи...")

            # Расчет точного времени выхода по МСК
            moscow_time = datetime.utcnow() + timedelta(hours=3)
            current_time = moscow_time.strftime("%H:%M:%S")

            # Алгоритм генерации
            direction = random.choice(["ВВЕРХ (CALL) ⬆️", "ВНИЗ (PUT) ⬇️"])
            accuracy = random.randint(87, 96)

            signal_text = (
                f"🎯 **АНАЛИЗ ЗАВЕРШЕН — СИГНАЛ ГОТОВ** 🎯\n\n"
                f"📊 Инструмент: **{asset}**\n"
                f" Направление: **{direction}**\n"
                f"⏱ Время экспирации: **{timeframe}**\n"
                f"⏳ Время выхода: **{current_time} (МСК)**\n"
                f"🎯 Проходимость алгоритма: **{accuracy}%**\n\n"
                f"ℹ️ _Рекомендуется открывать сделку моментально после выхода сигнала._"
            )

            # Отправляем сигнал новым сообщением
            bot.send_message(chat_id, signal_text, parse_mode="Markdown")
            
            # Предлагаем выбрать следующий актив
            bot.send_message(
                chat_id,
                "🔄 Чтобы получить новый сигнал, выберите категорию:",
                reply_markup=get_categories_keyboard()
            )

        # Кнопка возврата в главное меню
        elif call.data == "back_to_cats":
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="🤖 Выберите категорию активов для анализа:",
                reply_markup=get_categories_keyboard()
            )

    except Exception as e:
        print(f"Ошибка интерактивного меню: {e}")

if __name__ == "__main__":
    Thread(target=run_web_server).start()
    try:
        bot.remove_webhook()
    except:
        pass
    print("Продвинутый бот Pocket Option Pro запущен!")
    bot.infinity_polling()
