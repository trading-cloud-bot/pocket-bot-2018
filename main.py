import telebot
from telebot import types
import urllib.request
import json

# === НАСТРОЙКИ TELEGRAM ===
BOT_TOKEN = "8899997428:AAGR288_K2sCfXkYt8t8AtQZeeQERO53huM"
bot = telebot.TeleBot(BOT_TOKEN)

# === КАТАЛОГ ВСЕХ ПРИБЫЛЬНЫХ АКТИВОВ POCKET OPTION ===
CATEGORIES = {
    "💱 6 ТОП ВАЛЮТНЫХ ПАР": {
        "EUR/USD": "EURUSDT", "GBP/USD": "GBPUSDT", "USD/JPY": "JPYUSDT",
        "AUD/USD": "AUDUSDT", "USD/CAD": "CADUSDT", "USD/CHF": "CHFUSDT"
    },
    "🪙 ЗОЛОТО, НЕФТЬ И СЫРЬЕ": {
        "Золото (Gold)": "PAXGUSDT", "Серебро (Silver)": "XAGUSDT", "Нефть Brent": "OILUSDT"
    },
    "⚡ ТОП КРИПТОВАЛЮТА": {
        "Bitcoin (BTC)": "BTCUSDT", "Ethereum (ETH)": "ETHUSDT", "Solana (SOL)": "SOLUSDT",
        "Litecoin (LTC)": "LTCUSDT", "Ripple (XRP)": "XRPUSDT"
    }
}

ALL_ASSETS = {}
for cat_assets in CATEGORIES.values():
    ALL_ASSETS.update(cat_assets)

# === ВРЕМЯ ЭКСПИРАЦИИ (КАК НА POCKET OPTION) ===
TIMEFRAMES = {
    "⏱ 5 секунд": {"label": "5 сек", "limit": 30, "interval": "1"},
    "⏱ 30 секунд": {"label": "30 сек", "limit": 40, "interval": "1"},
    "⏱ 1 минута": {"label": "1 мин", "limit": 30, "interval": "1"},
    "⏱ 2 минуты": {"label": "2 мин", "limit": 35, "interval": "1"},
    "⏱ 3 минуты": {"label": "3 мин", "limit": 40, "interval": "1"},
    "⏱ 5 минут": {"label": "5 мин", "limit": 50, "interval": "5"}
}

USER_STATE = {}

# === ДВОЙНОЙ АНАЛИЗ РЫНКА (RSI + SMA) ===
def get_advanced_analysis(symbol, interval, limit):
    try:
        url = f"https://bybit.com{symbol}&interval={interval}&limit={limit}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode())
        if 'result' not in res_data or 'list' not in res_data['result']:
            return None, None, None
        candles = res_data['result']['list']
        if len(candles) < 20:
            return None, None, None
        candles.reverse()
        closes = [float(candle) for candle in candles]
        last_price = closes[-1]
        gains, losses = [], []
        for i in range(1, len(closes)):
            delta = closes[i] - closes[i-1]
            gains.append(delta if delta > 0 else 0.0)
            losses.append(abs(delta) if delta < 0 else 0.0)
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        if avg_loss == 0:
            rsi = 100.0 if avg_gain > 0 else 50.0
        else:
            rsi = 100 - (100 / (1 + (avg_gain / avg_loss)))
        sma_20 = sum(closes[-20:]) / 20
        return last_price, rsi, sma_20
    except:
        return None, None, None

def get_categories_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    buttons = [types.KeyboardButton(cat_name) for cat_name in CATEGORIES.keys()]
    markup.add(*buttons)
    return markup

def get_assets_inline(category_name):
    markup = types.InlineKeyboardMarkup(row_width=2)
    assets = CATEGORIES[category_name]
    buttons = [types.InlineKeyboardButton(text=name, callback_data=f"asset_{name}") for name in assets.keys()]
    markup.add(*buttons)
    return markup

def get_timeframe_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=tf_name, callback_data=f"tf_{tf_name}") for tf_name in TIMEFRAMES.keys()]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "📂 **Торговая панель Pocket Option**\nВыберите категорию активов:", 
        reply_markup=get_categories_keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text in CATEGORIES)
def handle_category(message):
    bot.send_message(
        message.chat.id, 
        f"📋 Активы категории *{message.text}*:\nВыберите инструмент для торговли:", 
        reply_markup=get_assets_inline(message.text),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("asset_"))
def handle_asset_choice(call):
    asset_name = call.data.replace("asset_", "")
    symbol = ALL_ASSETS.get(asset_name)
    USER_STATE[call.message.chat.id] = {"asset_name": asset_name, "symbol": symbol}
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"⏱ **Актив выбран: {asset_name}**\n\nТеперь выберите **время экспирации (время сделки)**, как на Pocket Option:",
        reply_markup=get_timeframe_inline(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("tf_"))
def handle_timeframe_choice(call):
    tf_name = call.data.replace("tf_", "")
    chat_id = call.message.chat.id
    if chat_id not in USER_STATE:
        bot.send_message(chat_id, "⚠️ Ошибка сессии. Пожалуйста, введите /start заново.")
        return
    state = USER_STATE[chat_id]
    asset_name = state["asset_name"]
    symbol = state["symbol"]
    bot.answer_callback_query(call.id, text=f"Анализирую под {tf_name}...")
    tf_config = TIMEFRAMES[tf_name]
    price, rsi, sma = get_advanced_analysis(symbol, tf_config["interval"], tf_config["limit"])
    if price is None or rsi is None or sma is None:
        bot.send_message(chat_id, "❌ Не удалось получить котировки. Попробуйте еще раз.")
        return
    fmt = ".5f" if "USD" in asset_name and "/" in asset_name else ".2f"
    if rsi <= 35 and price < sma:
        verdict = f"🟢 **СИГНАЛ: ВРЕМЯ ПОКУПКИ!**\n📥 **В Pocket Option:** Жмите **ВВЕРХ (Зеленая)** 📈\n⏱ **Время:** {tf_config['label']}\n🎯 _Идеальный момент для отскока цены наверх!_"
    elif rsi >= 65 and price > sma:
        verdict = f"🔴 **СИГНАЛ: ВРЕМЯ ДЛЯ ПРОДАЖИ!**\n📤 **В Pocket Option:** Жмите **ВНИЗ (Красная)** 📉\n⏱ **Время:** {tf_config['label']}\n🎯 _Идеальный момент для отскока цены вниз!_"
    else:
        verdict = f"⏳ **НЕЙТРАЛЬНАЯ ЗОНА (Ожидание)**\n📊 Для таймфрейма {tf_config['label']} четкого разворота нет.\n👉 _Рекомендация: Попробуйте выбрать другое время или другой актив._"
    response = (
        f"📊 **АНАЛИЗ: {asset_name}**\n"
        f"⏱ **Время экспирации:** {tf_name}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 **Живая цена:** {price:{fmt}}\n"
        f"📈 **Индекс RSI:** {rsi:.2f}\n"
        f"📉 **Линия тренда SMA:** {sma:{fmt}}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{verdict}"
    )
    bot.send_message(chat_id, response, parse_mode="Markdown")

if __name__ == "__main__":
    print("🚀 Робот Pocket Option с таймфреймами успешно запущен!")
    bot.infinity_polling()
