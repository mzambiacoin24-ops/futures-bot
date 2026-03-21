import requests, time, json, hmac, hashlib, base64, uuid

# ==============================
# 🔑 WEKA TAARIFA ZAKO HAPA
# ==============================

API_KEY = "69bd80471b35dd00017afdfb"
API_SECRET = "e6c7a53e-a25c-4edc-b52e-7f28bd4df1d9
"
API_PASSPHRASE = "bot1234"

TELEGRAM_TOKEN = "8787267026:AAHjMfzdg9JwVxdCo6pnoiNq2o1xvU2pC30"
CHAT_ID = "7010983039"

# ==============================
# ⚙️ SETTINGS
# ==============================

BASE_URL = "https://api-futures.kucoin.com"

SYMBOL = "ADAUSDTM"     # coin moja tu
LEVERAGE = 5
SIZE = "1"
TAKE_PROFIT = 0.2       # profit ya haraka (badilisha 0.1–0.5)

# ==============================
# 📩 TELEGRAM
# ==============================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ==============================
# 🔐 SIGNATURE
# ==============================

def get_headers(method, endpoint, body=""):
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

# ==============================
# 📊 ANGALIA POSITION
# ==============================

def get_position():
    endpoint = "/api/v1/positions"
    res = requests.get(BASE_URL + endpoint, headers=get_headers("GET", endpoint, ""))
    data = res.json()

    if "data" in data:
        for pos in data["data"]:
            if pos["symbol"] == SYMBOL and float(pos["currentQty"]) != 0:
                return pos
    return None

# ==============================
# ⚡ SET LEVERAGE
# ==============================

def set_leverage():
    endpoint = "/api/v1/position/leverage"
    body = json.dumps({
        "symbol": SYMBOL,
        "leverage": str(LEVERAGE)
    })

    requests.post(BASE_URL + endpoint,
        headers=get_headers("POST", endpoint, body),
        data=body
    )

# ==============================
# 🚀 OPEN TRADE
# ==============================

def open_trade(side):
    if get_position():
        send_telegram("⏳ Ninasubiri trade ifungwe...")
        return

    set_leverage()

    endpoint = "/api/v1/orders"
    body = json.dumps({
        "clientOid": str(uuid.uuid4()),
        "symbol": SYMBOL,
        "side": "buy" if side == "LONG" else "sell",
        "type": "market",
        "size": SIZE,
        "marginMode": "CROSS"
    })

    res = requests.post(BASE_URL + endpoint,
        headers=get_headers("POST", endpoint, body),
        data=body
    )

    data = res.json()

    if data.get("code") == "200000":
        send_telegram(f"🚀 TRADE OPENED {SYMBOL} {side}")
        return side
    else:
        send_telegram(f"❌ {data}")
        return None

# ==============================
# 💰 CLOSE TRADE
# ==============================

def close_trade(side):
    endpoint = "/api/v1/orders"

    close_side = "sell" if side == "LONG" else "buy"

    body = json.dumps({
        "clientOid": str(uuid.uuid4()),
        "symbol": SYMBOL,
        "side": close_side,
        "type": "market",
        "size": SIZE,
        "reduceOnly": True
    })

    requests.post(BASE_URL + endpoint,
        headers=get_headers("POST", endpoint, body),
        data=body
    )

    send_telegram(f"💰 POSITION CLOSED {SYMBOL}")

# ==============================
# 📈 SIGNAL (simple)
# ==============================

def get_signal():
    return "LONG" if int(time.time()) % 2 == 0 else "SHORT"

# ==============================
# 🔁 MAIN LOOP
# ==============================

send_telegram("🤖 BOT LIVE (AUTO PROFIT)")

current_side = None

while True:
    try:
        pos = get_position()

        if pos:
            pnl = float(pos["unrealisedPnl"])

            if pnl >= TAKE_PROFIT:
                send_telegram(f"🎯 PROFIT: {pnl} USDT")
                close_trade(current_side)
                current_side = None

        else:
            side = get_signal()
            current_side = open_trade(side)

        time.sleep(15)

    except Exception as e:
        send_telegram(f"ERROR: {str(e)}")
        time.sleep(10)
