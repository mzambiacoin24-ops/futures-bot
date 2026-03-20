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

BASE_URL = "https://api.kucoin.com"

# ===== TELEGRAM =====
def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ===== SIGN =====
def sign(method, endpoint, body=""):
    now = str(int(time.time() * 1000))
    str_to_sign = now + method + endpoint + body

    signature = base64.b64encode(
        hmac.new(KUCOIN_SECRET.encode(), str_to_sign.encode(), hashlib.sha256).digest()
    ).decode()

    passphrase = base64.b64encode(
        hmac.new(KUCOIN_SECRET.encode(), KUCOIN_PASSPHRASE.encode(), hashlib.sha256).digest()
    ).decode()

    headers = {
        "KC-API-KEY": KUCOIN_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": now,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2"
    }

    return headers

# ===== BALANCE =====
def get_balance():
    endpoint = "/api/v1/accounts"
    headers = sign("GET", endpoint)

    try:
        res = requests.get(BASE_URL + endpoint, headers=headers).json()
        for acc in res["data"]:
            if acc["currency"] == "USDT":
                return float(acc["available"])
    except:
        return 0

    return 0

# ===== PRICE =====
def get_price(symbol):
    try:
        r = requests.get(
            BASE_URL + "/api/v1/market/orderbook/level1",
            params={"symbol": symbol}
        ).json()
        return float(r["data"]["price"])
    except:
        return None

# ===== TIME TZ =====
def trading_time():
    hour = (datetime.utcnow().hour + 3) % 24
    return 4 <= hour < 16

# ===== TRADE (SIMULATED EXECUTION FOR NOW) =====
def trade(symbol, direction, margin):
    entry = get_price(symbol)

    send(f"""🚀 LIVE TRADE

📊 {symbol}
📍 {direction}

💰 Margin: ${round(margin,2)}
⚡ x20

📥 Entry: {entry}
""")

    time.sleep(5)

    exit_price = get_price(symbol)

    if direction == "LONG":
        profit = (exit_price - entry)/entry * margin * 20
    else:
        profit = (entry - exit_price)/entry * margin * 20

    send(f"🏁 CLOSED +${round(profit,2)}")

# ===== MAIN =====
def main():
    send("🤖 V9 KuCoin Bot Active 🚀")

    while True:
        if not trading_time():
            time.sleep(30)
            continue

        balance = get_balance()

        if balance <= 1:
            send(f"⚠️ No balance detected (${balance})")
            time.sleep(60)
            continue

        send(f"💰 Balance: ${balance}")

        margin = balance * 0.5

        coin = "BTC-USDT"
        direction = "LONG"

        trade(coin, direction, margin)

        time.sleep(60)

if __name__ == "__main__":
    main()
