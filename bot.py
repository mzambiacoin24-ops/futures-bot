import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = f"https://api.telegram.org/bot{TOKEN}"

# SETTINGS
MARGIN_BASE = 10
LEVERAGE = 10
COOLDOWN = 5

COINS = [
    "BTC-USDT","ETH-USDT","SOL-USDT",
    "XRP-USDT","ADA-USDT","DOGE-USDT",
    "AVAX-USDT","LINK-USDT"
]

price_cache = {}
last_trade_time = 0

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

# SCANNER (PERCENT BASED 🔥)
def get_best_coin():
    best_coin = None
    best_move = 0

    for coin in COINS:
        price = get_price(coin)
        if not price:
            continue

        if coin in price_cache:
            prev = price_cache[coin]

            if prev > 0:
                move_percent = abs((price - prev) / prev)

                if move_percent > best_move:
                    best_move = move_percent
                    best_coin = coin

        price_cache[coin] = price

    return best_coin

# TRADE ENGINE
def trade(symbol):
    global last_trade_time

    price = get_price(symbol)
    if not price:
        return

    prev = price_cache.get(symbol, price)
    direction = "LONG" if price > prev else "SHORT"

    margin = MARGIN_BASE
    position = margin * LEVERAGE
    entry = price

    send(f"""🚀 TRADE START

📊 {symbol}
📍 Direction: {direction}

💰 Margin: ${margin}
⚡ Leverage: x{LEVERAGE}
📦 Position: ${position}

📥 Entry: {round(entry,2)}
""")

    step = 0

    while step < 3:
        current = get_price(symbol)
        if not current:
            continue

        # LONG
        if direction == "LONG":
            tp = entry * 1.0006
            sl = entry * 0.9994

            if current >= tp:
                profit = (tp - entry)/entry * position
                send(f"""🎯 TP HIT

📊 {symbol}
💰 Profit: +${round(profit,2)}
⚡ x{LEVERAGE}
""")
                break

            if current <= sl:
                step += 1
                direction = "SHORT"
                margin += 5
                position = margin * LEVERAGE
                entry = current

                send(f"""🔁 HEDGE

➡️ SWITCH TO SHORT
💰 Margin: ${margin}
📥 Entry: {round(entry,2)}
""")

        # SHORT
        else:
            tp = entry * 0.9994
            sl = entry * 1.0006

            if current <= tp:
                profit = (entry - tp)/entry * position
                send(f"""🎯 TP HIT

📊 {symbol}
💰 Profit: +${round(profit,2)}
⚡ x{LEVERAGE}
""")
                break

            if current >= sl:
                step += 1
                direction = "LONG"
                margin += 5
                position = margin * LEVERAGE
                entry = current

                send(f"""🔁 HEDGE

➡️ SWITCH TO LONG
💰 Margin: ${margin}
📥 Entry: {round(entry,2)}
""")

        time.sleep(1)

    last_trade_time = time.time()

# MAIN
def main():
    send("🤖 Smart Futures Bot V3 Active 🚀")

    while True:
        now = time.time()

        if now - last_trade_time < COOLDOWN:
            time.sleep(1)
            continue

        symbol = get_best_coin()

        if symbol:
            trade(symbol)

        time.sleep(2)

# RUN
if __name__ == "__main__":
    main()
