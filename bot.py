import requests, time, hashlib, hmac, base64, json, uuid, os

# ====== KEYS ======
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

# ====== CHECK POSITION ======
def has_position():
    endpoint = f"/api/v1/positions?symbol={SYMBOL}"
    res = requests.get(BASE_URL + endpoint, headers=sign("GET", endpoint)).json()

    if res.get("data"):
        return True
    return False

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
    set_leverage()

    price = get_price()

    # CALCULATE TP / SL
    if side == "LONG":
        tp = price * (1 + TP_PERCENT)
        sl = price * (1 - SL_PERCENT)
    else:
        tp = price * (1 - TP_PERCENT)
        sl = price * (1 + SL_PERCENT)

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

    # TELEGRAM
    msg = f"""
🚀 TRADE OPENED

📊 Pair: {SYMBOL}
📌 Side: {side}

💰 Entry: {price:.5f}
🎯 TP: {tp:.5f}
🛑 SL: {sl:.5f}

👉 Weka manual KuCoin
"""
    send(msg)

# ====== STRATEGY ======
def strategy():
    if has_position():
        return  # ZUIA SPAM

    price = get_price()

    if int(price * 1000) % 2 == 0:
        open_trade("LONG")
    else:
        open_trade("SHORT")

# ====== START ======
send("🤖 BOT LIVE (NO SPAM MODE)")

while True:
    strategy()
    time.sleep(15)
