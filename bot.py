import requests
import time
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LEVERAGE = 20
DAILY_TARGET = 2

COINS = [
"BTC-USDT","ETH-USDT","SOL-USDT","AVAX-USDT","LINK-USDT","ADA-USDT","XRP-USDT",
"DOGE-USDT","DOT-USDT","MATIC-USDT","OP-USDT","ARB-USDT","APT-USDT","SUI-USDT",
"SEI-USDT","INJ-USDT","NEAR-USDT","FTM-USDT","ATOM-USDT","FIL-USDT",
"AAVE-USDT","RNDR-USDT","GALA-USDT","SAND-USDT","APE-USDT","LDO-USDT",
"UNI-USDT","CRV-USDT","DYDX-USDT","BLUR-USDT","PEPE-USDT","BONK-USDT",
"SHIB-USDT","FLOKI-USDT","ORDI-USDT","TIA-USDT","JTO-USDT","PYTH-USDT",
"WLD-USDT","ARKM-USDT"
]

total_profit = 0
start_day = datetime.utcnow().day

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

def get_price(symbol):
    try:
        r = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": symbol},
            timeout=3
        ).json()
        return float(r["data"]["price"])
    except:
        return None

# ⚡ FAST TREND CHECK
def quick_analyze(symbol):
    p1 = get_price(symbol)
    time.sleep(0.2)
    p2 = get_price(symbol)
    time.sleep(0.2)
    p3 = get_price(symbol)

    if None in [p1, p2, p3]:
        return None

    move = abs(p3 - p1)

    if move < p1 * 0.0003:
        return None

    if p1 < p2 < p3:
        return "LONG"
    elif p1 > p2 > p3:
        return "SHORT"
    else:
        return None

# ⚡ REAL-TIME PICK
def find_trade():
    for coin in COINS:
        direction = quick_analyze(coin)

        if direction:
            return coin, direction

    return None, None

def trade(balance):
    global total_profit

    symbol, direction = find_trade()

    if symbol is None:
        send("⚡ scanning fast...")
        return

    margin = balance * 0.3
    entry = get_price(symbol)

    if entry is None:
        return

    if direction == "LONG":
        tp = entry * 1.001
    else:
        tp = entry * 0.999

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${round(margin,2)}
⚡ x{LEVERAGE}

📥 Entry: {entry}
🎯 TP: {round(tp,4)}

💵 Total: ${round(total_profit,3)}
""")

    for i in range(90):
        price = get_price(symbol)
        if price is None:
            continue

        if direction == "LONG":
            pnl = (price - entry)/entry * margin * LEVERAGE
            tp_hit = price >= tp
        else:
            pnl = (entry - price)/entry * margin * LEVERAGE
            tp_hit = price <= tp

        if tp_hit:
            total_profit += pnl
            send(f"🏁 TP HIT +${round(pnl,3)} | Total ${round(total_profit,3)}")
            return

        if pnl < -0.1:
            total_profit += pnl
            send(f"🛑 STOP LOSS ${round(pnl,3)} | Total ${round(total_profit,3)}")
            return

        time.sleep(1)

def main():
    global total_profit, start_day

    send("🤖 V18.3 REAL-TIME BOT ACTIVE 🚀")

    while True:
        try:
            today = datetime.utcnow().day

            if today != start_day:
                total_profit = 0
                start_day = today

            if total_profit >= DAILY_TARGET:
                send(f"🛑 TARGET HIT ${round(total_profit,2)}")
                time.sleep(3600)
                continue

            balance = 4

            trade(balance)

            time.sleep(3)  # ⚡ FAST LOOP

        except Exception as e:
            send(f"🔥 ERROR: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    main()
