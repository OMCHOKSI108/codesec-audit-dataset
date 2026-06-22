from __future__ import annotations
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None

from review_engine.pipeline import review_code

GITHUB_API_BASE = "https://api.github.com"
COMMENT_MARKER = "<!-- codesec-audit-ai-review -->"
INLINE_FINGERPRINT_PREFIX = "<!-- codesec-audit-ai-inline:"
SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx"}
IGNORE_DIRS = {"node_modules", "dist", "build", ".venv", "venv", "data", "release", "notebooks", "__pycache__"}
MAX_INLINE_COMMENTS = 10


def _get_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise ValueError(f"{key} not set")
    return val


def get_jwt_token(app_id: str, private_key_pem: str) -> str:
    if pyjwt is None:
        raise ImportError("Install PyJWT: pip install pyjwt cryptography")
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 600, "iss": app_id}
    return pyjwt.encode(payload, private_key_pem, algorithm="RS256")


def get_installation_token(jwt_token: str, installation_id: str) -> str:
    url = f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens"
    resp = requests.post(url, headers={
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["token"]


def verify_webhook(payload_body: bytes, signature_header: str, secret: str) -> bool:
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def _should_skip(path: str) -> bool:
    p = Path(path)
    if any(part in IGNORE_DIRS for part in p.parts):
        return True
    if p.suffix not in SUPPORTED_EXTENSIONS:
        return True
    return False


def _parse_patch_added_lines(patch: str) -> set[int]:
    added: set[int] = set()
    new_offset = 0
    for line in patch.splitlines():
        if line.startswith("@@"):
            import re
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                new_offset = int(m.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            if new_offset:
                added.add(new_offset)
                new_offset += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
        elif line.startswith(" ") or line == "" or line.startswith("\\"):
            new_offset += 1
    return added


def _build_comment(summary: dict) -> str:
    lines = [COMMENT_MARKER, "", "# CodeSecAudit AI Review", "",
             f"## Verdict: **{summary['final_verdict']}**", "",
             f"Reviewed **{summary['total_files']}** changed file(s), "
             f"found **{summary['total_issues']}** issue(s). "
             f"Highest severity: **{summary['highest_severity'].capitalize()}**.", "",
             f"**Risk Score:** {summary['total_risk_score']}/100", ""]
    if summary["all_issues"]:
        rows = []
        for iss in summary["all_issues"]:
            rows.append(f"| `{iss['location']}` | {iss['cwe_id']} | {iss['severity'].capitalize()} | {iss['title']} |")
        lines.extend(["## Issues Found", "", "| Location | CWE | Severity | Issue |",
                      "|----------|-----|----------|-------|"] + rows + [""])
    else:
        lines.append("No security issues detected.")
    lines.append("---\n*Powered by CodeSecAudit AI*")
    return "\n".join(lines)


def _build_inline_body(issue: dict) -> str:
    p = issue.get("file", "unknown")
    ln = issue.get("line", 0)
    cwe = issue.get("cwe_id", "")
    fp = f"{INLINE_FINGERPRINT_PREFIX}{p}:{ln}:{cwe} -->"
    return (f"**CodeSecAudit AI:** {cwe} {issue['title']}\n\n"
            f"Severity: {issue.get('severity', 'medium').capitalize()}\n\n"
            f"{issue.get('explanation', '')}\n\n"
            f"Suggested fix: {issue.get('suggested_fix', '')}\n\n{fp}")


def _find_comment(token: str, owner: str, repo: str, pr_number: int) -> int | None:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}",
                                       "Accept": "application/vnd.github.v3+json"},
                        params={"per_page": 100}, timeout=30)
    if resp.status_code != 200:
        return None
    for c in resp.json():
        if COMMENT_MARKER in c.get("body", ""):
            return c["id"]
    return None


def _upsert_comment(token: str, owner: str, repo: str, pr_number: int, body: str) -> bool:
    existing = _find_comment(token, owner, repo, pr_number)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    if existing:
        url = f"{GITHUB_API_BASE}/repos/issues/comments/{existing}"
        resp = requests.patch(url, headers=headers, json={"body": body}, timeout=30)
    else:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        resp = requests.post(url, headers=headers, json={"body": body}, timeout=30)
    return resp.status_code in (200, 201)


def _post_inline_review(token: str, owner: str, repo: str, pr_number: int,
                        comments: list[dict], body: str) -> bool:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    payload = {"event": "COMMENT", "body": body, "comments": comments}
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}",
                                        "Accept": "application/vnd.github.v3+json"},
                         json=payload, timeout=30)
    return resp.status_code in (200, 201)


def process_pr(owner: str, repo: str, pr_number: int, token: str) -> dict:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files?per_page=100"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}",
                                       "Accept": "application/vnd.github.v3+json"}, timeout=30)
    if resp.status_code != 200:
        return {"status": "error", "reason": f"API returned {resp.status_code}"}

    pr_files = resp.json()
    supported = [f for f in pr_files if not _should_skip(f.get("filename", ""))]
    skipped = [f["filename"] for f in pr_files if _should_skip(f.get("filename", ""))]

    if not supported:
        body = _build_comment({"total_files": 0, "total_issues": 0, "highest_severity": "none",
                                "total_risk_score": 0, "final_verdict": "APPROVE", "all_issues": []})
        _upsert_comment(token, owner, repo, pr_number, body)
        return {"status": "skipped", "skipped_files": skipped}

    patch_map: dict[str, set[int]] = {}
    for f in supported:
        patch = f.get("patch", "")
        if patch:
            patch_map[f["filename"]] = _parse_patch_added_lines(patch)

    file_results = []
    for f in supported:
        fn = f["filename"]
        raw = f.get("raw_url", "")
        if not raw:
            continue
        r = requests.get(raw, timeout=30)
        if r.status_code != 200:
            continue
        result = review_code(code=r.text, file_path=fn, use_rag=False)
        file_results.append(result)

    total_issues = 0
    max_risk = 0
    severities: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    all_issues: list[dict] = []
    for res in file_results:
        issues = res.get("issues", [])
        total_issues += len(issues)
        risk = res.get("risk_score", 0)
        if risk > max_risk:
            max_risk = risk
        for iss in issues:
            sev = iss.get("severity", "medium")
            severities[sev] = severities.get(sev, 0) + 1
            fp = iss.get("file", "unknown")
            ln = iss.get("line")
            all_issues.append({
                "file": fp, "line": ln, "location": f"{fp}:{ln}" if ln else fp,
                "cwe_id": iss.get("cwe_id", ""), "severity": sev,
                "title": iss.get("title", ""),
                "code_snippet": iss.get("code_snippet", ""),
                "suggested_fix": iss.get("suggested_fix", ""),
            })

    highest = next((s for s in ["critical", "high", "medium", "low"] if severities.get(s, 0) > 0), "none")
    verdict = "WARNING" if total_issues > 0 else "APPROVE"
    summary_data = {"total_files": len(file_results), "total_issues": total_issues,
                    "highest_severity": highest, "total_risk_score": max_risk,
                    "final_verdict": verdict, "severity_counts": severities, "all_issues": all_issues}

    body = _build_comment(summary_data)
    _upsert_comment(token, owner, repo, pr_number, body)

    inline_comments: list[dict] = []
    posted = 0
    existing_fps: set[str] = set()
    for iss in all_issues:
        fpath = iss.get("file", "")
        lnum = iss.get("line")
        cwe = iss.get("cwe_id", "")
        added = patch_map.get(fpath)
        if added is not None and lnum and lnum in added:
            if posted >= MAX_INLINE_COMMENTS:
                break
            fp = f"{INLINE_FINGERPRINT_PREFIX}{fpath}:{lnum}:{cwe} -->"
            if fp in existing_fps:
                continue
            existing_fps.add(fp)
            inline_comments.append({"path": fpath, "line": lnum, "body": _build_inline_body(iss)})
            posted += 1

    if inline_comments:
        _post_inline_review(token, owner, repo, pr_number, inline_comments, body)

    return {"status": "completed", "total_issues": total_issues, "verdict": verdict,
            "inline_posted": posted, "skipped_files": skipped}


def handle_event(event_type: str, payload: dict) -> dict:
    if event_type != "pull_request":
        return {"status": "ignored", "reason": f"unhandled event: {event_type}"}
    action = payload.get("action", "")
    if action not in ("opened", "synchronize"):
        return {"status": "ignored", "reason": f"unhandled action: {action}"}

    pr = payload.get("pull_request", {})
    repo_info = payload.get("repository", {})
    owner = (repo_info.get("owner") or {}).get("login", "")
    repo = repo_info.get("name", "")
    pr_number = pr.get("number")
    installation_id = (payload.get("installation") or {}).get("id", "")
    if not all([owner, repo, pr_number, installation_id]):
        return {"status": "error", "reason": "missing owner/repo/pr/installation in payload"}

    app_id = _get_env("GITHUB_APP_ID")
    raw_key = _get_env("GITHUB_APP_PRIVATE_KEY")
    private_key = raw_key.replace("\\n", "\n")
    jwt_token = get_jwt_token(app_id, private_key)
    token = get_installation_token(jwt_token, str(installation_id))
    return process_pr(owner, repo, int(pr_number), token)
