from datetime import datetime, timezone

from website.config import Config


def get_usage(user: dict | None) -> dict:
    if not user:
        return {"used": 0, "limit": Config.FREE_PR_REVIEWS_PER_MONTH, "remaining": Config.FREE_PR_REVIEWS_PER_MONTH, "percent": 0, "extra": 0}
    used = user.get("reviews_used", 0)
    limit = user.get("reviews_limit", Config.FREE_PR_REVIEWS_PER_MONTH)
    extra = user.get("extra_reviews", 0)
    total_limit = limit + extra
    remaining = max(0, total_limit - used)
    percent = min(100, int((used / total_limit) * 100)) if total_limit > 0 else 0

    window_start = user.get("window_start")
    reset_date = ""
    if window_start:
        try:
            dt = datetime.fromisoformat(str(window_start).replace("Z", "+00:00"))
            reset_date = dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    return {
        "used": used,
        "limit": total_limit,
        "base_limit": limit,
        "remaining": remaining,
        "percent": percent,
        "extra": extra,
        "reset_date": reset_date,
    }


def remaining_reviews(user: dict | None) -> int:
    return get_usage(user)["remaining"]


def is_limit_reached(user: dict | None) -> bool:
    return remaining_reviews(user) <= 0


def usage_percent(user: dict | None) -> int:
    return get_usage(user)["percent"]
