import requests
import time
import os
import base64
import hmac
import hashlib

API_KEY = os.getenv("KUCOIN_KEY")
API_SECRET = os.getenv("KUCOIN_SECRET")
API_PASSPHRASE = os.getenv("KUCOIN_PASSPHRASE")

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = "https://api-futures.kucoin.com"

LEVERAGE = 20
trade_active = False

COINS = [
"BTCUSDTM","ETHUSDTM","SOLUSDTM","LINKUSDTM",
"AVAXUSDTM","DOGEUSDTM","XRPUSDTM","ADAUSDTM"
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

# ⚡ ULTRA FAST ENTRY
def find_trade():
    for coin in COINS:
        p1 = get_price(coin)
        time.sleep(0.15)
        p2 = get_price(coin)

        if None in [p1, p2]:
            continue

        diff = (p2 - p1) / p1

        # 🔥 micro movement entry
        if diff > 0.0002:
            return coin, "buy"
        elif diff < -0.0002:
            return coin, "sell"

    return None, None

def get_balance():
    endpoint = "/api/v1/account-overview?currency=USDT"
    headers = sign("GET", endpoint)

    r = requests.get(BASE_URL + endpoint, headers=headers).json()

    try:
        return float(r["data"]["availableBalance"])
    except:
        return 0

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

    return requests.post(BASE_URL + endpoint, headers=headers, data=body_str).json()

def trade():
    global trade_active

    if trade_active:
        return

    symbol, side = find_trade()

    if symbol is None:
        return

    balance = get_balance()

    if balance <= 1:
        send("⚠️ Balance ndogo")
        return

    margin = balance * 0.3
    price = get_price(symbol)

    if price is None:
        return

    size = int(margin * LEVERAGE / price)

    trade_active = True

    send(f"""⚡ SCALP ENTRY

📊 {symbol}
📍 {side.upper()}

💰 ${round(margin,2)}
⚡ x{LEVERAGE}
""")

    place_order(symbol, side, size)

    entry = price

    # 🎯 ULTRA SMALL TP
    if side == "buy":
        tp = entry * 1.0005
    else:
        tp = entry * 0.9995

    for i in range(60):
        p = get_price(symbol)
        if p is None:
            continue

        if side == "buy":
            if p >= tp:
                place_order(symbol, "sell", size)
                send(f"💰 TP HIT (+scalp)")
                trade_active = False
                return
        else:
            if p <= tp:
                place_order(symbol, "buy", size)
                send(f"💰 TP HIT (+scalp)")
                trade_active = False
                return

        time.sleep(0.5)

    # 🔴 FAST EXIT (no waiting forever)
    place_order(symbol, "sell" if side == "buy" else "buy", size)
    send("⚠️ Quick exit")

    trade_active = False

def main():
    send("⚡ V21 ULTRA SCALPER LIVE")

    while True:
        try:
            trade()
            time.sleep(1)
        except Exception as e:
            send(f"ERROR: {str(e)}")
            time.sleep(3)

if __name__ == "__main__":
    main()
