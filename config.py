"""
config.py — Central config for Microworkers Alerts (Telegram Edition)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Microworkers session ──────────────────────────────────────────────────────
MW_PHPSESSID   = os.getenv("MW_PHPSESSID", "")
BASE_URL       = "https://www.microworkers.com"
JOBS_URL       = f"{BASE_URL}/jobs.php"
CHECK_INTERVAL = 15    # seconds between scans
MIN_PAY        = 0.10  # USD — jobs below this are skipped

# ── HTTP headers (proven working — do NOT add Accept-Encoding) ────────────────
HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         BASE_URL,
}

# ── Telegram ──────────────────────────────────────────────────────────────────
# Get BOT_TOKEN from @BotFather on Telegram
# Get CHAT_ID from @userinfobot (your personal chat) or your channel's ID
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ── Startup validation ────────────────────────────────────────────────────────
def validate() -> bool:
    errors = []
    if not MW_PHPSESSID:
        errors.append("MW_PHPSESSID is empty — copy from browser cookies")
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is empty — get it from @BotFather")
    if not TELEGRAM_CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID is empty — get it from @userinfobot")

    for e in errors:
        print(f"[config] ✗  {e}")
    return len(errors) == 0
