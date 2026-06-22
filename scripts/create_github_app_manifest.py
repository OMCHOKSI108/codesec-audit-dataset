#!/usr/bin/env python3
"""Generate a GitHub App manifest and print the registration URL.

Usage:
    python scripts/create_github_app_manifest.py
    python scripts/create_github_app_manifest.py --org MyOrg
    python scripts/create_github_app_manifest.py --help
"""
import argparse
import json
import os
import urllib.parse

REPO_URL = "https://github.com/OMCHOKSI108/codesec-audit-dataset"

DEFAULTS = {
    "name": "CodeSecAudit AI",
    "url": os.environ.get("PUBLIC_WEBSITE_URL") or os.environ.get("API_BASE_URL") or REPO_URL,
    "callback_url": os.environ.get("GITHUB_CALLBACK_URL", ""),
    "webhook_url": os.environ.get("GITHUB_WEBHOOK_URL", ""),
}

PERMISSIONS = {
    "contents": "read",
    "pull_requests": "write",
    "issues": "write",
    "checks": "write",
    "metadata": "read",
}

EVENTS = [
    "pull_request",
    "installation",
    "installation_repositories",
]


def build_manifest(callback_url: str = "", webhook_url: str = "") -> dict:
    hook = None
    if webhook_url:
        hook = {"url": webhook_url, "active": True}

    manifest = {
        "name": DEFAULTS["name"],
        "url": DEFAULTS["url"],
        "public": False,
        "default_permissions": PERMISSIONS,
        "default_events": EVENTS,
    }

    if callback_url:
        manifest["redirect_url"] = callback_url
    if hook:
        manifest["hook_attributes"] = hook

    return manifest


def write_manifest(manifest: dict, path: str = ".github-app-manifest.json") -> str:
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    return os.path.abspath(path)


def build_register_url(manifest: dict, org: str | None = None) -> str:
    encoded = urllib.parse.quote(json.dumps(manifest))
    if org:
        return f"https://github.com/organizations/{org}/settings/apps/new?manifest={encoded}"
    return f"https://github.com/settings/apps/new?manifest={encoded}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate GitHub App manifest for CodeSecAudit AI"
    )
    parser.add_argument("--org", help="GitHub organization name (for org-level app)")
    parser.add_argument(
        "--webhook-url",
        default=DEFAULTS["webhook_url"],
        help=f"Webhook URL (default: GITHUB_WEBHOOK_URL env or empty)",
    )
    parser.add_argument(
        "--callback-url",
        default=DEFAULTS["callback_url"],
        help=f"OAuth callback URL (default: GITHUB_CALLBACK_URL env or empty)",
    )
    parser.add_argument(
        "--output",
        default=".github-app-manifest.json",
        help="Output path for manifest JSON (default: .github-app-manifest.json)",
    )

    args = parser.parse_args()

    manifest = build_manifest(
        callback_url=args.callback_url,
        webhook_url=args.webhook_url,
    )

    out_path = write_manifest(manifest, args.output)
    reg_url = build_register_url(manifest, org=args.org)

    print("=" * 72)
    print("  CodeSecAudit AI — GitHub App Manifest")
    print("=" * 72)
    print()
    print(f"  Manifest written: {out_path}")
    print()
    print(f"  Step 1: Open this URL in your browser:")
    print(f"  {reg_url}")
    print()
    print(f"  Step 2: Click 'Create GitHub App'")
    print(f"  Step 3: After redirect, copy the 'code' query parameter")
    print(f"  Step 4: Run:")
    print(f'    python scripts/complete_github_app_manifest.py --code YOUR_CODE')
    print()
    print(f"  Permissions requested:")
    for perm, level in PERMISSIONS.items():
        print(f"    - {perm}: {level}")
    print()
    print(f"  Events subscribed:")
    for evt in EVENTS:
        print(f"    - {evt}")
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
