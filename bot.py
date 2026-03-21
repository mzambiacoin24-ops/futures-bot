import requests, time, json, hmac, hashlib, base64, uuid

# ========= WEKA HAPA =========
API_KEY = "69bd80471b35dd00017afdfb"
API_SECRET = "e6c7a53e-a25c-4edc-b52e-7f28bd4df1d9"
API_PASSPHRASE = "bot1234"

TELEGRAM_TOKEN = "8787267026:AAHjMfzdg9JwVxdCo6pnoiNq2o1xvU2pC30"
CHAT_ID = "7010983039"

BASE_URL = "https://api-futures.kucoin.com"

SYMBOL = "ADAUSDTM"
LEVERAGE = 3
SIZE = "1"

TP_DIFF = 0.0015
SL_DIFF = 0.0012

COOLDOWN = 60
# ============================

def send(msg):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": msg})

def sign(method, endpoint, body=""):
    now = str(int(time.time()*1000))
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

def get_price():
    r = requests.get(BASE_URL+"/api/v1/ticker", params={"symbol": SYMBOL}).json()
    return float(r["data"]["price"])

def has_position():
    r = requests.get(BASE_URL+"/api/v1/positions", headers=sign("GET","/api/v1/positions")).json()
    for p in r.get("data", []):
        if float(p["currentQty"]) != 0:
            return True
    return False

def set_leverage():
    endpoint = "/api/v1/position/leverage"
    body = json.dumps({"symbol": SYMBOL, "leverage": str(LEVERAGE)})
    requests.post(BASE_URL+endpoint, headers=sign("POST",endpoint,body), data=body)

def open_trade(side):
    if has_position():
        return None

    set_leverage()

    entry = get_price()

    if side == "LONG":
        tp = entry + TP_DIFF
        sl = entry - SL_DIFF
    else:
        tp = entry - TP_DIFF
        sl = entry + SL_DIFF

    body = json.dumps({
        "clientOid": str(uuid.uuid4()),
        "symbol": SYMBOL,
        "side": "buy" if side=="LONG" else "sell",
        "type": "market",
        "size": SIZE,
        "marginMode": "CROSS"
    })

    res = requests.post(BASE_URL+"/api/v1/orders",
                        headers=sign("POST","/api/v1/orders",body),
                        data=body).json()

    if res.get("code") == "200000":
        send(f"""🚀 TRADE OPENED

🪙 {SYMBOL}
📍 {side}
📊 Entry: {round(entry,6)}

🎯 TP: {round(tp,6)}
🛑 SL: {round(sl,6)}
""")
        return (side, tp, sl)

    return None

def close_trade(side):
    body = json.dumps({
        "clientOid": str(uuid.uuid4()),
        "symbol": SYMBOL,
        "side": "sell" if side=="LONG" else "buy",
        "type": "market",
        "size": SIZE,
        "reduceOnly": True
    })

    requests.post(BASE_URL+"/api/v1/orders",
                  headers=sign("POST","/api/v1/orders",body),
                  data=body)

def signal():
    return "LONG" if int(time.time()) % 2 == 0 else "SHORT"

send("🤖 BOT LIVE (SMART MODE)")

trade = None

while True:
    try:
        if has_position() and trade:
            price = get_price()
            side, tp, sl = trade

            if (side=="LONG" and (price>=tp or price<=sl)) or \
               (side=="SHORT" and (price<=tp or price>=sl)):

                close_trade(side)

                send("💰 TRADE CLOSED")

                trade = None
                time.sleep(COOLDOWN)

        elif not has_position() and not trade:
            trade = open_trade(signal())

        time.sleep(10)

    except Exception as e:
        send(f"ERROR: {e}")
        time.sleep(5)
