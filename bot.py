import requests, time, hashlib, hmac, base64, json, uuid, os

# ===== KEYS =====
API_KEY = os.getenv("KUCOIN_KEY")
API_SECRET = os.getenv("KUCOIN_SECRET")
API_PASSPHRASE = os.getenv("KUCOIN_PASSPHRASE")

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ===== SETTINGS =====
SYMBOL = "ADAUSDTM"
SIZE = 10
LEVERAGE = 3

TP_PERCENT = 0.005
SL_PERCENT = 0.003

BASE_URL = "https://api-futures.kucoin.com"

# ===== GLOBAL STATE =====
current_position = None
entry_price = None
tp = None
sl = None
prices = []

# ===== TELEGRAM =====
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

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

# ===== PRICE =====
def get_price():
    url = f"{BASE_URL}/api/v1/ticker?symbol={SYMBOL}"
    return float(requests.get(url).json()['data']['price'])

# ===== TREND (SMART B) =====
def get_trend(price):
    prices.append(price)

    if len(prices) < 10:
        return None

    ema = sum(prices[-10:]) / 10

    if price > ema:
        return "LONG"
    else:
        return "SHORT"

# ===== OPEN TRADE =====
def open_trade(side):
    global current_position, entry_price, tp, sl

    price = get_price()

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

    current_position = side
    entry_price = price

    send(f"""
🚀 TRADE OPENED

📊 {SYMBOL}
📌 {side}

💰 Entry: {price:.5f}
🎯 TP: {tp:.5f}
🛑 SL: {sl:.5f}
""")

# ===== CLOSE =====
def close_trade():
    global current_position, entry_price

    if current_position is None:
        return

    endpoint = "/api/v1/orders"

    body = json.dumps({
        "clientOid": str(uuid.uuid4()),
        "symbol": SYMBOL,
        "side": "sell" if current_position == "LONG" else "buy",
        "type": "market",
        "size": SIZE,
        "marginMode": "cross",
        "positionSide": current_position
    })

    requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body), data=body)

    price = get_price()

    if current_position == "LONG":
        profit = price - entry_price
    else:
        profit = entry_price - price

    send(f"""
❌ TRADE CLOSED

📌 {current_position}
💰 Exit: {price:.5f}
📊 PnL: {profit:.5f}
""")

    current_position = None

# ===== MAIN ENGINE =====
def run_bot():
    global current_position

    price = get_price()
    trend = get_trend(price)

    if current_position is None:
        if trend:
            open_trade(trend)
        return

    # TP / SL
    if current_position == "LONG" and price >= tp:
        close_trade()

    elif current_position == "SHORT" and price <= tp:
        close_trade()

    elif current_position == "LONG" and price <= sl:
        close_trade()

    elif current_position == "SHORT" and price >= sl:
        close_trade()

    # TREND CHANGE
    elif trend and trend != current_position:
        close_trade()
        open_trade(trend)

# ===== START =====
send("🤖 BOT LIVE (SMART + AUTO TP/SL + REVERSE)")

while True:
    run_bot()
    time.sleep(10)
