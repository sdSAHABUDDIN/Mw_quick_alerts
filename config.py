"""
config.py — Central config for Microworkers Alerts (Telegram Edition)
"""

import os
import random
from dotenv import load_dotenv

load_dotenv()

# ── Microworkers session ──────────────────────────────────────────────────────
MW_PHPSESSID   = os.getenv("MW_PHPSESSID", "")
BASE_URL       = "https://www.microworkers.com"
JOBS_URL       = f"{BASE_URL}/jobs.php"

# Baseline interval. We will add heavy randomization to this in scraper.py
CHECK_INTERVAL = 30   # Raised from 15s to 45s for account safety
MIN_PAY        = 0.05  # USD — jobs below this are skipped

# ── Rotated User-Agents ───────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
]

def get_headers() -> dict:
    """Generates dynamic headers with a randomized User-Agent to avoid fingerprinting."""
    return {
        "User-Agent":      random.choice(USER_AGENTS),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer":         BASE_URL,
        "Connection":      "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

# ── Telegram ──────────────────────────────────────────────────────────────────
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