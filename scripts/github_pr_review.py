
import json
import os
import re
import sys
import subprocess
from pathlib import Path

import requests

from review_engine.pipeline import review_code

try:
    from review_store import init_db, save_review
    _HAS_DB = True
except ImportError:
    _HAS_DB = False

COMMENT_MARKER = "<!-- codesec-audit-ai-review -->"
INLINE_FINGERPRINT_PREFIX = "<!-- codesec-audit-ai-inline:"

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx"}

IGNORE_DIRS = {
    "node_modules", "dist", "build", ".venv", "venv",
    "data", "release", "notebooks", ".ipynb_checkpoints", "__pycache__",
}

IGNORE_PATTERNS = {
    "*.min.js", "*.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
}

MAX_FILE_SIZE = 200 * 1024
MAX_INLINE_COMMENTS = 10

GITHUB_API_BASE = "https://api.github.com"

_CONFIG: dict = {}
_IGNORE_PATTERNS_FROM_FILE: list[str] = []


def _load_config() -> None:
    global _CONFIG, _IGNORE_PATTERNS_FROM_FILE, MAX_INLINE_COMMENTS, SUPPORTED_EXTENSIONS
    workspace = os.environ.get("GITHUB_WORKSPACE", ".")

    yml_path = Path(workspace) / ".codesec.yml"
    if yml_path.exists():
        try:
            import yaml
            _CONFIG = yaml.safe_load(yml_path.read_text()) or {}
        except ImportError:
            print("  [config] Install PyYAML to read .codesec.yml; using defaults", file=sys.stderr)
        except Exception as e:
            print(f"  [config] Error loading .codesec.yml: {e}", file=sys.stderr)

    if "max_inline_comments" in _CONFIG:
        MAX_INLINE_COMMENTS = int(_CONFIG["max_inline_comments"])
    if "supported_extensions" in _CONFIG:
        SUPPORTED_EXTENSIONS = set(_CONFIG["supported_extensions"])

    ignore_path = Path(workspace) / ".codesecignore"
    if ignore_path.exists():
        for raw in ignore_path.read_text().splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                _IGNORE_PATTERNS_FROM_FILE.append(line)


def _matches_pattern(pattern: str, path_str: str) -> bool:
    pp = Path(path_str)
    if pattern.startswith("/"):
        pattern = pattern[1:]
    dir_only = pattern.endswith("/")
    if dir_only:
        pattern = pattern[:-1]
    if "/" in pattern:
        return pp.match(pattern)
    else:
        if dir_only:
            return pattern in pp.parts
        return any(Path(p).match(pattern) for p in pp.parts) or pp.match(pattern)


def _should_skip(path: str) -> bool:
    parts = Path(path).parts
    for part in parts:
        if part in IGNORE_DIRS:
            return True
    if any(path.endswith(suffix) for suffix in [".min.js", ".lock"]):
        return True
    basename = Path(path).name
    if basename in IGNORE_PATTERNS:
        return True
    ext = Path(path).suffix
    if ext not in SUPPORTED_EXTENSIONS:
        return True
    if _IGNORE_PATTERNS_FROM_FILE:
        for pat in _IGNORE_PATTERNS_FROM_FILE:
            if _matches_pattern(pat, path):
                return True
    return False


# --- Patch parsing ---

def parse_patch_added_lines(patch: str) -> set[int]:
    added: set[int] = set()
    new_offset = 0
    for line in patch.splitlines():
        if line.startswith("@@ "):
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                new_offset = int(m.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            added.add(new_offset)
            new_offset += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
        elif line.startswith(" ") or line == "" or line.startswith("\\"):
            new_offset += 1
    return added


def _parse_patch_check():
    patch = (
        "@@ -1,1 +1,2 @@\n"
        " user_input = input(\"expr: \")\n"
        "+result = eval(user_input)\n"
    )
    result = parse_patch_added_lines(patch)
    expected = {2}
    assert result == expected, f"Patch parse test failed: {result} != {expected}"
    return True


# --- GitHub API helpers ---

def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def _get_changed_files_from_git(base_ref: str, head_ref: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref, head_ref],
            capture_output=True, text=True, check=True, timeout=30,
        )
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"git diff failed: {e}", file=sys.stderr)
        return []


def _get_pr_files_with_patch(owner: str, repo: str, pr_number: int, token: str) -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    params: dict = {"per_page": 100}
    files: list[dict] = []
    page = 0
    while True:
        page += 1
        params["page"] = page
        resp = requests.get(url, headers=_headers(token), params=params, timeout=30)
        if resp.status_code != 200:
            print(f"GitHub API error: {resp.status_code}", file=sys.stderr)
            break
        data = resp.json()
        if not data:
            break
        for f in data:
            files.append({
                "filename": f.get("filename", ""),
                "patch": f.get("patch", ""),
                "status": f.get("status", ""),
            })
    return files


def _get_changed_files_from_api(owner: str, repo: str, pr_number: int, token: str) -> list[str]:
    return [f["filename"] for f in _get_pr_files_with_patch(owner, repo, pr_number, token)]


def _read_file_content(file_path: str) -> str | None:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return None
    if path.stat().st_size > MAX_FILE_SIZE:
        print(f"  Skipping {file_path}: file too large ({path.stat().st_size} bytes)", file=sys.stderr)
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  Error reading {file_path}: {e}", file=sys.stderr)
        return None


# --- Summary comment helpers ---

def _find_existing_comment(owner: str, repo: str, pr_number: int, token: str) -> int | None:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    params = {"per_page": 100}
    resp = requests.get(url, headers=_headers(token), params=params, timeout=30)
    if resp.status_code != 200:
        print(f"Failed to list comments: {resp.status_code}", file=sys.stderr)
        return None
    for comment in resp.json():
        if COMMENT_MARKER in comment.get("body", ""):
            return comment["id"]
    return None


def _update_comment(comment_id: int, body: str, token: str) -> bool:
    url = f"{GITHUB_API_BASE}/repos/issues/comments/{comment_id}"
    resp = requests.patch(url, headers=_headers(token), json={"body": body}, timeout=30)
    if resp.status_code not in (200, 201):
        print(f"Failed to update comment: {resp.status_code}", file=sys.stderr)
        return False
    return True


def _create_comment(owner: str, repo: str, pr_number: int, body: str, token: str) -> bool:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    resp = requests.post(url, headers=_headers(token), json={"body": body}, timeout=30)
    if resp.status_code not in (200, 201):
        print(f"Failed to create comment: {resp.status_code}", file=sys.stderr)
        return False
    return True


# --- Inline comment helpers ---

def _build_inline_fingerprint(path: str, line: int, cwe_id: str) -> str:
    return f"{INLINE_FINGERPRINT_PREFIX}{path}:{line}:{cwe_id} -->"


def _build_inline_comment_body(issue: dict) -> str:
    cwe = issue.get("cwe_id", "")
    title = issue.get("title", "")
    sev = issue.get("severity", "medium").capitalize()
    explanation = issue.get("explanation", "")
    fix = issue.get("suggested_fix", "")
    path = issue.get("file", "unknown")
    line = issue.get("line", 0)
    fingerprint = _build_inline_fingerprint(path, line, cwe)

    body = (
        f"**CodeSecAudit AI:** {cwe} {title}\n\n"
        f"Severity: {sev}\n\n"
        f"{explanation}\n\n"
        f"Suggested fix: {fix}\n\n"
        f"{fingerprint}"
    )
    return body


def _fetch_existing_inline_fingerprints(owner: str, repo: str, pr_number: int, token: str) -> set[str]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    params = {"per_page": 100}
    existing: set[str] = set()
    page = 0
    while True:
        page += 1
        params["page"] = page
        resp = requests.get(url, headers=_headers(token), params=params, timeout=30)
        if resp.status_code != 200:
            print(f"Failed to list PR comments: {resp.status_code}", file=sys.stderr)
            break
        data = resp.json()
        if not data:
            break
        for comment in data:
            body = comment.get("body", "")
            for token_body in body.split():
                if token_body.startswith(INLINE_FINGERPRINT_PREFIX):
                    existing.add(token_body.strip())
    return existing


def _post_inline_review(owner: str, repo: str, pr_number: int, token: str, comments: list[dict], summary_body: str) -> bool:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    payload = {
        "event": "COMMENT",
        "body": summary_body,
        "comments": comments,
    }
    resp = requests.post(url, headers=_headers(token), json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        print(f"Failed to post inline review: {resp.status_code}", file=sys.stderr)
        print(f"Response: {resp.text[:500]}", file=sys.stderr)
        return False
    print(f"Inline review posted: {len(comments)} comment(s)", file=sys.stderr)
    return True


# --- Review and aggregation ---

def _review_file(file_path: str, code: str) -> dict:
    return review_code(code=code, file_path=file_path, use_rag=False)


def _aggregate_results(file_results: list[dict]) -> dict:
    total_files = len(file_results)
    total_issues = 0
    max_risk = 0
    severities = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    all_issues = []

    for res in file_results:
        issues = res.get("issues", [])
        total_issues += len(issues)
        risk = res.get("risk_score", 0)
        if risk > max_risk:
            max_risk = risk
        for issue in issues:
            sev = issue.get("severity", "medium")
            if sev in severities:
                severities[sev] += 1
            fpath = issue.get("file") or "unknown"
            lnum = issue.get("line")
            location = f"{fpath}:{lnum}" if lnum else fpath
            all_issues.append({
                "file": issue.get("file", "unknown"),
                "line": issue.get("line"),
                "location": location,
                "cwe_id": issue.get("cwe_id", ""),
                "severity": sev,
                "title": issue.get("title", ""),
                "code_snippet": issue.get("code_snippet", ""),
                "suggested_fix": issue.get("suggested_fix", ""),
                "inline_status": issue.get("inline_status", "unknown"),
            })

    severity_order = ["critical", "high", "medium", "low"]
    highest_severity = "none"
    for s in severity_order:
        if severities[s] > 0:
            highest_severity = s
            break

    any_request = any(res.get("verdict") == "REQUEST_CHANGES" for res in file_results)
    any_warning = any(res.get("verdict") == "WARNING" for res in file_results)
    if any_request:
        final_verdict = "REQUEST_CHANGES"
    elif any_warning:
        final_verdict = "WARNING"
    else:
        final_verdict = "APPROVE"

    return {
        "total_files": total_files,
        "total_issues": total_issues,
        "highest_severity": highest_severity,
        "total_risk_score": max_risk,
        "final_verdict": final_verdict,
        "severity_counts": severities,
        "all_issues": all_issues,
    }


# --- Markdown builders ---

def _build_markdown(summary: dict, inline_posted: int | None = None) -> str:
    lines = []
    lines.append(COMMENT_MARKER)
    lines.append("")
    lines.append("# CodeSecAudit AI Review")
    lines.append("")
    lines.append(f"## Verdict: **{summary['final_verdict']}**")
    lines.append("")
    sev = summary["highest_severity"]
    sev_label = sev.capitalize() if sev != "none" else "None"
    lines.append(
        f"## Summary\n"
        f"Reviewed **{summary['total_files']}** changed code file(s) "
        f"and found **{summary['total_issues']}** potential issue(s). "
        f"Highest severity: **{sev_label}**."
    )
    lines.append("")
    lines.append(f"## Risk Score\n**{summary['total_risk_score']}/100**")
    lines.append("")

    if inline_posted is not None and summary["total_issues"] > inline_posted:
        lines.append(
            f"> Only the first {inline_posted} inline comment(s) were posted. "
            f"See table below for the full list of {summary['total_issues']} issue(s)."
        )
        lines.append("")

    if summary["all_issues"]:
        header = "| Location | CWE | Severity | Issue | Suggested Fix |"
        sep = "|----------|-----|----------|-------|---------------|"
        rows = []
        for issue in summary["all_issues"]:
            loc = issue.get("location") or "unknown"
            cwe = issue["cwe_id"] or "—"
            sev = issue["severity"].capitalize()
            title = issue["title"]
            fix = issue["suggested_fix"].replace("\n", "<br>").replace("|", "\\|")[:200]
            rows.append(f"| `{loc}` | {cwe} | {sev} | {title} | {fix} |")
        lines.append("## Issues Found")
        lines.append("")
        lines.append(header)
        lines.append(sep)
        lines.extend(rows)
        lines.append("")
    else:
        lines.append("## Issues Found\nNo security issues detected.")
        lines.append("")

    lines.append("---")
    lines.append("### Notes")
    lines.append("- This is an AI-assisted defensive security review.")
    lines.append("- It does not replace manual review or professional SAST tools.")
    lines.append("")
    return "\n".join(lines)


def _build_inline_plan_markdown(all_issues: list[dict]) -> str:
    lines = []
    lines.append("## Inline Comment Plan\n")
    header = "| Location | CWE | Severity | Will Inline Comment? | Reason |"
    sep = "|----------|-----|----------|----------------------|--------|"
    rows = []
    for issue in all_issues:
        loc = issue.get("location") or "unknown"
        cwe = issue["cwe_id"] or "—"
        sev = issue["severity"].capitalize()
        status = issue.get("inline_status", "unknown")
        if status == "dry-run-local":
            reason = "explicit file mode (no PR patch)"
        elif status == "commentable":
            reason = "line is in PR diff"
        elif status == "not-commentable":
            reason = "line not in PR diff"
        elif status == "skipped-cap":
            reason = "inline comment cap reached"
        elif status == "duplicate":
            reason = "already has inline comment"
        else:
            reason = "unknown"
        rows.append(f"| `{loc}` | {cwe} | {sev} | {status} | {reason} |")
    lines.append(header)
    lines.append(sep)
    lines.extend(rows)
    lines.append("")
    return "\n".join(lines)


# --- Dry-run ---

def _dry_run_report(explicit_files: list[str] | None = None) -> str:
    file_results = []
    sources: list[str] = explicit_files if explicit_files else []

    for filepath in sources:
        code = _read_file_content(filepath)
        if code is None:
            print(f"  Skipping {filepath}: cannot read or too large", file=sys.stderr)
            continue
        print(f"  Reviewing {filepath}...", file=sys.stderr)
        result = _review_file(filepath, code)
        for issue in result.get("issues", []):
            issue["inline_status"] = "dry-run-local"
        file_results.append(result)

    summary = _aggregate_results(file_results)
    markdown = _build_markdown(summary)
    plan = _build_inline_plan_markdown(summary["all_issues"])
    return markdown + "\n" + plan


# --- CI run ---

def _ci_run():
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("GITHUB_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path or not Path(event_path).exists():
        print(f"GITHUB_EVENT_PATH not found: {event_path}", file=sys.stderr)
        sys.exit(1)

    with open(event_path, "r") as f:
        event = json.load(f)

    repo_full = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repo_full:
        print(f"Invalid GITHUB_REPOSITORY: {repo_full}", file=sys.stderr)
        sys.exit(1)
    owner, repo = repo_full.split("/", 1)

    pr_number = event.get("pull_request", {}).get("number")
    if not pr_number:
        print("No pull request number found in event", file=sys.stderr)
        sys.exit(1)

    base_sha = event.get("pull_request", {}).get("base", {}).get("sha", "")
    head_sha = event.get("pull_request", {}).get("head", {}).get("sha", "")

    print(f"Reviewing PR #{pr_number} ({base_sha[:8]}...{head_sha[:8]})", file=sys.stderr)

    # Get changed files — prefer API for patch data
    pr_files = _get_pr_files_with_patch(owner, repo, pr_number, token)
    if not pr_files:
        # Fallback to git
        changed = _get_changed_files_from_git(base_sha, head_sha) if base_sha and head_sha else []
        supported = [f for f in changed if not _should_skip(f)]
        print(f"Changed files (git fallback): {len(changed)}, Supported: {len(supported)}", file=sys.stderr)
        if not supported:
            body = _build_markdown({
                "total_files": 0, "total_issues": 0, "highest_severity": "none",
                "total_risk_score": 0, "final_verdict": "APPROVE",
                "all_issues": [],
            })
            existing = _find_existing_comment(owner, repo, pr_number, token)
            if existing:
                _update_comment(existing, body, token)
            else:
                _create_comment(owner, repo, pr_number, body, token)
            return

        file_results = []
        for fp in supported:
            code = _read_file_content(fp)
            if code is None:
                continue
            print(f"  Reviewing {fp}...", file=sys.stderr)
            result = _review_file(fp, code)
            file_results.append(result)

        summary = _aggregate_results(file_results)
        markdown = _build_markdown(summary)
        existing = _find_existing_comment(owner, repo, pr_number, token)
        if existing:
            _update_comment(existing, markdown, token)
        else:
            _create_comment(owner, repo, pr_number, markdown, token)
        return

    # Build patch map: filename -> set of added line numbers
    patch_map: dict[str, set[int]] = {}
    supported_files: list[str] = []
    for f in pr_files:
        fname = f["filename"]
        if _should_skip(fname):
            continue
        supported_files.append(fname)
        if f.get("patch"):
            patch_map[fname] = parse_patch_added_lines(f["patch"])

    print(f"PR files: {len(pr_files)}, Supported: {len(supported_files)}", file=sys.stderr)

    if not supported_files:
        body = _build_markdown({
            "total_files": 0, "total_issues": 0, "highest_severity": "none",
            "total_risk_score": 0, "final_verdict": "APPROVE",
            "all_issues": [],
        })
        existing = _find_existing_comment(owner, repo, pr_number, token)
        if existing:
            _update_comment(existing, body, token)
        else:
            _create_comment(owner, repo, pr_number, body, token)
        return

    # Review each file
    file_results = []
    for fp in supported_files:
        code = _read_file_content(fp)
        if code is None:
            continue
        print(f"  Reviewing {fp}...", file=sys.stderr)
        result = _review_file(fp, code)
        file_results.append(result)

    # Map issues to commentable lines
    existing_fingerprints = _fetch_existing_inline_fingerprints(owner, repo, pr_number, token)

    inline_comments: list[dict] = []
    inline_posted_count = 0

    for res in file_results:
        for issue in res.get("issues", []):
            fpath = issue.get("file", "unknown")
            lnum = issue.get("line")
            cwe = issue.get("cwe_id", "")
            added_lines = patch_map.get(fpath)

            if added_lines is not None and lnum and lnum in added_lines:
                if inline_posted_count >= MAX_INLINE_COMMENTS:
                    issue["inline_status"] = "skipped-cap"
                    continue
                fingerprint = _build_inline_fingerprint(fpath, lnum, cwe)
                if fingerprint in existing_fingerprints:
                    issue["inline_status"] = "duplicate"
                    continue
                issue["inline_status"] = "commentable"
                inline_comments.append({
                    "path": fpath,
                    "line": lnum,
                    "body": _build_inline_comment_body(issue),
                })
                inline_posted_count += 1
            else:
                issue["inline_status"] = "not-commentable"

    summary = _aggregate_results(file_results)
    markdown = _build_markdown(summary, inline_posted=inline_posted_count if inline_posted_count > 0 else None)

    # Post summary comment
    existing = _find_existing_comment(owner, repo, pr_number, token)
    if existing:
        print(f"Updating existing comment #{existing}", file=sys.stderr)
        _update_comment(existing, markdown, token)
    else:
        print("Creating new comment", file=sys.stderr)
        _create_comment(owner, repo, pr_number, markdown, token)

    # Post inline comments
    if inline_comments:
        print(f"Posting {len(inline_comments)} inline comment(s)...", file=sys.stderr)
        _post_inline_review(owner, repo, pr_number, token, inline_comments, markdown)


# --- Main ---

def main():
    _load_config()

    # Quick self-test of patch parser
    try:
        _parse_patch_check()
    except AssertionError as e:
        print(f"Patch parser self-test failed: {e}", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]

    save_to_db = False
    if "--save" in args:
        args.remove("--save")
        save_to_db = True

    if "--dry-run" in args:
        idx = args.index("--dry-run")
        args.pop(idx)

        explicit = None
        if args and args[0] == "--files":
            args.pop(0)
            explicit = args

        if explicit:
            markdown = _dry_run_report(explicit_files=explicit)
            file_results = []
            for fp in explicit:
                code = _read_file_content(fp)
                if code:
                    file_results.append(review_code(code=code, file_path=fp, use_rag=False))
        else:
            changed = _get_changed_files_from_git("HEAD~1", "HEAD")
            supported = []
            skipped: list[str] = []
            for f in changed:
                (supported if not _should_skip(f) else skipped).append(f)
            if skipped:
                print("  Skipped files:", file=sys.stderr)
                for sf in skipped:
                    print(f"    - {sf}", file=sys.stderr)
            if not supported:
                print("No supported changed files detected. Use --files for explicit paths.", file=sys.stderr)
                return
            sources = list(map(str, supported))
            markdown = _dry_run_report(explicit_files=sources)
            file_results = []
            for fp in sources:
                code = _read_file_content(fp)
                if code:
                    file_results.append(review_code(code=code, file_path=fp, use_rag=False))

        if save_to_db and _HAS_DB:
            init_db()
            for res in file_results:
                saved = save_review(
                    review_result=res,
                    source="github-action-dry-run",
                    file_path=res.get("issues", [{}])[0].get("file") if res.get("issues") else None,
                )
                print(f"  Saved review {saved['review_id']}", file=sys.stderr)

        print(markdown)
        return

    _ci_run()


if __name__ == "__main__":
    main()
