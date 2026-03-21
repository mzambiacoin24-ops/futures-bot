import requests
import time
import hmac
import hashlib
import base64
import json
import uuid

# ====== SETTINGS ======
API_KEY = "69bd80471b35dd00017afdfb"
API_SECRET = "e6c7a53e-a25c-4edc-b52e-7f28bd4df1d9"
API_PASSPHRASE = "bot1234"

TELEGRAM_TOKEN = "8787267026:AAHjMfzdg9JwVxdCo6pnoiNq2o1xvU2pC30"
CHAT_ID = "7010983039"

BASE_URL = "https://api-futures.kucoin.com"

SYMBOL = "ADAUSDTM"
LEVERAGE = 3
SIZE = 10

TP_PERCENT = 0.5 / 100
SL_PERCENT = 0.5 / 100

# ====== GLOBAL STATE ======
has_position_long = False
has_position_short = False
total_profit = 0

# ====== TELEGRAM ======
def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
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

    headers = {
        "KC-API-KEY": API_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": now,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }
    return headers

# ====== PRICE ======
def get_price():
    r = requests.get(BASE_URL + f"/api/v1/ticker?symbol={SYMBOL}")
    return float(r.json()['data']['price'])

# ====== SET LEVERAGE ======
def set_leverage():
    endpoint = "/api/v1/position/leverage"
    body = json.dumps({
        "symbol": SYMBOL,
        "leverage": str(LEVERAGE)
    })
    requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body), data=body)

# ====== PLACE TRADE ======
def open_trade(side):
    global has_position_long, has_position_short

    if side == "LONG" and has_position_long:
        return
    if side == "SHORT" and has_position_short:
        return

    set_leverage()

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

    price = get_price()

    tp = price * (1 + TP_PERCENT) if side == "LONG" else price * (1 - TP_PERCENT)
    sl = price * (1 - SL_PERCENT) if side == "LONG" else price * (1 + SL_PERCENT)

    set_tp_sl(side, tp, sl)

    msg = f"""🚀 TRADE OPENED

📍 {SYMBOL}
📉 {side}

💰 Entry: {price:.5f}
🎯 TP: {tp:.5f}
🛑 SL: {sl:.5f}
"""
    send(msg)

    if side == "LONG":
        has_position_long = True
    else:
        has_position_short = True

# ====== TP/SL REAL ======
def set_tp_sl(side, tp, sl):
    endpoint = "/api/v1/st-orders"

    # TP
    body_tp = json.dumps({
        "symbol": SYMBOL,
        "side": "sell" if side == "LONG" else "buy",
        "stop": "up",
        "stopPrice": str(tp),
        "type": "market",
        "size": SIZE,
        "positionSide": side
    })
    requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body_tp), data=body_tp)

    # SL
    body_sl = json.dumps({
        "symbol": SYMBOL,
        "side": "sell" if side == "LONG" else "buy",
        "stop": "down",
        "stopPrice": str(sl),
        "type": "market",
        "size": SIZE,
        "positionSide": side
    })
    requests.post(BASE_URL + endpoint, headers=sign("POST", endpoint, body_sl), data=body_sl)

# ====== CHECK CLOSE ======
def check_close():
    global has_position_long, has_position_short, total_profit

    endpoint = f"/api/v1/positions?symbol={SYMBOL}"
    r = requests.get(BASE_URL + endpoint, headers=sign("GET", endpoint))
    data = r.json()['data']

    if not data:
        return

    for pos in data:
        if float(pos['currentQty']) == 0:
            pnl = float(pos['realisedPnl'])
            total_profit += pnl

            send(f"""✅ POSITION CLOSED

💰 Profit: {pnl:.4f} USDT
📊 Total: {total_profit:.4f} USDT
""")

            if pos['positionSide'] == "LONG":
                has_position_long = False
            else:
                has_position_short = False

# ====== SIMPLE SIGNAL ======
def signal():
    # mfano rahisi (unaweza kubaki na strategy yako)
    price = get_price()
    return "LONG" if int(time.time()) % 2 == 0 else "SHORT"

# ====== MAIN LOOP ======
send("🤖 BOT LIVE (SMART + HEDGE + TP/SL)")

while True:
    try:
        check_close()

        s = signal()

        open_trade(s)

        time.sleep(10)

    except Exception as e:
        send(f"❌ ERROR: {str(e)}")
        time.sleep(10)
