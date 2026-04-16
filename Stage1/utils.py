from datetime import datetime, timezone
from uuid6 import uuid7

def generate_id():
    return str(uuid7())

def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def classify_age(age: int):
    if 0 <= age <= 12:
        return "child"
    elif 13 <= age <= 19:
        return "teenager"
    elif 20 <= age <= 59:
        return "adult"
    else:
        return "senior"