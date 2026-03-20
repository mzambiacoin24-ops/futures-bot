import os
import time
import requests

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = f"https://api.telegram.org/bot{TOKEN}"

COINS = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT"]

# ===== SETTINGS PER COIN =====
SETTINGS = {
    "BTC-USDT": {"tp": 0.0005, "sl": 0.0005, "step": 15},
    "ETH-USDT": {"tp": 0.0007, "sl": 0.0007, "step": 7},
    "SOL-USDT": {"tp": 0.001, "sl": 0.001, "step": 2},
    "XRP-USDT": {"tp": 0.001, "sl": 0.001, "step": 2},
}

price_data = {c: [] for c in COINS}

positions = []
active_coin = None
direction = None

last_market_id = None

# ===== TELEGRAM =====
def send(msg):
    requests.post(f"{URL}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg
    })

def market_edit(msg):
    global last_market_id
    try:
        if last_market_id is None:
            res = requests.post(f"{URL}/sendMessage", json={
                "chat_id": CHAT_ID,
                "text": msg
            }).json()
            last_market_id = res["result"]["message_id"]
        else:
            requests.post(f"{URL}/editMessageText", json={
                "chat_id": CHAT_ID,
                "message_id": last_market_id,
                "text": msg
            })
    except:
        pass

# ===== PRICE =====
def get_price(symbol):
    try:
        url = "https://api.kucoin.com/api/v1/market/orderbook/level1"
        res = requests.get(url, params={"symbol": symbol}).json()
        return float(res["data"]["price"])
    except:
        return None

# ===== START =====
print("FUTURES BOT RUNNING")

send("Futures Bot Started\nScanning market...")

# ===== MAIN =====
while True:

    # collect prices
    for coin in COINS:
        price = get_price(coin)
        if price:
            price_data[coin].append(price)
            if len(price_data[coin]) > 10:
                price_data[coin].pop(0)

    # ===== MARKET WATCH =====
    watch = "MARKET LIVE\n\n"
    for coin in COINS:
        if price_data[coin]:
            watch += f"{coin}: {round(price_data[coin][-1],2)}\n"

    if active_coin:
        watch += f"\nActive: {active_coin} ({direction})"

    market_edit(watch)

    # ===== SIGNAL DETECTION =====
    if not active_coin:
        for coin in COINS:
            if len(price_data[coin]) < 3:
                continue

            last = price_data[coin][-1]
            prev = price_data[coin][-2]

            # breakout
            if last > prev:
                active_coin = coin
                direction = "LONG"
                send(f"SIGNAL\n{coin}\nDirection: LONG")
                break

            elif last < prev:
                active_coin = coin
                direction = "SHORT"
                send(f"SIGNAL\n{coin}\nDirection: SHORT")
                break

    # ===== ENTRY =====
    if active_coin:
        price = price_data[active_coin][-1]
        cfg = SETTINGS[active_coin]

        if len(positions) < 5:

            if not positions:
                entry = price
            else:
                last_entry = positions[-1]["entry"]

                if direction == "LONG":
                    entry = last_entry - cfg["step"]
                else:
                    entry = last_entry + cfg["step"]

            tp = entry * (1 + cfg["tp"]) if direction == "LONG" else entry * (1 - cfg["tp"])
            sl = entry * (1 - cfg["sl"]) if direction == "LONG" else entry * (1 + cfg["sl"])

            positions.append({"entry": entry, "tp": tp, "sl": sl})

            send(f"ENTRY #{len(positions)}\n{active_coin}\n{direction}\nEntry: {round(entry,2)}\nTP: {round(tp,2)}\nSL: {round(sl,2)}")

    # ===== EXIT =====
    if positions:
        price = price_data[active_coin][-1]

        new_positions = []

        for pos in positions:
            entry = pos["entry"]
            tp = pos["tp"]
            sl = pos["sl"]

            if direction == "LONG":
                if price >= tp:
                    send(f"TP HIT\n{active_coin}\nProfit")
                    continue
                elif price <= sl:
                    send(f"SL HIT\n{active_coin}\nLoss")
                    continue
            else:
                if price <= tp:
                    send(f"TP HIT\n{active_coin}\nProfit")
                    continue
                elif price >= sl:
                    send(f"SL HIT\n{active_coin}\nLoss")
                    continue

            new_positions.append(pos)

        positions = new_positions

        if not positions:
            active_coin = None
            direction = None
            send("Cycle Complete\nScanning again...")

    time.sleep(3)
