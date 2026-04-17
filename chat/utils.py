from datetime import datetime, timezone

def get_age_group(age: int):
    if age <= 12:
        return "child"
    elif age <= 19:
        return "teenager"
    elif age <= 59:
        return "adult"
    return "senior"


def utc_now():
    return datetime.now(timezone.utc)