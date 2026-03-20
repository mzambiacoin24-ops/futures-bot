import requests
import time
import os
import hmac
import hashlib
import base64
from datetime import datetime

# ===== ENV =====
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

KUCOIN_KEY = os.getenv("KUCOIN_KEY")
KUCOIN_SECRET = os.getenv("KUCOIN_SECRET")
KUCOIN_PASSPHRASE = os.getenv("KUCOIN_PASSPHRASE")

# ===== SETTINGS =====
SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
LEVERAGE = 20

# ===== TELEGRAM =====
def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

# ===== TIME =====
def trading_time():
    hour = (datetime.utcnow().hour + 3) % 24
    return 4 <= hour < 22

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

# ===== SIMPLE TREND =====
def get_direction(symbol):
    p1 = get_price(symbol)
    time.sleep(2)
    p2 = get_price(symbol)

    if p2 > p1:
        return "LONG"
    else:
        return "SHORT"

# ===== TRADE ENGINE =====
def trade(symbol, balance):
    margin = balance * 0.3  # 30% kutumia

    direction = get_direction(symbol)
    entry = get_price(symbol)

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${round(margin,2)}
⚡ x{LEVERAGE}

📥 Entry: {entry}
""")

    hedge_opened = False

    for i in range(40):  # ~40 seconds monitoring
        price = get_price(symbol)

        if direction == "LONG":
            pnl = (price - entry)/entry * margin * LEVERAGE
        else:
            pnl = (entry - price)/entry * margin * LEVERAGE

        # 🔥 HEDGE (ikiwa inakosea)
        if pnl < -0.02 and not hedge_opened:
            hedge_opened = True
            new_dir = "SHORT" if direction == "LONG" else "LONG"

            send(f"""🔁 HEDGE OPEN

Switch → {new_dir}
""")

        # 🎯 TAKE PROFIT
        if pnl > 0.05:
            send(f"""🏁 TAKE PROFIT

Profit: +${round(pnl,2)}
""")
            return

        time.sleep(1)

    send("⏹ EXIT (time end)")

# ===== BALANCE (SIMULATION FOR NOW) =====
def get_balance():
    return 4  # unaweza kubadilisha baadaye

# ===== MAIN =====
def main():
    send("🤖 V11 PRO BOT ACTIVE 🚀")

    while True:
        try:
            if not trading_time():
                time.sleep(60)
                continue

            balance = get_balance()

            for symbol in SYMBOLS:
                trade(symbol, balance)
                time.sleep(10)

            time.sleep(30)

        except Exception as e:
            send(f"🔥 ERROR: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    main()
