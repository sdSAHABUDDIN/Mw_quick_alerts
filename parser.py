"""
parser.py — Microworkers job list HTML parser with Email-only filtering
Selectors verified against live site: .jobslist, .jobname, .jobpayment, .jobdone, .jobttr, .jobsuccess
"""

import re
import hashlib
from bs4 import BeautifulSoup
from config import BASE_URL, MIN_PAY
from detect_category import detect_category  # Imported to handle strict routing


# ── Amount extractor ──────────────────────────────────────────────────────────

def extract_amount(text: str) -> float:
    """
    Parse pay amount from strings like '$0.15', '15¢', '0,15'.
    Returns float in USD.
    """
    text = text.replace(",", ".")
    if "¢" in text:
        m = re.search(r"[\d.]+", text)
        return float(m.group()) / 100 if m else 0.0
    m = re.search(r"[\d]+\.[\d]+|[\d]+", text)
    return float(m.group()) if m else 0.0


# ── Single card parser ────────────────────────────────────────────────────────

def parse_card(card) -> dict | None:
    """
    Parse one .jobslist card into a job dict.
    Returns None if any required field is missing.

    Fields returned:
      id, title, pay, done, total, remaining, ttr, success, url
    """
    try:
        # Title + URL (required — skip card if missing)
        name_el = card.select_one(".jobname a")
        if not name_el:
            return None
        title = name_el.get_text(strip=True)
        if not title:
            return None

        href    = name_el.get("href", "")
        job_url = (BASE_URL + "/" + href.lstrip("/")) if not href.startswith("http") else href

        # Pay
        pay_el = card.select_one(".jobpayment p")
        pay    = extract_amount(pay_el.get_text(strip=True) if pay_el else "0")

        # Slots done / total
        done_el   = card.select_one(".jobdone p")
        slots_raw = done_el.get_text(strip=True, separator="") if done_el else "0/0"
        m         = re.search(r"(\d+)\D+(\d+)", slots_raw)
        done      = int(m.group(1)) if m else 0
        total     = int(m.group(2)) if m else 0
        remaining = max(0, total - done)

        # Time-to-rate and success %
        ttr_el  = card.select_one(".jobttr p")
        ttr     = ttr_el.get_text(strip=True) if ttr_el else "?"
        succ_el = card.select_one(".jobsuccess p")
        success = succ_el.get_text(strip=True) if succ_el else "?"

        # Stable job ID — prefer URL param, fallback to title hash
        id_match = re.search(r"Id=([a-zA-Z0-9]+)", job_url, re.IGNORECASE)
        job_id   = id_match.group(1) if id_match else hashlib.md5(title.encode()).hexdigest()[:12]

        return {
            "id":        job_id,
            "title":     title,
            "pay":       pay,
            "done":      done,
            "total":     total,
            "remaining": remaining,
            "ttr":       ttr,
            "success":   success,
            "url":       job_url,
        }

    except Exception:
        return None


# ── Page parser ───────────────────────────────────────────────────────────────

def parse_jobs_page(html: str) -> list[dict]:
    """
    Parse the full jobs.php HTML and return all valid job dicts.
    """
    soup  = BeautifulSoup(html, "html.parser")
    cards = soup.select(".jobslist")
    jobs  = [j for card in cards if (j := parse_card(card)) is not None]
    return jobs


# ── Filter ────────────────────────────────────────────────────────────────────

def matches_filters(job: dict) -> bool:
    """
    Strict filter engine. Only allows jobs that are categorized as 
    'Email' by detect_category, have available slots, and meet min pay.
    """
    # 1. Check for minimum required pay
    if job["pay"] < MIN_PAY:
        return False
        
    # 2. Check if there are slots remaining
    if job["remaining"] <= 0:
        return False
        
    # 3. STRICT CATEGORY FILTER: Drop anything that isn't explicitly an 'Email' job
    if detect_category(job["title"]) != "Targeted Email":
        return False
        
    # Passes all strict filters!
    return True