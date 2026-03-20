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
            timeout=5
        ).json()
        return float(r["data"]["price"])
    except:
        return None

# 🔥 IMPROVED ANALYSIS (BALANCED)
def analyze(symbol):
    prices = []

    for _ in range(5):
        p = get_price(symbol)
        if p is None:
            return None, None
        prices.append(p)
        time.sleep(0.3)  # faster scan

    move = abs(prices[-1] - prices[0])

    up = all(prices[i] < prices[i+1] for i in range(len(prices)-1))
    down = all(prices[i] > prices[i+1] for i in range(len(prices)-1))

    # 🔥 less strict filter
    if move < prices[0] * 0.0004:
        return None, None

    if up:
        return "LONG", move
    elif down:
        return "SHORT", move
    else:
        return None, None

def pick_best():
    best_symbol = None
    best_move = 0
    best_direction = None

    for coin in COINS:
        direction, move = analyze(coin)

        if direction is None:
            continue

        if move > best_move:
            best_move = move
            best_symbol = coin
            best_direction = direction

    return best_symbol, best_direction

def trade(balance):
    global total_profit

    symbol, direction = pick_best()

    if symbol is None:
        send("⏳ Scanning market...")
        time.sleep(5)
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
🔥 Best Opportunity

📍 {direction}

💰 Margin: ${round(margin,2)}
⚡ x{LEVERAGE}

📥 Entry: {entry}
🎯 TP: {round(tp,4)}

💵 Total Profit: ${round(total_profit,3)}
""")

    hedge_open = False
    hedge_dir = None
    hedge_margin = 0

    for i in range(120):
        price = get_price(symbol)
        if price is None:
            continue

        if direction == "LONG":
            pnl = (price - entry)/entry * margin * LEVERAGE
            tp_hit = price >= tp
        else:
            pnl = (entry - price)/entry * margin * LEVERAGE
            tp_hit = price <= tp

        total_pnl = pnl

        if pnl < -0.03 and not hedge_open:
            hedge_open = True
            hedge_dir = "SHORT" if direction == "LONG" else "LONG"
            hedge_margin = margin * 2

            send(f"""🔁 HEDGE ON

Direction: {hedge_dir}
💰 ${round(hedge_margin,2)}
""")

        if hedge_open:
            if hedge_dir == "LONG":
                hedge_pnl = (price - entry)/entry * hedge_margin * LEVERAGE
            else:
                hedge_pnl = (entry - price)/entry * hedge_margin * LEVERAGE

            total_pnl = pnl + hedge_pnl

        if i % 10 == 0:
            send(f"""📊 STATUS

{symbol}
PNL: {round(total_pnl,3)}
💰 Total: ${round(total_profit,3)}
""")

        if tp_hit:
            total_profit += total_pnl
            send(f"""🏁 TP HIT

💰 +${round(total_pnl,3)}
📊 Total: ${round(total_profit,3)}
""")
            return

        if total_pnl < -0.15:
            total_profit += total_pnl
            send(f"""🛑 STOP LOSS

Loss: ${round(total_pnl,3)}
📊 Total: ${round(total_profit,3)}
""")
            return

        time.sleep(1)

    send("⏹ EXIT")

def main():
    global total_profit, start_day

    send("🤖 V18.1 AUTO SCANNER ACTIVE 🚀")

    while True:
        try:
            today = datetime.utcnow().day

            if today != start_day:
                total_profit = 0
                start_day = today

            if total_profit >= DAILY_TARGET:
                send(f"""🛑 TARGET HIT

💰 ${round(total_profit,2)}
""")
                time.sleep(3600)
                continue

            balance = 4

            trade(balance)

            time.sleep(10)

        except Exception as e:
            send(f"🔥 ERROR: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    main()
