import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# SETTINGS
MARGIN = 10  # fixed $
LEVERAGE = 10
COOLDOWN = 30

SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]

last_trade_time = 0
last_price = {}

# ===== TELEGRAM FUNCTION =====
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ===== PRICE FETCH =====
def get_price(symbol):
    try:
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
        res = requests.get(url).json()
        return float(res['data']['price'])
    except:
        return None

# ===== SIGNAL LOGIC =====
def check_signal(symbol, price):
    global last_price

    if symbol not in last_price:
        last_price[symbol] = price
        return None

    prev = last_price[symbol]
    last_price[symbol] = price

    # breakout logic
    if price > prev * 1.001:
        return "LONG"
    elif price < prev * 0.999:
        return "SHORT"
    else:
        return None

# ===== TRADE EXECUTION (PAPER) =====
def trade(symbol, side, price):
    global last_trade_time

    position_size = MARGIN * LEVERAGE

    if symbol == "BTC-USDT":
        tp_percent = 0.002  # 0.2%
        sl_percent = 0.002
    else:
        tp_percent = 0.004  # 0.4%
        sl_percent = 0.004

    if side == "LONG":
        tp = price * (1 + tp_percent)
        sl = price * (1 - sl_percent)
    else:
        tp = price * (1 - tp_percent)
        sl = price * (1 + sl_percent)

    # MESSAGE ENTRY
    send(f"""🚀 NEW TRADE

📊 {symbol}
📍 Direction: {side}

💰 Margin: ${MARGIN}
⚡ Leverage: x{LEVERAGE}
📦 Position Size: ${position_size}

📥 Entry: {round(price,2)}
🎯 TP: {round(tp,2)}
🛑 SL: {round(sl,2)}
""")

    # ===== MONITOR TRADE =====
    while True:
        current = get_price(symbol)
        if current is None:
            continue

        if side == "LONG":
            if current >= tp:
                profit = (tp - price) / price * position_size
                send(f"""🎯 TP HIT

📊 {symbol}
💰 Profit: +${round(profit,2)}
⚡ Leverage: x{LEVERAGE}
📦 Position: ${position_size}
""")
                break

            if current <= sl:
                loss = (price - sl) / price * position_size
                send(f"""🛑 SL HIT

📊 {symbol}
❌ Loss: -${round(loss,2)}
""")
                break

        else:  # SHORT
            if current <= tp:
                profit = (price - tp) / price * position_size
                send(f"""🎯 TP HIT

📊 {symbol}
💰 Profit: +${round(profit,2)}
⚡ Leverage: x{LEVERAGE}
📦 Position: ${position_size}
""")
                break

            if current >= sl:
                loss = (sl - price) / price * position_size
                send(f"""🛑 SL HIT

📊 {symbol}
❌ Loss: -${round(loss,2)}
""")
                break

        time.sleep(2)

    last_trade_time = time.time()

# ===== MAIN LOOP =====
def main():
    send("🤖 Futures Bot Active! Ready to trade 🚀")

    while True:
        now = time.time()

        # cooldown
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
