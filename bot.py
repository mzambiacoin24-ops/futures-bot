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

LEVERAGE = 20
MAX_HEDGE = 2

price_history = {}
price_cache = {}

in_trade = False
last_trade_time = 0

daily_profit = 0
current_day = datetime.utcnow().day  # use UTC base

# ===== SEND =====
def send(msg):
    try:
        requests.post(f"{URL}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ===== RESET =====
def reset_day():
    global daily_profit, current_day
    tz_day = (datetime.utcnow().hour + 3) // 24 + datetime.utcnow().day
    if tz_day != current_day:
        current_day = tz_day
        daily_profit = 0
        send("🔄 New Day — Reset Done (TZ)")

# ===== TIME (TZ) =====
def trading_time():
    hour = (datetime.utcnow().hour + 3) % 24
    return 4 <= hour < 16

# ===== PRICE =====
def get_price(symbol):
    try:
        r = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": symbol}
        ).json()
        return float(r["data"]["price"])
    except:
        return None

# ===== HISTORY =====
def update_history(symbol, price):
    if symbol not in price_history:
        price_history[symbol] = []
    price_history[symbol].append(price)
    if len(price_history[symbol]) > 5:
        price_history[symbol].pop(0)

# ===== SIGNAL =====
def get_signal(symbol):
    h = price_history.get(symbol, [])
    if len(h) < 4:
        return None

    up = h[0] < h[1] < h[2] < h[3]
    down = h[0] > h[1] > h[2] > h[3]

    if up:
        return "LONG"
    if down:
        return "SHORT"

    return None

# ===== SCAN =====
def get_best_coin():
    best = None
    best_move = 0

    for coin in COINS:
        price = get_price(coin)
        if not price:
            continue

        update_history(coin, price)

        if coin in price_cache:
            prev = price_cache[coin]
            move = abs((price - prev) / prev)

            if move > 0.0003 and move > best_move:
                best_move = move
                best = coin

        price_cache[coin] = price

    return best

# ===== TRADE =====
def trade(symbol, direction, margin, daily_target):
    global in_trade, daily_profit

    in_trade = True

    entry = get_price(symbol)
    hedge = 0
    peak = 0

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${round(margin,2)}
⚡ x{LEVERAGE}

📥 Entry: {round(entry,2)}
""")

    while True:
        price = get_price(symbol)
        if not price:
            continue

        position = margin * LEVERAGE

        if direction == "LONG":
            profit = (price - entry)/entry * position
        else:
            profit = (entry - price)/entry * position

        if profit > peak:
            peak = profit

        # 🔒 TRAILING
        if peak > 0.5:
            lock = peak * 0.6
            if profit < lock:
                send(f"🔒 EXIT +${round(profit,2)}")
                daily_profit += profit
                break

        # 🎯 DAILY TARGET
        if daily_profit + profit >= daily_target:
            send(f"🏁 TARGET HIT +${round(daily_profit + profit,2)}")
            daily_profit += profit
            break

        # 🔁 HEDGE
        if profit < -1:
            if hedge >= MAX_HEDGE:
                send(f"🛑 LOSS ${round(profit,2)}")
                daily_profit += profit
                break

            hedge += 1
            direction = "SHORT" if direction == "LONG" else "LONG"
            margin += margin * 0.2
            entry = price

            send(f"""🔁 HEDGE {hedge}
➡️ {direction}
💰 Margin: ${round(margin,2)}
""")

        time.sleep(1)

    in_trade = False

# ===== MAIN =====
def main():
    send("🤖 V8 TZ Bot Active 🇹🇿🚀")

    while True:
        reset_day()

        if not trading_time():
            time.sleep(30)
            continue

        if in_trade:
            time.sleep(1)
            continue

        balance = 100  # demo balance
        margin = balance * 0.5
        daily_target = margin * 0.5

        if daily_profit >= daily_target:
            time.sleep(60)
            continue

        coin = get_best_coin()

        if coin:
            signal = get_signal(coin)
            if signal:
                trade(coin, signal, margin, daily_target)

        time.sleep(1)

if __name__ == "__main__":
    main()
