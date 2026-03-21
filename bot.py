import time
import requests
import hashlib
import hmac
import base64
import uuid
import json

API_KEY = "69bd80471b35dd00017afdfb"
API_SECRET = "
e6c7a53e-a25c-4edc-b52e-7f28bd4df1d9"
API_PASSPHRASE = "bot1234"

BASE_URL = "https://api-futures.kucoin.com"

SYMBOLS = [
    "BTCUSDTM","ETHUSDTM","SOLUSDTM","XRPUSDTM","ADAUSDTM",
    "DOGEUSDTM","LINKUSDTM","AVAXUSDTM","DOTUSDTM","LTCUSDTM"
]

LEVERAGE = 20
MARGIN_USDT = 1.2


def sign(method, endpoint, body=""):
    now = str(int(time.time() * 1000))
    str_to_sign = now + method + endpoint + body
    signature = base64.b64encode(
        hmac.new(API_SECRET.encode(), str_to_sign.encode(), hashlib.sha256).digest()
    ).decode()

    passphrase = base64.b64encode(
        hmac.new(API_SECRET.encode(), API_PASSPHRASE.encode(), hashlib.sha256).digest()
    ).decode()

    headers = {
        "KC-API-KEY": API_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": now,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }
    return headers


def set_leverage(symbol):
    endpoint = "/api/v1/position/leverage"
    url = BASE_URL + endpoint

    body = json.dumps({
        "symbol": symbol,
        "leverage": LEVERAGE,
        "marginMode": "ISOLATED"
    })

    headers = sign("POST", endpoint, body)
    requests.post(url, headers=headers, data=body)


def place_trade(symbol, side):
    endpoint = "/api/v1/orders"
    url = BASE_URL + endpoint

    client_oid = str(uuid.uuid4())

    body = json.dumps({
        "clientOid": client_oid,
        "symbol": symbol,
        "side": "buy" if side == "LONG" else "sell",
        "type": "market",
        "leverage": str(LEVERAGE),
        "marginMode": "ISOLATED",
        "size": 0.01
    })

    headers = sign("POST", endpoint, body)
    res = requests.post(url, headers=headers, data=body).json()

    if "code" in res and res["code"] != "200000":
        print(f"❌ ORDER FAILED: {res}")
    else:
        print(f"✅ REAL TRADE: {symbol} {side}")


def get_price(symbol):
    url = BASE_URL + f"/api/v1/ticker?symbol={symbol}"
    try:
        return float(requests.get(url).json()['data']['price'])
    except:
        return None


def scan():
    while True:
        print("⚡ scanning fast...")
        for symbol in SYMBOLS:
            price = get_price(symbol)
            if price:
                # simple logic (scalp)
                if price % 2 < 1:
                    set_leverage(symbol)
                    place_trade(symbol, "LONG")
                    time.sleep(2)
                else:
                    set_leverage(symbol)
                    place_trade(symbol, "SHORT")
                    time.sleep(2)

        time.sleep(1)


print("🚀 V31 TRUE REAL BOT LIVE")
scan()
