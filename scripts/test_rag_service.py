"""Smoke test for the local RAG service."""

import subprocess
import sys
import time
from urllib import request, error

SERVICE_URL = "http://localhost:7860"


def test_health():
    try:
        resp = request.urlopen(f"{SERVICE_URL}/health", timeout=5)
        data = resp.read().decode()
        print(f"OK: GET /health -> {resp.status}")
        return True
    except Exception as e:
        print(f"FAIL: GET /health -> {e}")
        return False


def test_search():
    import json

    body = json.dumps({"query": "sql injection prepared statements", "top_k": 3}).encode()
    req = request.Request(
        f"{SERVICE_URL}/rag/search",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode())
        n = len(data.get("results", []))
        print(f"OK: POST /rag/search -> {n} results, "
              f"query_time={data['metadata']['query_time_ms']}ms")
        if n > 0:
            r = data["results"][0]
            print(f"     Top result: [{r['cwe_id']}] {r['title']} "
                  f"(score={r['score']:.3f})")
        return True
    except Exception as e:
        print(f"FAIL: POST /rag/search -> {e}")
        return False


def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        globals()["SERVICE_URL"] = base_url

    print(f"Testing RAG service at {SERVICE_URL}")
    print()

    checks = [test_health, test_search]
    failures = 0
    for check in checks:
        if not check():
            failures += 1
        print()

    if failures:
        print(f"{failures} check(s) FAILED")
        sys.exit(1)
    else:
        print("All checks passed!")


if __name__ == "__main__":
    main()
