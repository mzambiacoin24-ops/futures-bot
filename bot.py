import requests
import time
import hmac
import hashlib
import base64
import json
import uuid

# ====== WEKA HAPA TU ======
API_KEY = "69bd80471b35dd00017afdfb"

API_SECRET = "e6c7a53e-a25c-4edc-b52e-7f28bd4df1d9"
API_PASSPHRASE = "bot1234"

TELEGRAM_TOKEN = "8787267026:AAHjMfzdg9JwVxdCo6pnoiNq2o1xvU2pC30"
CHAT_ID = "7010983039"
# ==========================

BASE_URL = "https://api-futures.kucoin.com"

LEVERAGE = 5
SIZE = "1"

SYMBOLS = ["ADAUSDTM"]
    
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

# ===== LEVERAGE =====
def set_leverage(symbol):
    endpoint = "/api/v1/position/leverage"
    body = json.dumps({
        "symbol": symbol,
        "leverage": str(LEVERAGE)
    })
    requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body), data=body)

# ===== TRADE =====
def place_trade(symbol, side):
    try:
        set_leverage(symbol)

        endpoint = "/api/v1/orders"

        body = json.dumps({
            "clientOid": str(uuid.uuid4()),
            "symbol": symbol,
            "side": "buy" if side == "LONG" else "sell",
            "type": "market",
            "size": SIZE,
            "marginMode": "CROSS"   # 🔥 HII NDIO FIX YA MWISHO
        })

        res = requests.post(BASE_URL + endpoint,
                            headers=sign("POST", endpoint, body),
                            data=body).json()

        if res.get("code") == "200000":
            send(f"🚀 TRADE OPENED\n{symbol} {side}")
        else:
            send(f"❌ ORDER FAILED\n{res}")

    except Exception as e:
        send(f"ERROR: {str(e)}")

# ===== SIMPLE SCAN =====
def scan():
    import random
    return random.choice(SYMBOLS), random.choice(["LONG","SHORT"])

# ===== MAIN =====
send("🤖 BOT LIVE (FINAL FIXED)")

while True:
    try:
        send("⚡ scanning market...")

        symbol, side = scan()

        place_trade(symbol, side)

        time.sleep(8)

    except Exception as e:
        send(f"LOOP ERROR: {str(e)}")
        time.sleep(5)
