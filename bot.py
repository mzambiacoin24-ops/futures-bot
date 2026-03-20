import requests
import time
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
LEVERAGE = 20

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

def trading_time():
    hour = (datetime.utcnow().hour + 3) % 24
    return 4 <= hour < 22

def get_price(symbol):
    try:
        r = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": symbol}
        ).json()
        return float(r["data"]["price"])
    except:
        return None

def pick_symbol():
    best = None
    best_move = 0

    for s in SYMBOLS:
        p1 = get_price(s)
        time.sleep(1)
        p2 = get_price(s)

        move = abs(p2 - p1)

        if move > best_move:
            best_move = move
            best = s

    return best

def get_direction(symbol):
    p1 = get_price(symbol)
    time.sleep(2)
    p2 = get_price(symbol)

    return "LONG" if p2 > p1 else "SHORT"

def trade(balance):
    symbol = pick_symbol()
    direction = get_direction(symbol)

    margin = balance * 0.5
    entry = get_price(symbol)

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${round(margin,2)}
⚡ x{LEVERAGE}

📥 Entry: {entry}
""")

    hedge = False

    for i in range(120):  # 2 minutes
        price = get_price(symbol)

        if direction == "LONG":
            pnl = (price - entry)/entry * margin * LEVERAGE
        else:
            pnl = (entry - price)/entry * margin * LEVERAGE

        # LIVE STATUS
        if i % 10 == 0:
            send(f"📊 RUNNING PNL: ${round(pnl,3)}")

        # HEDGE
        if pnl < -0.01 and not hedge:
            hedge = True
            new_dir = "SHORT" if direction == "LONG" else "LONG"

            send(f"""🔁 HEDGE ACTIVATED

Switch → {new_dir}
""")

        # TAKE PROFIT
        if pnl > 0.05:
            send(f"""🏁 PROFIT CLOSED

💰 +${round(pnl,2)}
""")
            return

        time.sleep(1)

    send("⏹ EXIT (timeout)")

def get_balance():
    return 4

def main():
    send("🤖 V12 CORE BOT ACTIVE 🚀")

    while True:
        try:
            if not trading_time():
                time.sleep(60)
                continue

            balance = get_balance()

            if balance < 1:
                send("⚠️ Balance ndogo")
                time.sleep(60)
                continue

            trade(balance)

            time.sleep(20)

        except Exception as e:
            send(f"🔥 ERROR: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    main()
