"""Check a deployed remote RAG service health and search."""

import json
import os
import sys
import time
from urllib import request, error

SERVICE_URL = os.getenv("CODESEC_RAG_SERVICE_URL", "")
API_KEY = os.getenv("CODESEC_RAG_API_KEY", "")

QUERY = "sql injection prepared statements"
TOP_K = 3


def check_health():
    t0 = time.time()
    try:
        resp = request.urlopen(f"{SERVICE_URL}/health", timeout=10)
        elapsed = (time.time() - t0) * 1000
        data = json.loads(resp.read())
        print(f"  status:           {data.get('status')}")
        print(f"  index_loaded:     {data.get('index_loaded')}")
        print(f"  total_chunks:     {data.get('total_chunks')}")
        print(f"  embedding_count:  {data.get('embedding_count')}")
        print(f"  embedding_model:  {data.get('embedding_model')}")
        print(f"  uptime:           {data.get('uptime_seconds')}s")
        print(f"  latency:          {elapsed:.0f}ms")
        return data.get("status") == "ok" and data.get("index_loaded") is True
    except Exception as e:
        print(f"  ERROR: health check failed: {e}")
        return False


def check_search():
    body = json.dumps({"query": QUERY, "top_k": TOP_K}).encode()
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-CodeSec-RAG-Key"] = API_KEY

    req = request.Request(
        f"{SERVICE_URL}/rag/search",
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        t0 = time.time()
        resp = request.urlopen(req, timeout=30)
        elapsed = (time.time() - t0) * 1000
        data = json.loads(resp.read())
        results = data.get("results", [])
        meta = data.get("metadata", {})

        print(f"  results:          {len(results)}")
        print(f"  query_time_ms:    {meta.get('query_time_ms', round(elapsed, 2))}")
        print(f"  total_latency_ms: {elapsed:.0f}")
        print(f"  total_chunks:     {meta.get('total_chunks')}")
        print(f"  model:            {meta.get('embedding_model')}")
        if results:
            r = results[0]
            print(f"  top_result:")
            print(f"    rank:   {r['rank']}")
            print(f"    score:  {r['score']:.4f}")
            print(f"    title:  {r['title']}")
            print(f"    cwe_id: {r['cwe_id']}")
            print(f"    source: {r['source_file']}")
        return len(results) > 0
    except Exception as e:
        print(f"  ERROR: search failed: {e}")
        return False


def main():
    if not SERVICE_URL:
        print("ERROR: CODESEC_RAG_SERVICE_URL is not set")
        sys.exit(1)

    print(f"Checking remote RAG service at: {SERVICE_URL}")
    if API_KEY:
        print(f"  Using API key authentication")
    print()

    print("[1/2] Health check:")
    ok_health = check_health()
    print()

    print(f"[2/2] Search test (query={QUERY!r}, top_k={TOP_K}):")
    ok_search = check_search()
    print()

    if ok_health and ok_search:
        print("OK: Remote RAG service is healthy and responding")
    else:
        print("FAIL: One or more checks failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
