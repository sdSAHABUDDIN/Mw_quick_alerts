"""
scraper.py — Microworkers Job Monitor (Telegram Edition)

Polls the Microworkers job page every CHECK_INTERVAL seconds.
Sends a Telegram alert for every new job that passes the filters.

Run:
  python scraper.py

Keep alive on a VPS (recommended):
  See README.md → Deployment section for the systemd service file.
"""

import time
import requests
from datetime import datetime

from config import JOBS_URL, CHECK_INTERVAL, MIN_PAY, validate
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
    """
    Validate config, build session, verify it's authenticated.
    Returns session on success, None on failure.
    """
    if not validate():
        return None

    session = create_session()
    log(f"Cookie set: PHPSESSID={session.cookies.get('PHPSESSID', '')[:14]}...", "OK")
    log("Verifying session against live site...")

    try:
        r = session.get(JOBS_URL, timeout=20)
        log(f"Response: status={r.status_code}  size={len(r.text)} chars  encoding={r.encoding}")

        if is_session_expired(r):
            log("Cookie expired — log in to microworkers.com, copy a fresh PHPSESSID into .env", "ERR")
            return None

        jobs = parse_jobs_page(r.text)
        log(f"Job cards found on first load: {len(jobs)}", "OK" if jobs else "WARN")
        return session

    except requests.exceptions.Timeout:
        log("Timed out — check your internet connection.", "ERR")
        return None
    except requests.RequestException as e:
        log(f"Network error: {e}", "ERR")
        return None


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_jobs(session: requests.Session) -> list[dict]:
    """
    Fetch and parse the current job list.
    Returns empty list on any error (loop keeps running).
    """
    try:
        resp = session.get(JOBS_URL, timeout=20)

        if is_session_expired(resp):
            log("Session expired mid-run! Update PHPSESSID in .env and restart.", "ERR")
            return []

        jobs = parse_jobs_page(resp.text)
        log(f"  {len(jobs)} job cards fetched")
        return jobs

    except requests.exceptions.Timeout:
        log("Timeout — will retry next scan.", "WARN")
        return []
    except requests.RequestException as e:
        log(f"Network error: {e}", "ERR")
        return []


# ── Console alert ─────────────────────────────────────────────────────────────

def print_alert(job: dict):
    print()
    log("━" * 56, "ALERT")
    log(f"  🔔  NEW JOB DETECTED!", "ALERT")
    log(f"  Title   : {job['title']}", "ALERT")
    log(f"  Pay     : ${job['pay']:.2f}   TTR: {job['ttr']} min   Success: {job['success']}")
    log(f"  Slots   : {job['done']}/{job['total']}  →  {job['remaining']} remaining")
    log(f"  URL     : {job['url']}")
    log("━" * 56, "ALERT")
    print()


# ── Main loop ─────────────────────────────────────────────────────────────────

def run():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   Microworkers Job Monitor  —  Telegram Edition 🤖  ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Interval : {CHECK_INTERVAL}s                                      ║")
    print(f"║  Min pay  : ${MIN_PAY:.2f}                                    ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    session = setup()
    if not session:
        log("Startup failed — fix the errors above and restart.", "ERR")
        return

    # ── Initial scan: record existing jobs WITHOUT alerting ───────────────────
    # This means even after a restart, you won't get spammed with old jobs.
    seen_ids: set[str] = set()
    log("Initial scan — recording existing jobs (no alerts this round)...")
    for j in fetch_jobs(session):
        seen_ids.add(j["id"])
    log(f"Loaded {len(seen_ids)} existing jobs. Now watching for NEW ones...", "OK")
    print()

    # ── Main polling loop ─────────────────────────────────────────────────────
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
                    print_alert(job)  # console
                    alert(job)        # Telegram
                else:
                    log(f"  Skipped (filtered): '{job['title'][:48]}' — ${job['pay']:.2f}")
        else:
            log(f"  No new jobs. Tracking {len(seen_ids)} total. Next scan in {CHECK_INTERVAL}s...")

        time.sleep(CHECK_INTERVAL)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\nStopped. Goodbye! 👋")
