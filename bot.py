import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# SETTINGS
MARGIN = 10
LEVERAGE = 10
COOLDOWN = 30

SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]

last_trade_time = 0
last_price = {}
last_signal = {}

# ===== TELEGRAM =====
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ===== PRICE =====
def get_price(symbol):
    try:
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
        res = requests.get(url).json()
        return float(res['data']['price'])
    except:
        return None

# ===== SIGNAL =====
def check_signal(symbol, price):
    global last_price, last_signal

    if symbol not in last_price:
        last_price[symbol] = price
        return None

    prev = last_price[symbol]
    last_price[symbol] = price

    signal = None

    if price > prev * 1.001:
        signal = "LONG"
    elif price < prev * 0.999:
        signal = "SHORT"

    # avoid duplicate signals
    if symbol in last_signal and last_signal[symbol] == signal:
        return None

    if signal:
        last_signal[symbol] = signal

    return signal

# ===== TRADE =====
def trade(symbol, side, price):
    global last_trade_time

    position_size = MARGIN * LEVERAGE

    # BTC special TP
    if symbol == "BTC-USDT":
        tp_percent = 0.002
        sl_percent = 0.002
    else:
        tp_percent = 0.004
        sl_percent = 0.004

    if side == "LONG":
        tp = price * (1 + tp_percent)
        sl = price * (1 - sl_percent)
    else:
        tp = price * (1 - tp_percent)
        sl = price * (1 + sl_percent)

    # ENTRY MESSAGE
    send(f"""🚀 NEW TRADE

📊 {symbol}
📍 Direction: {side}

💰 Margin: ${MARGIN}
⚡ Leverage: x{LEVERAGE}
📦 Position: ${position_size}

📥 Entry: {round(price,2)}
🎯 TP: {round(tp,2)}
🛑 SL: {round(sl,2)}
""")

    # MONITOR
    while True:
        current = get_price(symbol)
        if current is None:
            continue

        # LONG
        if side == "LONG":
            if current >= tp:
                profit = (tp - price) / price * position_size
                send(f"""🎯 TP HIT

📊 {symbol}
📍 LONG

💰 Profit: +${round(profit,2)}
⚡ Leverage: x{LEVERAGE}
📦 Position: ${position_size}
""")
                break

            if current <= sl:
                loss = (price - sl) / price * position_size
                send(f"""🛑 SL HIT

📊 {symbol}
📍 LONG

❌ Loss: -${round(loss,2)}
""")
                break

        # SHORT
        else:
            if current <= tp:
                profit = (price - tp) / price * position_size
                send(f"""🎯 TP HIT

📊 {symbol}
📍 SHORT

💰 Profit: +${round(profit,2)}
⚡ Leverage: x{LEVERAGE}
📦 Position: ${position_size}
""")
                break

            if current >= sl:
                loss = (sl - price) / price * position_size
                send(f"""🛑 SL HIT

📊 {symbol}
📍 SHORT

❌ Loss: -${round(loss,2)}
""")
                break

        time.sleep(2)

    last_trade_time = time.time()

# ===== MAIN =====
def main():
    send("🤖 Futures Bot Active! Ready to trade 🚀")

    while True:
        now = time.time()

        if now - last_trade_time < COOLDOWN:
            time.sleep(2)
            continue

        for symbol in SYMBOLS:
            price = get_price(symbol)
            if price is None:
                continue

            signal = check_signal(symbol, price)

            if signal:
                trade(symbol, signal, price)

        time.sleep(5)

# RUN
if __name__ == "__main__":
    main()
