import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = f"https://api.telegram.org/bot{TOKEN}"

COINS = [
    "BTC-USDT","ETH-USDT","SOL-USDT",
    "XRP-USDT","ADA-USDT","DOGE-USDT",
    "AVAX-USDT","LINK-USDT"
]

MARGIN = 50
LEVERAGE = 20
COOLDOWN = 5
MAX_HEDGE = 2

price_history = {}
price_cache = {}
in_trade = False
last_trade_time = 0

def send(msg):
    try:
        requests.post(f"{URL}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

def get_price(symbol):
    try:
        res = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": symbol}
        ).json()
        return float(res["data"]["price"])
    except:
        return None

# ===== HISTORY =====
def update_history(symbol, price):
    if symbol not in price_history:
        price_history[symbol] = []

    price_history[symbol].append(price)

    if len(price_history[symbol]) > 5:
        price_history[symbol].pop(0)

# ===== FAST TREND DETECTION (3m STYLE) =====
def get_signal(symbol):
    h = price_history.get(symbol, [])

    if len(h) < 4:
        return None

    up = h[0] < h[1] < h[2] < h[3]
    down = h[0] > h[1] > h[2] > h[3]

    body = abs(h[-1] - h[-2])
    prev_body = abs(h[-2] - h[-3])

    if body > prev_body * 1.1:
        if up:
            return "LONG"
        if down:
            return "SHORT"

    return None

# ===== SMART SCAN =====
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

            if move > 0.0004 and move > best_move:
                best_move = move
                best = coin

        price_cache[coin] = price

    return best

# ===== TRADE =====
def trade(symbol, direction):
    global in_trade, last_trade_time

    in_trade = True

    entry = get_price(symbol)
    if not entry:
        in_trade = False
        return

    hedge = 0
    leverage = LEVERAGE
    margin = MARGIN
    peak = 0

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${margin}
⚡ x{leverage}

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

        if profit > peak:
            peak = profit

        # 🔒 TRAILING (FAST)
        if peak > 0.1:
            lock = peak * 0.6
            if profit < lock:
                send(f"🔒 EXIT +${round(profit,2)}")
                break

        # 💥 BIG TP
        if profit > 0.4:
            send(f"🎯 TP +${round(profit,2)}")
            break

        # 🔁 HEDGE
        if profit < -0.08:
            if hedge >= MAX_HEDGE:
                send(f"🛑 LOSS ${round(profit,2)}")
                break

            hedge += 1
            direction = "SHORT" if direction == "LONG" else "LONG"
            leverage = 30
            margin += 10
            entry = current

            send(f"""🔁 HEDGE {hedge}

➡️ {direction}
⚡ x{leverage}
💰 Margin: ${margin}
""")

        time.sleep(1)

    last_trade_time = time.time()
    in_trade = False

# ===== MAIN =====
def main():
    send("🤖 V7 Fast Trend Bot Active 🚀")

    while True:
        if in_trade:
            time.sleep(1)
            continue

        if time.time() - last_trade_time < COOLDOWN:
            time.sleep(1)
            continue

        coin = get_best_coin()

        if coin:
            signal = get_signal(coin)

            if signal:
                trade(coin, signal)

        time.sleep(1)

if __name__ == "__main__":
    main()
