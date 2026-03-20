import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = f"https://api.telegram.org/bot{TOKEN}"

SYMBOL = "BTC-USDT"

MARGIN_BASE = 10
LEVERAGE = 10

COOLDOWN = 5

last_price = None
last_trade_time = 0

# ===== TELEGRAM =====
def send(msg):
    requests.post(f"{URL}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": msg
    })

# ===== PRICE =====
def get_price():
    try:
        res = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": SYMBOL}
        ).json()
        return float(res["data"]["price"])
    except:
        return None

# ===== MAIN =====
def run():
    global last_price, last_trade_time

    send("🤖 Hedged Scalping Bot Active")

    while True:
        price = get_price()
        if price is None:
            continue

        if last_price is None:
            last_price = price
            continue

        # ===== SIGNAL =====
        if time.time() - last_trade_time > COOLDOWN:

            if price > last_price:
                direction = "LONG"
            else:
                direction = "SHORT"

            # ===== TRADE 1 =====
            margin = MARGIN_BASE
            position = margin * LEVERAGE
            entry = price

            send(f"""🚀 TRADE START

📊 {SYMBOL}
📍 Direction: {direction}

💰 Margin: ${margin}
⚡ Leverage: x{LEVERAGE}
📦 Position: ${position}

📥 Entry: {round(entry,2)}
""")

            # ===== TRACK =====
            step = 0
            while step < 3:

                current = get_price()

                # ===== LONG =====
                if direction == "LONG":

                    tp = entry * 1.0006
                    sl = entry * 0.9994

                    if current >= tp:
                        profit = (tp - entry)/entry * position
                        send(f"🎯 TP HIT +${round(profit,2)}")
                        break

                    if current <= sl:
                        step += 1
                        direction = "SHORT"
                        margin += 5
                        position = margin * LEVERAGE
                        entry = current

                        send(f"""🔁 HEDGE

➡️ SWITCH TO SHORT
💰 Margin: ${margin}
📥 Entry: {round(entry,2)}
""")

                # ===== SHORT =====
                else:

                    tp = entry * 0.9994
                    sl = entry * 1.0006

                    if current <= tp:
                        profit = (entry - tp)/entry * position
                        send(f"🎯 TP HIT +${round(profit,2)}")
                        break

                    if current >= sl:
                        step += 1
                        direction = "LONG"
                        margin += 5
                        position = margin * LEVERAGE
                        entry = current

                        send(f"""🔁 HEDGE

➡️ SWITCH TO LONG
💰 Margin: ${margin}
📥 Entry: {round(entry,2)}
""")

                time.sleep(1)

            last_trade_time = time.time()

        last_price = price
        time.sleep(1)

# RUN
if __name__ == "__main__":
    run()
