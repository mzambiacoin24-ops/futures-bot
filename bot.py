import requests, time, json, hmac, hashlib, base64, uuid

# ===== WEKA HAPA KEYS ZAKO =====
API_KEY = "69bd80471b35dd00017afdfb"
API_SECRET = "e6c7a53e-a25c-4edc-b52e-7f28bd4df1d9"
API_PASSPHRASE = "bot1234"

TELEGRAM_TOKEN = "8787267026:AAHjMfzdg9JwVxdCo6pnoiNq2o1xvU2pC30"
CHAT_ID = "7010983039"

BASE_URL = "https://api-futures.kucoin.com"

LEVERAGE = 5
SIZE = "1"
SYMBOLS = ["ADAUSDTM"]

# ===== TELEGRAM =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ===== SIGN =====
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

# ===== CHECK POSITION =====
def has_open_position(symbol):
    endpoint = "/api/v1/positions"
    res = requests.get(BASE_URL + endpoint, headers=get_headers("GET", endpoint, ""))
    data = res.json()

    if "data" in data:
        for pos in data["data"]:
            if pos["symbol"] == symbol and float(pos["currentQty"]) != 0:
                return True
    return False

# ===== SET LEVERAGE =====
def set_leverage(symbol):
    endpoint = "/api/v1/position/leverage"
    body = json.dumps({
        "symbol": symbol,
        "leverage": str(LEVERAGE)
    })
    requests.post(BASE_URL + endpoint, headers=get_headers("POST", endpoint, body), data=body)

# ===== PLACE TRADE =====
def place_trade(symbol, side):
    if has_open_position(symbol):
        send_telegram("⏳ Ninasubiri position ifungwe...")
        return

    set_leverage(symbol)

    endpoint = "/api/v1/orders"
    body = json.dumps({
        "clientOid": str(uuid.uuid4()),
        "symbol": symbol,
        "side": "buy" if side == "LONG" else "sell",
        "type": "market",
        "size": SIZE,
        "marginMode": "CROSS"
    })

    res = requests.post(BASE_URL + endpoint, headers=get_headers("POST", endpoint, body), data=body)
    data = res.json()

    if "code" in data and data["code"] == "200000":
        send_telegram(f"🚀 TRADE OPENED {symbol} {side}")
    else:
        send_telegram(f"❌ {data}")

# ===== SIMPLE STRATEGY =====
def get_signal():
    return "LONG" if int(time.time()) % 2 == 0 else "SHORT"

# ===== MAIN LOOP =====
send_telegram("🤖 BOT LIVE (1 TRADE MODE)")

while True:
    try:
        for symbol in SYMBOLS:
            side = get_signal()
            place_trade(symbol, side)
        time.sleep(30)
    except Exception as e:
        send_telegram(f"ERROR: {str(e)}")
        time.sleep(10)
