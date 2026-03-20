import requests
import time
import os
import base64
import hmac
import hashlib
import json

API_KEY = os.getenv("KUCOIN_KEY")
API_SECRET = os.getenv("KUCOIN_SECRET")
API_PASSPHRASE = os.getenv("KUCOIN_PASSPHRASE")

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = "https://api-futures.kucoin.com"

LEVERAGE = 20
trade_active = False
TOTAL_PROFIT = 0
TARGET_PROFIT = 0.05

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
        r = requests.get(BASE_URL + "/api/v1/ticker", params={"symbol": symbol}).json()
        return float(r["data"]["price"])
    except:
        return None

def get_balance():
    endpoint = "/api/v1/account-overview?currency=USDT"
    headers = sign("GET", endpoint)

    r = requests.get(BASE_URL + endpoint, headers=headers).json()

    try:
        return float(r["data"]["availableBalance"])
    except:
        return 0

# ✅ FIXED POSITION READER
def get_position(symbol):
    endpoint = f"/api/v1/position?symbol={symbol}"
    headers = sign("GET", endpoint)

    r = requests.get(BASE_URL + endpoint, headers=headers).json()

    try:
        data = r.get("data", {})
        qty = float(data.get("currentQty", 0))

        if qty != 0:
            return {
                "size": abs(qty),
                "entry": float(data.get("avgEntryPrice", 0)),
                "pnl": float(data.get("unrealisedPnl", 0))
            }
    except:
        pass

    return None

def place_order(symbol, side, size):
    endpoint = "/api/v1/orders"

    body = {
        "symbol": symbol,
        "side": side,
        "type": "market",
        "size": size,
        "leverage": str(LEVERAGE)
    }

    body_str = json.dumps(body)
    headers = sign("POST", endpoint, body_str)

    return requests.post(BASE_URL + endpoint, headers=headers, data=body_str).json()

def find_trade():
    for coin in COINS:
        p1 = get_price(coin)
        time.sleep(0.2)
        p2 = get_price(coin)

        if None in [p1, p2]:
            continue

        diff = (p2 - p1) / p1

        if diff > 0.0002:
            return coin, "buy"
        elif diff < -0.0002:
            return coin, "sell"

    return None, None

def trade():
    global trade_active, TOTAL_PROFIT

    if trade_active:
        return

    symbol, side = find_trade()
    if symbol is None:
        return

    balance = get_balance()
    if balance <= 1:
        send("⚠️ Balance ndogo")
        return

    price = get_price(symbol)
    if price is None:
        return

    margin = balance * 0.3
    position_value = margin * LEVERAGE
    size = int(position_value / price)

    trade_active = True

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {side.upper()}

💰 Margin: ${round(margin,2)}
⚡ Leverage: x{LEVERAGE}
📦 Position: ${round(position_value,2)}

📥 Entry: {round(price,4)}

💵 Total Profit: ${round(TOTAL_PROFIT,4)}
""")

    place_order(symbol, side, size)

    time.sleep(3)

    while True:
        pos = get_position(symbol)

        if pos is None:
            time.sleep(1)
            continue

        pnl = pos["pnl"]

        if pnl >= TARGET_PROFIT:
            close_side = "sell" if side == "buy" else "buy"
            place_order(symbol, close_side, pos["size"])

            TOTAL_PROFIT += pnl

            send(f"""✅ TP HIT

💰 +${round(pnl,4)}
💵 Total: ${round(TOTAL_PROFIT,4)}
""")

            trade_active = False
            return

        time.sleep(1)

def main():
    send("🤖 V25 REAL BOT CONNECTED 🚀")

    while True:
        try:
            trade()
            time.sleep(1)
        except Exception as e:
            send(f"ERROR: {str(e)}")
            time.sleep(3)

if __name__ == "__main__":
    main()
