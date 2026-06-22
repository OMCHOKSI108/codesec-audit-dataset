#!/usr/bin/env python3
"""Exchange a GitHub App manifest code for credentials.

Usage:
    python scripts/complete_github_app_manifest.py --code TEMP_CODE
    python scripts/complete_github_app_manifest.py --help
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)


GITHUB_API = "https://api.github.com"
SECRETS_DIR = Path("secrets")
CREDENTIALS_FILE = SECRETS_DIR / "github_app_credentials.local.json"


def exchange_code(code: str) -> dict:
    url = f"{GITHUB_API}/app-manifests/{code}/conversions"
    resp = requests.post(
        url,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "codesec-audit-ai",
        },
        timeout=30,
    )
    if resp.status_code != 201:
        print(f"Error: GitHub API returned {resp.status_code}", file=sys.stderr)
        print(resp.text[:500], file=sys.stderr)
        sys.exit(1)
    return resp.json()


def build_output(creds: dict) -> dict:
    pem = creds.get("pem", "")
    pem_b64 = base64.b64encode(pem.encode()).decode() if pem else ""
    return {
        "app_id": str(creds.get("id", "")),
        "slug": creds.get("slug", ""),
        "client_id": creds.get("client_id", ""),
        "client_secret": creds.get("client_secret", ""),
        "webhook_secret": creds.get("webhook_secret", ""),
        "pem": pem,
        "pem_base64": pem_b64,
    }


def save_credentials(data: dict) -> str:
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return str(CREDENTIALS_FILE.resolve())


def print_safe_summary(data: dict):
    print("=" * 72)
    print("  GitHub App Registered Successfully")
    print("=" * 72)
    print()
    print(f"  App ID:   {data['app_id']}")
    print(f"  Slug:     {data['slug']}")
    print(f"  Client ID: {data['client_id']}")
    print()
    print("  Credentials saved to: secrets/github_app_credentials.local.json")
    print()
    print("  Set these environment variables (values hidden):")
    print()
    print(f"    GITHUB_APP_ID={data['app_id']}")
    print(f"    GITHUB_APP_SLUG={data['slug']}")
    print(f"    GITHUB_CLIENT_ID={data['client_id']}")
    print(f"    GITHUB_CLIENT_SECRET=<saved to secrets/>")
    print(f"    GITHUB_WEBHOOK_SECRET=<saved to secrets/>")
    print(f"    GITHUB_PRIVATE_KEY_BASE64=<saved to secrets/>")
    print()
    print("  To apply to .env:")
    print("    python scripts/apply_github_app_env.py")
    print("    python scripts/apply_github_app_env.py --write  (to actually write)")
    print()
    print("  To apply to Render:")
    print("    Use the Render dashboard or CLI to set these env vars:")
    print("    - GITHUB_APP_ID")
    print("    - GITHUB_APP_SLUG")
    print("    - GITHUB_CLIENT_ID")
    print("    - GITHUB_CLIENT_SECRET")
    print("    - GITHUB_WEBHOOK_SECRET")
    print("    - GITHUB_PRIVATE_KEY_BASE64")
    print()
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(
        description="Complete GitHub App manifest registration"
    )
    parser.add_argument("--code", required=True, help="Temporary code from GitHub redirect")
    args = parser.parse_args()

    creds = exchange_code(args.code.strip())
    output = build_output(creds)
    saved_path = save_credentials(output)
    print_safe_summary(output)


if __name__ == "__main__":
    main()
