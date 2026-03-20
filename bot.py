import requests
import time
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = f"https://api.telegram.org/bot{TOKEN}"

COINS = [
    "BTC-USDT","ETH-USDT","SOL-USDT",
    "XRP-USDT","ADA-USDT","DOGE-USDT",
    "AVAX-USDT","LINK-USDT"
]

BASE_MARGIN = 10
margin = BASE_MARGIN

COOLDOWN = 5
MAX_HEDGE = 2
DAILY_TARGET = 10

price_history = {}
price_cache = {}

last_trade_time = 0
in_trade = False

daily_profit = 0
current_day = datetime.now().day

# TELEGRAM
def send(msg):
    try:
        requests.post(f"{URL}/sendMessage", data={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except:
        pass

# PRICE
def get_price(symbol):
    try:
        res = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": symbol}
        ).json()
        return float(res["data"]["price"])
    except:
        return None

# HISTORY
def update_history(symbol, price):
    if symbol not in price_history:
        price_history[symbol] = []

    price_history[symbol].append(price)

    if len(price_history[symbol]) > 6:
        price_history[symbol].pop(0)

# SIGNAL
def get_signal(symbol):
    h = price_history.get(symbol, [])

    if len(h) < 6:
        return None

    up = all(h[i] < h[i+1] for i in range(4))
    down = all(h[i] > h[i+1] for i in range(4))

    body = abs(h[-1] - h[-2])
    prev_body = abs(h[-2] - h[-3])

    if body > prev_body * 1.2:
        if up:
            return "LONG"
        if down:
            return "SHORT"

    return None

# SCAN
def get_best_coin():
    best_coin = None
    best_move = 0

    for coin in COINS:
        price = get_price(coin)
        if not price:
            continue

        update_history(coin, price)

        if coin in price_cache:
            prev = price_cache[coin]
            move = abs((price - prev) / prev)

            if move > 0.0005 and move > best_move:
                best_move = move
                best_coin = coin

        price_cache[coin] = price

    return best_coin

# TRADE
def trade(symbol, direction):
    global last_trade_time, in_trade, margin, daily_profit

    in_trade = True

    price = get_price(symbol)
    if not price:
        in_trade = False
        return

    entry = price
    leverage = 10
    hedge = 0
    peak_profit = 0

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${round(margin,2)}
⚡ Leverage: x{leverage}

📥 Entry: {round(entry,2)}
""")

    while True:
        current = get_price(symbol)
        if not current:
            continue

        position = margin * leverage

        if direction == "LONG":
            profit = (current - entry)/entry * position
        else:
            profit = (entry - current)/entry * position

        if profit > peak_profit:
            peak_profit = profit

        # 🔥 TRAILING LOCK
        if peak_profit > 0.04:
            lock = peak_profit * 0.6
            if profit < lock:
                send(f"🔒 TRAILING EXIT +${round(profit,2)}")
                daily_profit += profit
                margin += profit  # compounding
                break

        # BIG TP
        if profit > 0.2:
            send(f"🎯 BIG TP +${round(profit,2)}")
            daily_profit += profit
            margin += profit
            break

        # HEDGE
        if profit < -0.03:

            if hedge >= MAX_HEDGE:
                send(f"🛑 EXIT LOSS ${round(profit,2)}")
                daily_profit += profit
                margin += profit
                break

            hedge += 1
            direction = "SHORT" if direction == "LONG" else "LONG"

            leverage = 20 if hedge == 1 else 30
            margin += 5
            entry = current

            send(f"""🔁 HEDGE {hedge}

➡️ {direction}
⚡ x{leverage}
💰 Margin: ${round(margin,2)}
""")

        time.sleep(1)

    last_trade_time = time.time()
    in_trade = False

# MAIN
def main():
    global current_day, daily_profit

    send("🤖 V6.2 Money Bot Active 💰")

    while True:
        now_day = datetime.now().day

        # RESET DAY
        if now_day != current_day:
            current_day = now_day
            daily_profit = 0
            send("🌅 New Day Reset")

        # STOP IF TARGET HIT
        if daily_profit >= DAILY_TARGET:
            send(f"🎉 DAILY TARGET HIT: ${round(daily_profit,2)}\nBot Paused")
            time.sleep(60)
            continue

        now = time.time()

        if now - last_trade_time < COOLDOWN:
            time.sleep(1)
            continue

        symbol = get_best_coin()

        if symbol:
            direction = get_signal(symbol)

            if direction and not in_trade:
                trade(symbol, direction)

        time.sleep(1)

if __name__ == "__main__":
    main()
