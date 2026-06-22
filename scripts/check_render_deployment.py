#!/usr/bin/env python3
"""
Smoke test for CodeSecAudit AI Render deployment.

Tests:
  - API /health
  - API /
  - API /review/code
  - API /stats
  - Dashboard URL
  - Review UI URL

Usage:
    export RENDER_API_URL=https://codesec-api.onrender.com
    export RENDER_DASHBOARD_URL=https://codesec-dashboard.onrender.com
    export RENDER_REVIEW_UI_URL=https://codesec-review-ui.onrender.com
    python scripts/check_render_deployment.py
"""

import os
import sys
import json
import urllib.request
import urllib.error
import time

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"


def check_url(url: str, method: str = "GET", data: dict | None = None,
              timeout: int = 30) -> tuple[bool, int, str | None]:
    try:
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        if body:
            req.add_header("Content-Type", "application/json")
        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - start
            content = resp.read().decode()
            return True, resp.status, content[:200], elapsed
    except urllib.error.HTTPError as e:
        return False, e.code, str(e), 0
    except Exception as e:
        return False, 0, str(e), 0


def check(name: str, url: str, method: str = "GET",
          data: dict | None = None, expect_status: int = 200) -> tuple[bool, str]:
    ok, status, body, elapsed = check_url(url, method, data)
    status_match = status == expect_status
    passed = ok and status_match

    label = f"[{name}]"
    dots = max(1, 60 - len(label))
    elapsed_str = f"{elapsed:.1f}s" if elapsed else ""
    status_line = f"{label}{'.' * dots} {PASS if passed else FAIL}"
    if elapsed_str:
        status_line += f"  ({elapsed_str})"
    print(status_line)

    if not passed:
        detail = body if isinstance(body, str) else str(body)
        print(f"  Expected {expect_status}, got {status}: {detail[:150]}")

    return passed


def main():
    api = os.getenv("RENDER_API_URL", "").rstrip("/")
    dashboard = os.getenv("RENDER_DASHBOARD_URL", "").rstrip("/")
    review_ui = os.getenv("RENDER_REVIEW_UI_URL", "").rstrip("/")

    if not api:
        print("ERROR: RENDER_API_URL not set.")
        print("Usage:")
        print("  export RENDER_API_URL=https://codesec-api.onrender.com")
        print("  export RENDER_DASHBOARD_URL=https://codesec-dashboard.onrender.com")
        print("  export RENDER_REVIEW_UI_URL=https://codesec-review-ui.onrender.com")
        print("  python scripts/check_render_deployment.py")
        sys.exit(1)

    all_pass = True

    print(f"\nChecking Render deployment:\n")
    print(f"  API:         {api}")
    print(f"  Dashboard:   {dashboard or '(not set)'}")
    print(f"  Review UI:   {review_ui or '(not set)'}\n")

    # 1. /health
    all_pass &= check("1/6 API /health", f"{api}/health")

    # 2. /
    all_pass &= check("2/6 API /", api)

    # 3. /review/code
    all_pass &= check(
        "3/6 API /review/code",
        f"{api}/review/code",
        method="POST",
        data={"code": "eval(user_input)", "file_path": "test.py"},
    )

    # 4. /stats
    all_pass &= check("4/6 API /stats", f"{api}/stats")

    # 5. Dashboard URL
    if dashboard:
        all_pass &= check("5/6 Dashboard URL", dashboard)
    else:
        print(f"[5/6 Dashboard URL]...... SKIP (not set)")

    # 6. Review UI URL
    if review_ui:
        all_pass &= check("6/6 Review UI URL", review_ui)
    else:
        print(f"[6/6 Review UI URL]...... SKIP (not set)")

    print()
    if all_pass:
        print("All checks passed.")
        sys.exit(0)
    else:
        print("Some checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
