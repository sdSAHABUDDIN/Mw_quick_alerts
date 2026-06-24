# detect_category.py
import re

_RULES = {
    "Targeted Email Jobs": [
        "email", 
        "name email", 
        "website email",
    ]
}

_PRIORITY = [
    "Targeted Email Jobs"
]

def detect_category(title: str) -> str:
    t = title.lower()
    for cat in _PRIORITY:
        for kw in _RULES[cat]:
            # Exact or substring phrase match
            if kw in t:
                return "Targeted Email"
    return "Other"

def detect_subcategory(title: str) -> str:
    """Kept blank for now to support Step 4 future schema seamlessly"""
    return ""