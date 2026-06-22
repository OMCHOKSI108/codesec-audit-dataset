from website.config import Config


def get_usage(user: dict | None) -> dict:
    limit = Config.FREE_PR_REVIEWS_PER_MONTH
    used = (user or {}).get("reviews_used", 0)
    remaining = max(0, limit - used)
    percent = min(100, round((used / limit) * 100)) if limit > 0 else 0
    return {
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "percent": percent,
    }


def remaining_reviews(user: dict | None) -> int:
    return get_usage(user)["remaining"]


def usage_percent(user: dict | None) -> int:
    return get_usage(user)["percent"]
