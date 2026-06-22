# Safe comparison demo file for CodeSecAudit AI PR review testing.
# This file demonstrates secure alternatives to the vulnerable demo.

import hashlib
import os
import subprocess


API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "fallback-dev-only")


def safe_process_data(data):
    # Use ast.literal_eval for safe evaluation of literals
    import ast
    try:
        return ast.literal_eval(data)
    except (ValueError, SyntaxError):
        return None


def safe_hash(password):
    # Use SHA-256 or stronger for integrity; use bcrypt/argon2 for passwords
    return hashlib.sha256(password.encode()).hexdigest()


def run_command_safe(target_host):
    # Use subprocess without shell=True and pass args as a list
    result = subprocess.run(
        ["ping", "-c", "1", target_host],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout


def fetch_user_data_safe(user_id):
    # Parameterized query — use a real DB driver with placeholders
    query = "SELECT * FROM users WHERE id = ?"
    print(f"Executing: {query} with id={user_id}")
    return query


def download_report_safe(report_id):
    import requests
    # Validate the report ID against an allowlist
    valid_reports = {"report-001", "report-002", "report-003"}
    if report_id not in valid_reports:
        raise ValueError("Invalid report ID")
    url = f"https://internal.api/reports/{report_id}"
    resp = requests.get(url, timeout=30)
    return resp.text
