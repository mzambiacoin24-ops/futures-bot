import requests
import time
import os
import base64
import hmac
import hashlib
from datetime import datetime

API_KEY = os.getenv("KUCOIN_KEY")
API_SECRET = os.getenv("KUCOIN_SECRET")
API_PASSPHRASE = os.getenv("KUCOIN_PASSPHRASE")

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = "https://api-futures.kucoin.com"

LEVERAGE = 20
trade_active = False

COINS = [
"BTCUSDTM","ETHUSDTM","SOLUSDTM","AVAXUSDTM","LINKUSDTM","ADAUSDTM",
"XRPUSDTM","DOGEUSDTM","DOTUSDTM","MATICUSDTM","OPUSDTM","ARBUSDTM"
]

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
        hmac.new(API_SECRET.encode(), str_to_sign.encode(), hashlib.sha256).digest()
    ).decode()

    passphrase = base64.b64encode(
        hmac.new(API_SECRET.encode(), API_PASSPHRASE.encode(), hashlib.sha256).digest()
    ).decode()

    return {
        "KC-API-KEY": API_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": now,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }

def get_price(symbol):
    try:
        r = requests.get(
            "https://api-futures.kucoin.com/api/v1/ticker",
            params={"symbol": symbol}
        ).json()
        return float(r["data"]["price"])
    except:
        return None

# ⚡ FAST SCAN
def find_trade():
    for coin in COINS:
        p1 = get_price(coin)
        time.sleep(0.2)
        p2 = get_price(coin)
        time.sleep(0.2)
        p3 = get_price(coin)

        if None in [p1, p2, p3]:
            continue

        if p1 < p2 < p3:
            return coin, "buy"
        elif p1 > p2 > p3:
            return coin, "sell"

    return None, None

# 💰 GET BALANCE
def get_balance():
    endpoint = "/api/v1/account-overview?currency=USDT"
    headers = sign("GET", endpoint)

    r = requests.get(BASE_URL + endpoint, headers=headers).json()

    try:
        return float(r["data"]["availableBalance"])
    except:
        return 0

# 🚀 PLACE ORDER
def place_order(symbol, side, size):
    endpoint = "/api/v1/orders"

    body = {
        "symbol": symbol,
        "side": side,
        "type": "market",
        "size": size,
        "leverage": str(LEVERAGE)
    }

    body_str = str(body).replace("'", '"')
    headers = sign("POST", endpoint, body_str)

    r = requests.post(BASE_URL + endpoint, headers=headers, data=body_str)
    return r.json()

def trade():
    global trade_active

    if trade_active:
        return

    symbol, side = find_trade()

    if symbol is None:
        send("⚡ scanning...")
        return

    balance = get_balance()

    if balance <= 1:
        send("⚠️ Low balance")
        return

    margin = balance * 0.3
    size = int(margin * LEVERAGE / get_price(symbol))

    trade_active = True

    send(f"""🚀 REAL TRADE

📊 {symbol}
📍 {side.upper()}

💰 Margin: ${round(margin,2)}
⚡ x{LEVERAGE}
""")

    res = place_order(symbol, side, size)

    send(f"✅ Order placed")

    time.sleep(10)

    trade_active = False

def main():
    send("🤖 V20 REAL BOT LIVE 🚀")

    while True:
        try:
            trade()
            time.sleep(3)
        except Exception as e:
            send(f"ERROR: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    main()
