# detect_category.py
import re

_RULES = {
    "Email": [
        "email", "gmail", "auto signup",
        "confirm email", "name email", "website email", "email submit",
        
    ]
}

_PRIORITY = [
    "Email"
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