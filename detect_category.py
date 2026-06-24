# detect_category.py
import re

_RULES = {
    "Email": [
        "email", "gmail", "ac1", "yhr", "maguru", "auto signup",
        "confirm email", "name email", "website email", "email submit",
        "email 2x", "email 3x", "email interaction",
    ],
    "YouTube": [
        "youtube", "ttv-video", "ttv youtube", "watch + like", "watch + comment",
        "stats for nerds", "youtube shorts", "youtube live", "search + watch",
        "video obtain", "hair transplant", "water drop",
    ],
    "Social Media": [
        "facebook", "instagram", "twitter", "linkedin", "reddit",
        "medium", "product hunt", "contest vote",
    ],
    "Search & Visit": [
        "bing", "duckduckgo", "startpage", "search + visit",
        "website search", "website engage", "visit page",
    ],
    "Data Collection": [
        "data collection", "image annotation", "sort annotation",
        "walmart", "data entry",
    ],
    "App Install": [
        "application install", "install + review", "app testing",
        "app install",
    ],
    "CPA Offers": [
        "cpa", "lead generation", "offer completion",
    ],
}

_PRIORITY = [
    "Email", "YouTube", "Social Media",
    "Search & Visit", "Data Collection", "App Install", "CPA Offers",
]

def detect_category(title: str) -> str:
    t = title.lower()
    for cat in _PRIORITY:
        for kw in _RULES[cat]:
            if kw in t:
                return cat
    return "Other"

def detect_subcategory(title: str) -> str:
    """Kept blank for now to support Step 4 future schema seamlessly"""
    return ""