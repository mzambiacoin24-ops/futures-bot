import requests, time, hashlib, hmac, base64, json, uuid, os

# ====== WEKA HIZI TU ======
API_KEY = os.getenv("KUCOIN_KEY")
API_SECRET = os.getenv("KUCOIN_SECRET")
API_PASSPHRASE = os.getenv("KUCOIN_PASSPHRASE")

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ====== SETTINGS ======
SYMBOL = "ADAUSDTM"
LEVERAGE = 3
SIZE = 10

TP_PERCENT = 0.005
SL_PERCENT = 0.003

BASE_URL = "https://api-futures.kucoin.com"

has_long = False
has_short = False

# ====== TELEGRAM ======
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ====== SIGN ======
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

# ====== PRICE ======
def get_price():
    url = f"{BASE_URL}/api/v1/ticker?symbol={SYMBOL}"
    return float(requests.get(url).json()['data']['price'])

# ====== SET LEVERAGE ======
def set_leverage():
    endpoint = "/api/v1/position/risk-limit-level/change"
    body = json.dumps({
        "symbol": SYMBOL,
        "leverage": str(LEVERAGE)
    })
    requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body), data=body)

# ====== OPEN TRADE ======
def open_trade(side):
    global has_long, has_short

    if side == "LONG" and has_long:
        return
    if side == "SHORT" and has_short:
        return

    set_leverage()

    price = get_price()
    tp = price * (1 + TP_PERCENT) if side == "LONG" else price * (1 - TP_PERCENT)
    sl = price * (1 - SL_PERCENT) if side == "LONG" else price * (1 + SL_PERCENT)

    endpoint = "/api/v1/orders"

    body = json.dumps({
        "clientOid": str(uuid.uuid4()),
        "symbol": SYMBOL,
        "side": "buy" if side == "LONG" else "sell",
        "type": "market",
        "size": SIZE,
        "marginMode": "cross",
        "positionSide": side
    })

    requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body), data=body)

    # ====== MANUAL TP/SL LOGIC ======
    monitor_trade(side, tp, sl)

    msg = f"""
🚀 TRADE OPENED
{SYMBOL}
{side}

Entry: {price:.5f}
TP: {tp:.5f}
SL: {sl:.5f}
"""
    send(msg)

    if side == "LONG":
        has_long = True
    else:
        has_short = True

# ====== MONITOR TP/SL ======
def monitor_trade(side, tp, sl):
    global has_long, has_short

    while True:
        price = get_price()

        if side == "LONG":
            if price >= tp or price <= sl:
                close_position("LONG")
                has_long = False
                break
        else:
            if price <= tp or price >= sl:
                close_position("SHORT")
                has_short = False
                break

        time.sleep(3)

# ====== CLOSE ======
def close_position(side):
    endpoint = "/api/v1/orders"
    body = json.dumps({
        "clientOid": str(uuid.uuid4()),
        "symbol": SYMBOL,
        "side": "sell" if side == "LONG" else "buy",
        "type": "market",
        "size": SIZE,
        "marginMode": "cross",
        "positionSide": side
    })

    requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body), data=body)

    send(f"✅ CLOSED {side}")

# ====== SIMPLE STRATEGY ======
def strategy():
    price = get_price()

    if int(price * 1000) % 2 == 0:
        open_trade("LONG")
    else:
        open_trade("SHORT")

# ====== LOOP ======
send("🤖 BOT LIVE (SMART + HEDGE + TP/SL)")

while True:
    strategy()
    time.sleep(10)
