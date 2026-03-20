import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
LEVERAGE = 20

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
            params={"symbol": symbol}
        ).json()
        return float(r["data"]["price"])
    except:
        return None

def pick_symbol():
    best = None
    best_move = 0

    for s in SYMBOLS:
        p1 = get_price(s)
        time.sleep(1)
        p2 = get_price(s)

        move = abs(p2 - p1)

        if move > best_move:
            best_move = move
            best = s

    return best

def get_direction(symbol):
    p1 = get_price(symbol)
    time.sleep(2)
    p2 = get_price(symbol)

    return "LONG" if p2 > p1 else "SHORT"

def trade(balance):
    symbol = pick_symbol()
    direction = get_direction(symbol)

    base_margin = balance * 0.3
    entry = get_price(symbol)

    send(f"""🚀 TRADE START

📊 {symbol}
📍 {direction}

💰 Margin: ${round(base_margin,2)}
⚡ x{LEVERAGE}

📥 Entry: {entry}
""")

    hedge_open = False
    hedge_direction = None
    hedge_margin = 0

    for i in range(180):  # ~3 minutes
        price = get_price(symbol)

        # MAIN PNL
        if direction == "LONG":
            pnl_main = (price - entry)/entry * base_margin * LEVERAGE
        else:
            pnl_main = (entry - price)/entry * base_margin * LEVERAGE

        total_pnl = pnl_main

        # 🔁 HEDGE SYSTEM (STRONG)
        if pnl_main < -0.02 and not hedge_open:
            hedge_open = True
            hedge_direction = "SHORT" if direction == "LONG" else "LONG"
            hedge_margin = base_margin * 2   # 🔥 nguvu mara 2

            send(f"""🔁 HEDGE ACTIVATED

Direction → {hedge_direction}
💰 Hedge Margin: ${round(hedge_margin,2)}
""")

        # HEDGE PNL
        if hedge_open:
            if hedge_direction == "LONG":
                pnl_hedge = (price - entry)/entry * hedge_margin * LEVERAGE
            else:
                pnl_hedge = (entry - price)/entry * hedge_margin * LEVERAGE

            total_pnl = pnl_main + pnl_hedge

        # 📊 LIVE STATUS
        if i % 10 == 0:
            send(f"""📊 STATUS

Main: {round(pnl_main,3)}
Total: {round(total_pnl,3)}
""")

        # 🎯 EXIT PROFIT
        if total_pnl > 0.05:
            send(f"""🏁 PROFIT CLOSED

💰 +${round(total_pnl,2)}
""")
            return

        # 🛑 LOSS CONTROL
        if total_pnl < -0.1:
            send(f"""🛑 STOP LOSS

Loss: ${round(total_pnl,2)}
""")
            return

        time.sleep(1)

    send("⏹ EXIT (timeout)")

def get_balance():
    return 4

def main():
    send("🤖 V13 REAL HEDGE BOT ACTIVE 🚀")

    while True:
        try:
            balance = get_balance()

            if balance < 1:
                send("⚠️ Balance ndogo")
                time.sleep(60)
                continue

            trade(balance)

            time.sleep(20)

        except Exception as e:
            send(f"🔥 ERROR: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    main()
