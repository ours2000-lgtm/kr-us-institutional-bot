"""
Telegram notification utility
KR_US_INSTITUTIONAL_BOT
"""

from __future__ import annotations

import requests


# ---------------------------------------------------------
# Telegram 설정
# ---------------------------------------------------------

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"


# ---------------------------------------------------------
# Telegram 메시지 전송
# ---------------------------------------------------------

def send_telegram_message(message: str) -> None:
    """
    Send message to Telegram
    """

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        # Alert 실패는 Runtime을 깨면 안됨
        pass