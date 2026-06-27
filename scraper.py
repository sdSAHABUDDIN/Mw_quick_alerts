"""
scraper.py — Microworkers Job Monitor (Anti-Detection Edition)
"""

import time
import random
import requests
from datetime import datetime

from config import JOBS_URL, CHECK_INTERVAL, MIN_PAY, validate, get_headers
from auth import create_session, is_session_expired
from parser import parse_jobs_page, matches_filters
from notifier import alert


# ── Logger ────────────────────────────────────────────────────────────────────

def log(msg: str, level: str = "INFO"):
    now   = datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "·", "OK": "✓", "ALERT": "🔔", "WARN": "⚠", "ERR": "✗"}
    print(f"[{now}] {icons.get(level, '·')} {msg}")


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup() -> requests.Session | None:
    if not validate():
        return None

    session = create_session()
    log(f"Cookie set: PHPSESSID={session.cookies.get('PHPSESSID', '')[:14]}...", "OK")
    log("Verifying session against live site...")

    try:
        # Dynamically fetch updated headers
        r = session.get(JOBS_URL, headers=get_headers(), timeout=20)
        log(f"Response: status={r.status_code}  size={len(r.text)} chars")

        if r.status_code == 429:
            log("Rate limited immediately on setup! Backing off for 5 mins.", "ERR")
            return None

        if is_session_expired(r):
            log("Cookie expired — log in to microworkers.com, copy a fresh PHPSESSID into .env", "ERR")
            return None

        jobs = parse_jobs_page(r.text)
        log(f"Job cards found on first load: {len(jobs)}", "OK" if jobs else "WARN")
        return session

    except requests.exceptions.Timeout:
        log("Timed out during setup — check internet connection.", "ERR")
        return None
    except requests.RequestException as e:
        log(f"Network error during setup: {e}", "ERR")
        return None


# ── Fetch with Anti-Detection & Backoff ────────────────────────────────────────

def fetch_jobs(session: requests.Session) -> list[dict]:
    """
    Fetch and parse job list with exponential backoff and rate-limiting safety.
    """
    base_retry_delay = 30
    
    for attempt in range(3):
        try:
            # Injecting freshly randomized headers for every network call
            resp = session.get(JOBS_URL, headers=get_headers(), timeout=20)

            # Handle Anti-Scraping Rate Limits Safely
            if resp.status_code == 429:
                log("Rate limited (HTTP 429)! Cooling down script for 5 minutes...", "WARN")
                time.sleep(300)
                return []

            if is_session_expired(resp):
                log("Session expired mid-run! Update PHPSESSID in .env and restart.", "ERR")
                return []

            jobs = parse_jobs_page(resp.text)
            log(f"  {len(jobs)} job cards fetched")
            return jobs

        except requests.exceptions.Timeout:
            delay = base_retry_delay * (2 ** attempt)
            log(f"Timeout on attempt {attempt + 1}. Retrying in {delay}s...", "WARN")
            time.sleep(delay)
        except requests.RequestException as e:
            delay = base_retry_delay * (2 ** attempt)
            log(f"Network error ({e}) on attempt {attempt + 1}. Retrying in {delay}s...", "ERR")
            time.sleep(delay)
            
    return []


# ── Console alert ─────────────────────────────────────────────────────────────

def print_alert(job: dict):

    print()

    log("━" * 56, "ALERT")

    log("  🔔  NEW JOB DETECTED!", "ALERT")

    log(f"  Title   : {job['title']}", "ALERT")

    log(f"  Pay     : ${job['pay']:.2f}   TTR: {job['ttr']} min SUCCESS: {job['success']} min")

    log(f"  Slots   : {job['done']}/{job['total']}  →  {job['remaining']} remaining")

    log(f"  URL     : {job['url']}")

    log("━" * 56, "ALERT")

    print() 


# ── Main loop ─────────────────────────────────────────────────────────────────

def run():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   Microworkers Job Monitor  — Stealth Edition 🛡️    ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Base Interval : {CHECK_INTERVAL}s (With Jitter Enabled)          ║")
    print(f"║  Min pay       : ${MIN_PAY:.2f}                                    ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    session = setup()
    if not session:
        log("Startup failed — fix the errors above and restart.", "ERR")
        return

    seen_ids: set[str] = set()
    log("Initial scan — recording existing jobs (no alerts this round)...")
    for j in fetch_jobs(session):
        seen_ids.add(j["id"])
    log(f"Loaded {len(seen_ids)} existing jobs. Now watching for NEW ones...", "OK")
    print()

    scan = 0
    while True:
        scan += 1
        log(f"Scan #{scan} — {datetime.now().strftime('%H:%M:%S')}")

        current_jobs = fetch_jobs(session)
        new_jobs     = [j for j in current_jobs if j["id"] not in seen_ids]

        if new_jobs:
            for job in new_jobs:
                seen_ids.add(job["id"])
                if matches_filters(job):
                    print_alert(job)
                    alert(job)
                else:
                    log(f"  Skipped (filtered): '{job['title'][:48]}' — ${job['pay']:.2f}")
        else:
            # Humanize timing patterns by introducing random variance (jitter)
            jitter = random.uniform(0.8, 1.3)
            actual_sleep = CHECK_INTERVAL * jitter
            log(f"  No new jobs. Next scan in {actual_sleep:.1f}s (Jitter factor: {jitter:.2f}x)...")
            time.sleep(actual_sleep)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\nStopped cleanly. Goodbye! 👋")