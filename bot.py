import os
import time
import requests

# ========= CONFIG =========
TOKEN = os.getenv("TOKEN")

SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]

TRADE_AMOUNT = 10
LEVERAGE = 5

TP_PERCENT = 0.01   # 1%
SL_PERCENT = 0.005  # 0.5%

CHECK_SPEED = 5

CHAT_ID = None

positions = {}

# ========= TELEGRAM =========
def get_chat_id():
    global CHAT_ID
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        data = requests.get(url).json()
        if data["result"]:
            CHAT_ID = data["result"][-1]["message"]["chat"]["id"]
    except:
        pass

def send(msg):
    if not CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

# ========= PRICE =========
def get_price(symbol):
    try:
        url = "https://api.kucoin.com/api/v1/market/orderbook/level1"
        params = {"symbol": symbol}
        res = requests.get(url, params=params).json()
        return float(res["data"]["price"])
    except:
        return None

# ========= START =========
print("🚀 FUTURES BOT STARTED")

while CHAT_ID is None:
    get_chat_id()
    print("Waiting for /start...")
    time.sleep(2)

send("🚀 FUTURES BOT ACTIVE")

# ========= MAIN LOOP =========
while True:
    for symbol in SYMBOLS:
        price = get_price(symbol)
        if not price:
            continue

        # ===== OPEN TRADE =====
        if symbol not in positions:
            entry = price
            tp = entry * (1 + TP_PERCENT)
            sl = entry * (1 - SL_PERCENT)

            positions[symbol] = {
                "entry": entry,
                "tp": tp,
                "sl": sl
            }

            send(f"""🟢 FUTURES ENTRY

🪙 {symbol}
💰 Capital: ${TRADE_AMOUNT}
⚡ Leverage: x{LEVERAGE}

📊 Entry: {round(entry,2)}
🎯 TP: {round(tp,2)}
🛑 SL: {round(sl,2)}""")

        # ===== CHECK TP/SL =====
        else:
            entry = positions[symbol]["entry"]
            tp = positions[symbol]["tp"]
            sl = positions[symbol]["sl"]

            # TAKE PROFIT
            if price >= tp:
                profit = ((price - entry) / entry) * 100 * LEVERAGE

                send(f"""📤 TP HIT

🪙 {symbol}
📊 Entry: {round(entry,2)}
📊 Exit: {round(price,2)}

💵 Profit: +{round(profit,2)}%""")

                del positions[symbol]

            # STOP LOSS
            elif price <= sl:
                loss = ((price - entry) / entry) * 100 * LEVERAGE

                send(f"""🛑 SL HIT

🪙 {symbol}
📊 Entry: {round(entry,2)}
📊 Exit: {round(price,2)}

💸 Loss: {round(loss,2)}%""")

                del positions[symbol]

    time.sleep(CHECK_SPEED)
