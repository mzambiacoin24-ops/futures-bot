import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = None

def send_message(text):
    requests.post(f"{URL}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": text
    })

def get_updates():
    global last_update_id
    params = {"timeout": 100}
    if last_update_id:
        params["offset"] = last_update_id + 1

    res = requests.get(f"{URL}/getUpdates", params=params).json()
    return res

def handle_updates(updates):
    global last_update_id

    for update in updates["result"]:
        last_update_id = update["update_id"]

        if "message" in update:
            text = update["message"].get("text")

            if text == "/start":
                send_message("🤖 Futures Bot Active!\nReady to trade 🚀")

while True:
    updates = get_updates()
    if "result" in updates:
        handle_updates(updates)

    time.sleep(2)
