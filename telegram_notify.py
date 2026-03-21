import json
import requests
import os

BASE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(BASE, "config", "telegram.json")

def send_telegram(msg):
    try:
        with open(CFG, "r", encoding="utf-8") as f:
            conf = json.load(f)
        token = conf["token"]
        chat = conf["chat_id"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat, "text": msg})
    except:
        pass
