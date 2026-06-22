import logging

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    pass


def fetch_reviews(api_url: str, limit: int = 20) -> list[dict]:
    import requests as req

    try:
        resp = req.get(f"{api_url}/reviews?limit={limit}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("reviews", data.get("data", []))
        return []
    except Exception as e:
        logger.warning(f"Failed to fetch reviews from API: {e}")
        return []


def fetch_stats(api_url: str) -> dict:
    import requests as req

    try:
        resp = req.get(f"{api_url}/stats", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Failed to fetch stats from API: {e}")
        return {}
