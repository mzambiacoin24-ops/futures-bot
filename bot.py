import requests
import time
import os
import hmac
import hashlib
import base64
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

KUCOIN_KEY = os.getenv("KUCOIN_KEY")
KUCOIN_SECRET = os.getenv("KUCOIN_SECRET")
KUCOIN_PASSPHRASE = os.getenv("KUCOIN_PASSPHRASE")

BASE_URL = "https://api-futures.kucoin.com"

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

def get_price(symbol):
    try:
        r = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": symbol}
        ).json()
        return float(r["data"]["price"])
    except:
        return None

def trading_time():
    hour = (datetime.utcnow().hour + 3) % 24
    return 4 <= hour < 22

def trade(symbol, direction, margin):
    entry = get_price(symbol)

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${round(margin,2)}
⚡ x20

📥 Entry: {entry}
""")

    hedge_opened = False

    for i in range(30):  # seconds loop
        price = get_price(symbol)

        if direction == "LONG":
            pnl = (price - entry)/entry * margin * 20
        else:
            pnl = (entry - price)/entry * margin * 20

        # 🔥 HEDGE TRIGGER
        if pnl < -0.03 and not hedge_opened:
            hedge_opened = True
            new_direction = "SHORT" if direction == "LONG" else "LONG"

            send(f"""🔁 HEDGE ACTIVATED

Switch to {new_direction}
""")

        time.sleep(1)

    send(f"🏁 CLOSED (monitor end)")

def main():
    send("🤖 V10.9 REAL HEDGE START 🇹🇿")

    while True:
        try:
            if not trading_time():
                time.sleep(60)
                continue

            margin = 2  # keep fixed for testing

            trade("BTC-USDT", "LONG", margin)

            time.sleep(60)

        except Exception as e:
            send(f"🔥 ERROR: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    main()
