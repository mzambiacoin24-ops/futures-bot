import requests
import time
import hmac
import hashlib
import base64
import json
import uuid
import os

# ========= WEKA HIZI TU =========
API_KEY = "69bd80471b35dd00017afdfb"
API_SECRET = "e6c7a53e-a25c-4edc-b52e-7f28bd4df1d9"
API_PASSPHRASE = "bot1234"

TELEGRAM_TOKEN = "8787267026:AAHjMfzdg9JwVxdCo6pnoiNq2o1xvU2pC30"
CHAT_ID = "7010983039"
# ===============================

BASE_URL = "https://api-futures.kucoin.com"

LEVERAGE = 20
TRADE_SIZE = 1
CHECK_SPEED = 3

COINS = [
    "BTCUSDTM","ETHUSDTM","SOLUSDTM",
    "XRPUSDTM","ADAUSDTM","LINKUSDTM",
    "AVAXUSDTM","DOGEUSDTM"
]

# ===== TELEGRAM =====
def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

# ===== SIGN =====
def sign(method, endpoint, body=""):
    now = str(int(time.time()*1000))
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

# ===== PRICE =====
def get_price(symbol):
    try:
        r = requests.get(BASE_URL + "/api/v1/ticker", params={"symbol": symbol}).json()
        return float(r["data"]["price"])
    except:
        return None

# ===== LEVERAGE =====
def set_leverage(symbol):
    endpoint = "/api/v1/position/leverage"
    body = json.dumps({
        "symbol": symbol,
        "leverage": str(LEVERAGE)
    })
    requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body), data=body)

# ===== ORDER =====
def place_trade(symbol, side):
    try:
        set_leverage(symbol)

        endpoint = "/api/v1/orders"
        body = json.dumps({
            "clientOid": str(uuid.uuid4()),
            "symbol": symbol,
            "side": "buy" if side == "LONG" else "sell",
            "type": "market",
            "size": TRADE_SIZE
        })

        res = requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body), data=body).json()

        if res.get("code") == "200000":
            send(f"""🚀 TRADE OPENED

🪙 {symbol}
📍 {side}
⚡ Leverage: x{LEVERAGE}
📦 Size: {TRADE_SIZE}
""")
            return True
        else:
            send(f"❌ ORDER FAILED\n{res}")
            return False

    except Exception as e:
        send(f"ERROR: {str(e)}")
        return False

# ===== STRATEGY (SMART ENTRY) =====
def find_entry():
    for coin in COINS:
        p1 = get_price(coin)
        time.sleep(0.3)
        p2 = get_price(coin)

        if None in [p1, p2]:
            continue

        move = (p2 - p1) / p1

        if move > 0.0003:
            return coin, "LONG"
        elif move < -0.0003:
            return coin, "SHORT"

    return None, None

# ===== MAIN =====
send("🤖 BOT LIVE (CROSS + AUTO LEVERAGE)")

while True:
    try:
        send("⚡ scanning market...")

        symbol, side = find_entry()

        if symbol:
            place_trade(symbol, side)
        else:
            send("⏳ no entry")

        time.sleep(CHECK_SPEED)

    except Exception as e:
        send(f"LOOP ERROR: {str(e)}")
        time.sleep(5)
