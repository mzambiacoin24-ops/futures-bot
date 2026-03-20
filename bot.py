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

active_trade = False  # 🔥 muhimu kwa hedging

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

def sign(method, endpoint, body=""):
    now = str(int(time.time() * 1000))
    str_to_sign = now + method + endpoint + body

    signature = base64.b64encode(
        hmac.new(KUCOIN_SECRET.encode(), str_to_sign.encode(), hashlib.sha256).digest()
    ).decode()

    passphrase = base64.b64encode(
        hmac.new(KUCOIN_SECRET.encode(), KUCOIN_PASSPHRASE.encode(), hashlib.sha256).digest()
    ).decode()

    return {
        "KC-API-KEY": KUCOIN_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": now,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }

def trading_time():
    hour = (datetime.utcnow().hour + 3) % 24
    return 4 <= hour < 22

def get_balance():
    endpoint = "/api/v1/account-overview?currency=USDT"
    headers = sign("GET", endpoint)
    try:
        res = requests.get(BASE_URL + endpoint, headers=headers).json()
        if res.get("code") != "200000":
            return 0
        return float(res["data"]["availableBalance"])
    except:
        return 0

def get_price(symbol):
    try:
        r = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": symbol}
        ).json()
        return float(r["data"]["price"])
    except:
        return None

def trade(symbol, direction, margin):
    global active_trade
    active_trade = True

    entry = get_price(symbol)

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${round(margin,2)}
⚡ x20

📥 Entry: {entry}
""")

    time.sleep(30)

    exit_price = get_price(symbol)

    if direction == "LONG":
        profit = (exit_price - entry)/entry * margin * 20
    else:
        profit = (entry - exit_price)/entry * margin * 20

    send(f"🏁 CLOSED +${round(profit,2)}")

    active_trade = False  # 🔥 trade imeisha

def main():
    send("🤖 V10.8 HEDGE BASE BOT ACTIVE 🇹🇿")

    while True:
        try:
            if not trading_time():
                time.sleep(60)
                continue

            if active_trade:
                time.sleep(5)
                continue

            balance = get_balance()

            if balance <= 1:
                time.sleep(60)
                continue

            margin = balance * 0.5

            # 👇 bado LONG kwa sasa (hatujafanya hedge bado)
            trade("BTC-USDT", "LONG", margin)

            time.sleep(5)

        except Exception as e:
            send(f"🔥 ERROR: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    main()
