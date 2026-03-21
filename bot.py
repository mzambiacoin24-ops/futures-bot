import requests, time, json, hmac, hashlib, base64, uuid

# ===== WEKA KEYS =====
API_KEY = "69bd80471b35dd00017afdfb"
API_SECRET = "
e6c7a53e-a25c-4edc-b52e-7f28bd4df1d9"
API_PASSPHRASE = "bot1234"

TELEGRAM_TOKEN = "8787267026:AAHjMfzdg9JwVxdCo6pnoiNq2o1xvU2pC30"
CHAT_ID = "7010983039"

BASE_URL = "https://api-futures.kucoin.com"

LEVERAGE = 5
SIZE = "1"
SYMBOLS = ["ADAUSDTM"]
TAKE_PROFIT = 0.2   # profit ndogo ya haraka

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
def get_position(symbol):
    endpoint = "/api/v1/positions"
    res = requests.get(BASE_URL + endpoint, headers=get_headers("GET", endpoint, ""))
    data = res.json()

    if "data" in data:
        for pos in data["data"]:
            if pos["symbol"] == symbol and float(pos["currentQty"]) != 0:
                return pos
    return None

# ===== SET LEVERAGE =====
def set_leverage(symbol):
    endpoint = "/api/v1/position/leverage"
    body = json.dumps({
        "symbol": symbol,
        "leverage": str(LEVERAGE)
    })
    requests.post(BASE_URL + endpoint, headers=get_headers("POST", endpoint, body), data=body)

# ===== OPEN TRADE =====
def open_trade(symbol, side):
    if get_position(symbol):
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

    if data.get("code") == "200000":
        send_telegram(f"🚀 TRADE OPENED {symbol} {side}")
    else:
        send_telegram(f"❌ {data}")

# ===== CLOSE TRADE =====
def close_trade(symbol, side):
    endpoint = "/api/v1/orders"

    close_side = "sell" if side == "LONG" else "buy"

    body = json.dumps({
        "clientOid": str(uuid.uuid4()),
        "symbol": symbol,
        "side": close_side,
        "type": "market",
        "size": SIZE,
        "reduceOnly": True
    })

    requests.post(BASE_URL + endpoint,
        headers=get_headers("POST", endpoint, body),
        data=body
    )

    send_telegram(f"💰 POSITION CLOSED {symbol}")

# ===== SIGNAL =====
def get_signal():
    return "LONG" if int(time.time()) % 2 == 0 else "SHORT"

# ===== MAIN =====
send_telegram("🤖 BOT LIVE (AUTO PROFIT ON)")

current_side = None

while True:
    try:
        for symbol in SYMBOLS:
            pos = get_position(symbol)

            if pos:
                pnl = float(pos["unrealisedPnl"])

                if pnl >= TAKE_PROFIT:
                    send_telegram(f"🎯 PROFIT: {pnl} USDT")
                    close_trade(symbol, current_side)
                    current_side = None

            else:
                side = get_signal()
                open_trade(symbol, side)
                current_side = side

        time.sleep(15)

    except Exception as e:
        send_telegram(f"ERROR: {str(e)}")
        time.sleep(10)
