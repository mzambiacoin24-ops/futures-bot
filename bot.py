import requests
import time
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
LEVERAGE = 20

DAILY_TARGET = 2  # unaweza badilisha baadaye

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

        price = r.get("data", {}).get("price", None)
        if price is None:
            return None

        return float(price)

    except:
        return None

def analyze_market(symbol):
    prices = []

    for _ in range(5):
        p = get_price(symbol)
        if p is None:
            return None, None
        prices.append(p)
        time.sleep(1)

    move = max(prices) - min(prices)

    if move < 0.05:
        return None, None

    if prices[-1] > prices[0]:
        return "LONG", move
    else:
        return "SHORT", move

def pick_symbol():
    best_symbol = None
    best_move = 0
    best_direction = None

    for s in SYMBOLS:
        direction, move = analyze_market(s)

        if direction is None:
            continue

        if move > best_move:
            best_move = move
            best_symbol = s
            best_direction = direction

    return best_symbol, best_direction

def trade(balance):
    global total_profit

    symbol, direction = pick_symbol()

    if symbol is None:
        send("⏳ No strong market, waiting...")
        time.sleep(10)
        return

    base_margin = balance * 0.3
    position_size = base_margin * LEVERAGE
    entry = get_price(symbol)

    if entry is None:
        return

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${round(base_margin,2)}
⚡ Leverage: x{LEVERAGE}
📦 Position: ${round(position_size,2)}

📥 Entry: {entry}
""")

    hedge_open = False
    hedge_direction = None
    hedge_margin = 0
    peak_profit = 0

    for i in range(180):
        price = get_price(symbol)

        if price is None:
            continue

        if direction == "LONG":
            pnl_main = (price - entry)/entry * base_margin * LEVERAGE
        else:
            pnl_main = (entry - price)/entry * base_margin * LEVERAGE

        total_pnl = pnl_main

        if pnl_main < -0.02 and not hedge_open:
            hedge_open = True
            hedge_direction = "SHORT" if direction == "LONG" else "LONG"
            hedge_margin = base_margin * 2

            send(f"""🔁 HEDGE ACTIVATED

Direction → {hedge_direction}
💰 Hedge Margin: ${round(hedge_margin,2)}
""")

        if hedge_open:
            if hedge_direction == "LONG":
                pnl_hedge = (price - entry)/entry * hedge_margin * LEVERAGE
            else:
                pnl_hedge = (entry - price)/entry * hedge_margin * LEVERAGE

            total_pnl = pnl_main + pnl_hedge

        if i % 10 == 0:
            send(f"""📊 STATUS

Main: {round(pnl_main,3)}
Total: {round(total_pnl,3)}
💰 Session Profit: ${round(total_profit,3)}
""")

        if total_pnl > peak_profit:
            peak_profit = total_pnl

        # QUICK PROFIT
        if total_pnl > 0.02:
            total_profit += total_pnl
            send(f"""🏁 PROFIT LOCKED

💰 Trade: +${round(total_pnl,3)}
📊 Total: ${round(total_profit,3)}
""")
            return

        # TRAILING
        if peak_profit > 0.02 and total_pnl < peak_profit * 0.6:
            total_profit += total_pnl
            send(f"""🔒 TRAILING EXIT

💰 Trade: +${round(total_pnl,3)}
📊 Total: ${round(total_profit,3)}
""")
            return

        # STOP LOSS
        if total_pnl < -0.1:
            total_profit += total_pnl
            send(f"""🛑 STOP LOSS

Loss: ${round(total_pnl,2)}
📊 Total: ${round(total_profit,3)}
""")
            return

        time.sleep(1)

    send("⏹ EXIT (timeout)")

def main():
    global total_profit, start_day

    send("🤖 V16 ELITE BOT ACTIVE 🚀")

    while True:
        try:
            today = datetime.utcnow().day

            if today != start_day:
                total_profit = 0
                start_day = today

            if total_profit >= DAILY_TARGET:
                send(f"""🛑 DAILY TARGET REACHED

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

            time.sleep(20)

        except Exception as e:
            send(f"🔥 ERROR: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    main()
