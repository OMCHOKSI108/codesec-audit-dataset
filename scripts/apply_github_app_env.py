#!/usr/bin/env python3
"""Apply saved GitHub App credentials to .env (safe dry-run by default).

Usage:
    python scripts/apply_github_app_env.py          # dry-run
    python scripts/apply_github_app_env.py --write  # actually write
    python scripts/apply_github_app_env.py --help
"""
import argparse
import json
import os
import sys
from pathlib import Path

SECRETS_FILE = Path("secrets/github_app_credentials.local.json")
ENV_FILE = Path(".env")

# Map credential keys to .env variable names
KEY_MAP = {
    "app_id": "GITHUB_APP_ID",
    "slug": "GITHUB_APP_SLUG",
    "client_id": "GITHUB_CLIENT_ID",
    "client_secret": "GITHUB_CLIENT_SECRET",
    "webhook_secret": "GITHUB_WEBHOOK_SECRET",
    "pem_base64": "GITHUB_PRIVATE_KEY_BASE64",
}


def load_credentials(path: Path) -> dict:
    if not path.exists():
        print(f"Credentials not found: {path}", file=sys.stderr)
        print("Run: python scripts/complete_github_app_manifest.py --code YOUR_CODE", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def read_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip()
    return env


def write_env(path: Path, env: dict):
    with open(path, "w") as f:
        for key, val in env.items():
            f.write(f"{key}={val}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Apply GitHub App credentials to .env"
    )
    parser.add_argument("--write", action="store_true", help="Actually write to .env")
    args = parser.parse_args()

    creds = load_credentials(SECRETS_FILE)
    current = read_env(ENV_FILE)

    updates = {}
    for cred_key, env_key in KEY_MAP.items():
        val = creds.get(cred_key, "")
        if val:
            updates[env_key] = val

    print("=" * 72)
    print("  Apply GitHub App Credentials to .env")
    print("=" * 72)
    print()
    if args.write:
        print("  Mode: WRITE")
    else:
        print("  Mode: DRY-RUN (pass --write to apply)")
    print()

    changed = 0
    for env_key, val in updates.items():
        old = current.get(env_key, "")
        status = "update" if old else "  new"
        if old:
            changed += 1
        print(f"    [{status}] {env_key}")
    if not updates:
        print("  No credentials to apply.")

    print()
    if args.write:
        current.update(updates)
        write_env(ENV_FILE, current)
        print(f"  Written {len(updates)} keys to {ENV_FILE}")
    else:
        if changed:
            print(f"  {changed} key(s) would be updated.")
        print("  Run with --write to apply.")
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
