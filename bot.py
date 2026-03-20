import requests
import time
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
LEVERAGE = 20
DAILY_TARGET = 2

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

# 🔥 SMART TREND CHECK (PRO)
def get_trend(symbol):
    prices = []

    for _ in range(6):
        p = get_price(symbol)
        if p is None:
            return None
        prices.append(p)
        time.sleep(1)

    up = all(prices[i] < prices[i+1] for i in range(len(prices)-1))
    down = all(prices[i] > prices[i+1] for i in range(len(prices)-1))

    move = abs(prices[-1] - prices[0])

    if move < 0.5:  # filter noise
        return None

    if up:
        return "LONG"
    elif down:
        return "SHORT"
    else:
        return None

def pick_trade():
    for s in SYMBOLS:
        trend = get_trend(s)
        if trend:
            return s, trend
    return None, None

def trade(balance):
    global total_profit

    symbol, direction = pick_trade()

    if symbol is None:
        send("⏳ No clean trend, waiting...")
        time.sleep(15)
        return

    margin = balance * 0.3
    entry = get_price(symbol)

    if entry is None:
        return

    # 🎯 REAL TP CALCULATION
    if direction == "LONG":
        tp = entry * 1.0007
    else:
        tp = entry * 0.9993

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${round(margin,2)}
⚡ Leverage: x{LEVERAGE}

📥 Entry: {entry}
🎯 TP: {round(tp,2)}

💵 Session Profit: ${round(total_profit,3)}
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

        # 🔁 HEDGE SYSTEM
        if pnl < -0.03 and not hedge_open:
            hedge_open = True
            hedge_dir = "SHORT" if direction == "LONG" else "LONG"
            hedge_margin = margin * 2

            send(f"""🔁 HEDGE ON

Direction: {hedge_dir}
💰 Hedge: ${round(hedge_margin,2)}
""")

        if hedge_open:
            if hedge_dir == "LONG":
                hedge_pnl = (price - entry)/entry * hedge_margin * LEVERAGE
            else:
                hedge_pnl = (entry - price)/entry * hedge_margin * LEVERAGE

            total_pnl = pnl + hedge_pnl

        if i % 10 == 0:
            send(f"""📊 STATUS

Price: {price}
PNL: {round(total_pnl,3)}
💵 Total Profit: ${round(total_profit,3)}
""")

        # 🎯 TP HIT
        if tp_hit:
            total_profit += total_pnl
            send(f"""🏁 TP HIT

💰 Profit: +${round(total_pnl,3)}
📊 Total: ${round(total_profit,3)}
""")
            return

        # 🛑 STOP LOSS
        if total_pnl < -0.15:
            total_profit += total_pnl
            send(f"""🛑 STOP LOSS

Loss: ${round(total_pnl,3)}
📊 Total: ${round(total_profit,3)}
""")
            return

        time.sleep(1)

    send("⏹ EXIT (timeout)")

def main():
    global total_profit, start_day

    send("🤖 V17 PRO BOT ACTIVE 🚀")

    while True:
        try:
            today = datetime.utcnow().day

            if today != start_day:
                total_profit = 0
                start_day = today

            if total_profit >= DAILY_TARGET:
                send(f"""🛑 TARGET HIT

💰 Total: ${round(total_profit,2)}
Bot paused
""")
                time.sleep(3600)
                continue

            balance = 4

            if balance < 1:
                time.sleep(60)
                continue

            trade(balance)

            time.sleep(15)

        except Exception as e:
            send(f"🔥 ERROR: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    main()
