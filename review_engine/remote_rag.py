import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SERVICE_URL = os.getenv("CODESEC_RAG_SERVICE_URL", "")
API_KEY = os.getenv("CODESEC_RAG_API_KEY", "")
TIMEOUT = int(os.getenv("CODESEC_RAG_TIMEOUT", "15"))


def search_remote_rag(query: str, top_k: int = 3) -> dict:
    if not SERVICE_URL:
        return {
            "results": [],
            "metadata": {},
            "error": "CODESEC_RAG_SERVICE_URL not configured",
        }

    url = f"{SERVICE_URL.rstrip('/')}/rag/search"
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-CodeSec-RAG-Key"] = API_KEY

    try:
        resp = requests.post(
            url,
            json={"query": query, "top_k": top_k},
            headers=headers,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("Remote RAG: %d results for query=%r (%.1fms)",
                     len(data.get("results", [])),
                     query,
                     data.get("metadata", {}).get("query_time_ms", 0))
        return data
    except requests.exceptions.RequestException as e:
        logger.warning("Remote RAG request failed: %s", e)
        return {
            "results": [],
            "metadata": {},
            "error": f"Remote RAG service unavailable: {e}",
        }


def remote_rag_available() -> bool:
    if not SERVICE_URL:
        return False
    try:
        resp = requests.get(f"{SERVICE_URL.rstrip('/')}/health", timeout=5)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False
