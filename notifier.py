"""
notifier.py — Alert dispatcher: Telegram Bot API only

Sends a formatted message with an inline "Open Job" button for every new job.
No database, no Firebase, no FCM. Just Telegram.
"""

import logging
import requests as http

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from detect_category import detect_category

logger = logging.getLogger(__name__)

_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Category emoji map for nicer messages
_CAT_EMOJI = {
    "Email":          "📧",
    "YouTube":        "▶️",
    "Social Media":   "📱",
    "Search & Visit": "🔍",
    "Data Collection":"📊",
    "App Install":    "📲",
    "CPA Offers":     "💼",
    "Other":          "🗂️",
}


def send_telegram(job: dict) -> bool:
    """
    Send a single job alert to the configured Telegram chat.
    Returns True on success, False on failure.
    """
    cat   = detect_category(job["title"])
    emoji = _CAT_EMOJI.get(cat, "🗂️")

    text = (
        f"🔔 <b>New Job Alert!</b>\n\n"
        f"📌 <b>{job['title']}</b>\n\n"
        f"💰 Pay: <b>${job['pay']:.2f}</b>\n"
        f"{emoji} Category: {cat}\n"
        f"🎰 Slots left: <b>{job.get('remaining', '?')}</b> / {job.get('total', '?')}\n"
        f"⏱️ Time-to-rate: {job.get('ttr', '?')} min\n"
        f"✅ Success rate: {job.get('success', '?')}"
    )

    payload = {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "▶️  Open Job on Microworkers", "url": job["url"]}
            ]]
        },
    }

    try:
        r = http.post(f"{_API}/sendMessage", json=payload, timeout=10)
        if r.ok:
            return True
        logger.warning(f"[telegram] send failed: {r.status_code} — {r.text[:120]}")
        return False
    except Exception as e:
        logger.error(f"[telegram] exception: {e}")
        return False


def alert(job: dict):
    """
    Main entry point called by scraper.py for every new matching job.
    """
    cat = detect_category(job["title"])
    ok  = send_telegram(job)
    status = "✓" if ok else "✗ FAILED"
    print(f"[alert] {status} '{job['title'][:50]}' [{cat}] → Telegram")
