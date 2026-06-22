import requests
from website.config import Config


def fetch_reviews(limit: int = 50, offset: int = 0) -> list[dict]:
    try:
        url = f"{Config.CODESEC_API_URL}/reviews"
        resp = requests.get(url, params={"limit": limit, "offset": offset}, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return []


def fetch_stats() -> dict:
    try:
        url = f"{Config.CODESEC_API_URL}/stats"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return {}


def fetch_review(review_id: str) -> dict | None:
    try:
        url = f"{Config.CODESEC_API_URL}/reviews/{review_id}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return None
