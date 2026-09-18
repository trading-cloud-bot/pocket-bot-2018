import os
import telebot
from telebot import types
from flask import Flask, request
from tradingview_ta import TA_Handler, Interval

# Инициализируем бота из переменной окружения Render
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Настройка Flask для работы Webhook на Render
app = Flask(__name__)

# Функция для получения реального технического анализа с TradingView
def get_trading_signal(symbol, exchange, screener):
    try:
        handler = TA_Handler(
            symbol=symbol,
            exchange=exchange,
            screener=screener,
            interval=Interval.INTERVAL_1_MINUTE  # Анализ рынка на 1-минутном графике
        )
        analysis = handler.get_analysis()
        summary = analysis.summary['RECOMMENDATION']
        
        # Переводим рекомендации в красивый цветной формат
        if "STRONG_BUY" in summary:
            return f"🟢🟢 **STRONG BUY / АКТИВНО ПОКУПАТЬ**\n📈 Тренд: Сильный бычий"
        elif "BUY" in summary:
            return f"🟢 **BUY / ПОКУПАТЬ**\n📈 Тренд: Восходящий"
        elif "STRONG_SELL" in summary:
            return f"🔴🔴 **STRONG SELL / АКТИВНО ПРОДАВАТЬ**\n📉 Тренд: Сильный медвежий"
        elif "SELL" in summary:
            return f"🔴 **SELL / ПРОДАВАТЬ**\n📉 Тренд: Нисходящий"
        else:
            return f"🟡 **NEUTRAL / НЕЙТРАЛЬНО**\n⏳ Рекомендуется подождать"
    except Exception as e:
        return f"❌ Ошибка получения данных / Error getting data"

# Стартовое меню с двуязычными кнопками
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_currency = types.KeyboardButton("💱 Валюта / Currency")
    btn_commodities = types.KeyboardButton("👑 Товары / Commodities")
    btn_crypto = types.KeyboardButton("🪙 Крипта / Crypto")
    
    markup.add(btn_currency)
    markup.add(btn_commodities)
    markup.add(btn_crypto)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Выберите категорию для анализа:\nHello! Select a category for analysis:", 
        reply_markup=markup
    )

# Обработка нажатий на двуязычные кнопки
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    # Временное сообщение, чтобы пользователь видел, что бот думает
    status_msg = bot.send_message(message.chat.id, "🔄 Анализируем рынок... / Analyzing market...")
    
    if message.text == "💱 Валюта / Currency":
        # Анализируем EURUSD на стабильном форекс-коннекторе FX
        signal = get_trading_signal("EURUSD", "FX", "forex")
        response = f"📊 **Пара: EUR/USD (Forex)**\n\n{signal}\n\n⏱ Экспирация / Expiration: 1-5 min"
        
    elif message.text == "👑 Товары / Commodities":
        # Анализируем Золото (GOLD) на бирже TVC
        signal = get_trading_signal("GOLD", "TVC", "cfd")
        response = f"📊 **Актив: GOLD / Золото**\n\n{signal}\n\n⏱ Экспирация / Expiration: 1-5 min"
        
    elif message.text == "🪙 Крипта / Crypto":
        # Анализируем Bitcoin (BTCUSDT) на бирже BINANCE
        signal = get_trading_signal("BTCUSDT", "BINANCE", "crypto")
        response = f"📊 **Пара: BTC/USDT (Crypto)**\n\n{signal}\n\n⏱ Экспирация / Expiration: 1-5 min"
    else:
        response = "❓ Неизвестная команда / Unknown command"
        
    # Удаляем временное сообщение "Анализируем рынок" и присылаем готовый сигнал
    bot.delete_message(message.chat.id, status_msg.message_id)
    bot.send_message(message.chat.id, response, parse_mode="Markdown")

# Настройки сервера вебхуков для Render
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://' + request.host + '/' + TOKEN)
    return "Bot is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
