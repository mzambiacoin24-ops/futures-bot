import time
import requests
import hashlib
import hmac
import base64
import uuid
import json

# ====== WEKA HIZI TU ======
API_KEY = "69bd80471b35dd00017afdfb"
API_SECRET = "e6c7a53e-a25c-4edc-b52e-7f28bd4df1d9"
API_PASSPHRASE = "bot1234"

TELEGRAM_TOKEN = "8787267026:AAHjMfzdg9JwVxdCo6pnoiNq2o1xvU2pC30"
CHAT_ID = "7010983039"
# ==========================

BASE_URL = "https://api-futures.kucoin.com"

SYMBOLS = [
    "BTCUSDTM","ETHUSDTM","SOLUSDTM","XRPUSDTM","ADAUSDTM",
    "DOGEUSDTM","LINKUSDTM","AVAXUSDTM","DOTUSDTM","LTCUSDTM"
]

LEVERAGE = 20
SIZE = 0.01


# ===== TELEGRAM =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    try:
        requests.post(url, data=data)
    except:
        pass


# ===== SIGN =====
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


# ===== SET LEVERAGE =====
def set_leverage(symbol):
    endpoint = "/api/v1/position/leverage"
    body = json.dumps({
        "symbol": symbol,
        "leverage": LEVERAGE,
        "marginMode": "ISOLATED"
    })
    requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body), data=body)


# ===== PLACE TRADE =====
def place_trade(symbol, side):
    endpoint = "/api/v1/orders"

    client_oid = str(uuid.uuid4())

    body = json.dumps({
        "clientOid": client_oid,
        "symbol": symbol,
        "side": "buy" if side == "LONG" else "sell",
        "type": "market",
        "leverage": str(LEVERAGE),
        "marginMode": "ISOLATED",
        "size": SIZE
    })

    res = requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body), data=body).json()

    if "code" in res and res["code"] != "200000":
        send_telegram(f"❌ ORDER FAILED\n{res}")
    else:
        send_telegram(f"🚀 TRADE START\n{symbol} {side}\n💰 Size: {SIZE}")


# ===== GET PRICE =====
def get_price(symbol):
    try:
        r = requests.get(BASE_URL + f"/api/v1/ticker?symbol={symbol}").json()
        return float(r["data"]["price"])
    except:
        return None


# ===== MAIN SCAN =====
def scan():
    send_telegram("🤖 BOT LIVE (REAL TRADING STARTED)")

    while True:
        send_telegram("⚡ scanning market...")

        for symbol in SYMBOLS:
            price = get_price(symbol)

            if price:
                if price % 2 < 1:
                    set_leverage(symbol)
                    place_trade(symbol, "LONG")
                    time.sleep(2)
                else:
                    set_leverage(symbol)
                    place_trade(symbol, "SHORT")
                    time.sleep(2)

        time.sleep(3)


# ===== RUN =====
scan()
