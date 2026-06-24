"""
auth.py — Session management for Microworkers
Uses PHPSESSID cookie (proven working). No form login needed.

How to get PHPSESSID:
  1. Log into microworkers.com in Chrome
  2. Open DevTools → Application → Cookies → www.microworkers.com
  3. Copy the PHPSESSID value into your .env file
  4. Re-copy it every time your session expires (usually 1–7 days)
"""

import requests
from config import MW_PHPSESSID, JOBS_URL, HEADERS


def create_session() -> requests.Session:
    """
    Build an authenticated requests.Session using the PHPSESSID cookie.
    Raises RuntimeError if the session is expired or invalid.
    """
    if not MW_PHPSESSID:
        raise RuntimeError("MW_PHPSESSID is empty. Add it to your .env file.")

    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.set("PHPSESSID", MW_PHPSESSID, domain="www.microworkers.com")
    return session


def verify_session(session: requests.Session) -> bool:
    """
    Make a real request to confirm the session is still valid.
    Returns True if authenticated, False if cookie expired.
    """
    try:
        r = session.get(JOBS_URL, timeout=20)

        if "login" in r.url.lower():
            return False

        if "loginForm" in r.text or "sign_in" in r.text.lower():
            return False

        return True

    except requests.RequestException:
        return False


def is_session_expired(response: requests.Response) -> bool:
    """
    Quick check on an existing response — did MW silently redirect to login?
    Call this inside the main loop to catch mid-run expiry.
    """
    return "login" in response.url.lower() or "loginForm" in response.text
