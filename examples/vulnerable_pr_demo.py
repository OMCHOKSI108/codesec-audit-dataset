# Intentionally vulnerable demo file for CodeSecAudit AI PR review testing.
# Do not use this code in production.

import hashlib
import os
import subprocess


API_SECRET_KEY = "sk-live-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"


def unsafe_eval(user_input):
    result = eval(user_input)
    return result


def unsafe_hash(password):
    return hashlib.md5(password.encode()).hexdigest()


def run_command(user_cmd):
    os.system("ping -c 1 " + user_cmd)


def fetch_user_data(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    print(f"Executing: {query}")
    return query


def download_report(url):
    import requests
    resp = requests.get("https://internal.api/" + url, timeout=30)
    return resp.text


def unsafe_sha1(data):
    return hashlib.sha1(data.encode()).hexdigest()
