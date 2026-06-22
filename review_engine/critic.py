from __future__ import annotations
import re
from typing import Optional

RULES: list[dict] = [
    {
        "id": "eval-call",
        "title": "Code Injection via eval()",
        "cwe_id": "CWE-94",
        "severity": "critical",
        "patterns": [
            r"\beval\s*\(",
            r"\bexec\s*\(",
            r"\bnew\s+Function\s*\(",
        ],
        "explanation": (
            "Using eval(), exec(), or new Function() executes arbitrary code from strings. "
            "An attacker who controls any part of the evaluated string can execute arbitrary commands, "
            "leading to full compromise of the application."
        ),
    },
    {
        "id": "sql-concat",
        "title": "SQL Injection via String Concatenation",
        "cwe_id": "CWE-89",
        "severity": "critical",
        "patterns": [
            r"(?:SELECT|INSERT|UPDATE|DELETE)\s+.*?\+\s*(?:request|req\.|input|params)",
            r"execute\s*\(\s*['\"].*?['\"]\s*\+",
            r"query\s*\(\s*['\"].*?['\"]\s*\+",
            r"cursor\.execute\s*\(\s*['\"].*?['\"]\s*\+",
            r"(?:SELECT|INSERT|UPDATE|DELETE).*?f['\"].*?\{.*?\}",
        ],
        "explanation": (
            "Building SQL queries with string concatenation or interpolation using user input "
            "allows an attacker to alter the query structure, potentially accessing or destroying "
            "data they should not be able to."
        ),
    },
    {
        "id": "subprocess-shell",
        "title": "OS Command Injection via subprocess/shell",
        "cwe_id": "CWE-78",
        "severity": "critical",
        "patterns": [
            r"subprocess\.(?:call|Popen|run|check_output)\s*\(.*?shell\s*=\s*True",
            r"os\.system\s*\(",
            r"os\.popen\s*\(",
            r"exec\s*\(.*?['\"].*?\+",
            r"Runtime\.getRuntime\(\)\.exec\s*\(",
        ],
        "explanation": (
            "Executing shell commands with user-influenced arguments can allow an attacker "
            "to run arbitrary OS commands. Prefer safe APIs that do not invoke a shell."
        ),
    },
    {
        "id": "weak-hash",
        "title": "Weak Hashing Algorithm",
        "cwe_id": "CWE-328",
        "severity": "high",
        "patterns": [
            r"\bmd5\s*\(",
            r"\bsha1\s*\(",
            r"MessageDigest\.getInstance\s*\(\s*['\"]MD5['\"]",
            r"MessageDigest\.getInstance\s*\(\s*['\"]SHA-1['\"]",
        ],
        "explanation": (
            "MD5 and SHA-1 are cryptographically broken and vulnerable to collision attacks. "
            "Use a modern hashing algorithm like SHA-256 or SHA-3 for integrity checks, "
            "or bcrypt/argon2 for password storage."
        ),
    },
    {
        "id": "hardcoded-secret",
        "title": "Hardcoded Credential / Secret",
        "cwe_id": "CWE-798",
        "severity": "critical",
        "patterns": [
            r"(?:api_key|apikey|api\.key|api_secret|secret_key)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}",
            r"(?:password|passwd|pwd)\s*[:=]\s*['\"][A-Za-z0-9_!@#$%^&*()]{8,}",
            r"(?:token)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{20,}",
        ],
        "explanation": (
            "Hardcoded credentials, API keys, or secrets in source code are exposed to anyone "
            "with access to the repository. Use environment variables or a secrets manager instead."
        ),
    },
    {
        "id": "unsafe-path",
        "title": "Path Traversal via Unsafe File Access",
        "cwe_id": "CWE-22",
        "severity": "high",
        "patterns": [
            r"file\s*=\s*new\s+File\s*\(\s*(?:request|req\.|params|\.\.\.)",
            r"(?:open|read|write|delete)\s*\(\s*(?:request|req\.|params|\.\.\.)",
            r"Path\.join\s*\(.*?(?:request|req\.|params|\.\.\.)",
        ],
        "explanation": (
            "Using user-supplied input to construct file paths without validation can allow an "
            "attacker to read or write files outside the intended directory."
        ),
    },
    {
        "id": "unsafe-url-fetch",
        "title": "Server-Side Request Forgery (SSRF)",
        "cwe_id": "CWE-918",
        "severity": "high",
        "patterns": [
            r"requests?\.(?:get|post|put|delete)\s*\(\s*(?:request|req\.|params|\.\.\.)",
            r"urllib\.(?:request|urlopen)\s*\(.*?(?:request|req\.|params|\.\.\.)",
            r"HttpURLConnection\s*\(.*?(?:request|req\.|params|\.\.\.)",
        ],
        "explanation": (
            "Making HTTP requests to URLs constructed from user input can allow an attacker "
            "to probe internal network resources."
        ),
    },
]


MAX_FINDINGS_PER_RULE = 3
MAX_TOTAL_FINDINGS = 20


def _dedup_key(issue: dict) -> str:
    return f"{issue.get('file')}|{issue.get('line')}|{issue['cwe_id']}|{issue['code_snippet']}"


def detect_issues(code: str, file_path: Optional[str] = None) -> list[dict]:
    issues: list[dict] = []
    rule_counts: dict[str, int] = {}
    seen_dedup: set[str] = set()
    lines = code.splitlines(keepends=False)

    for line_no, line in enumerate(lines, start=1):
        if len(issues) >= MAX_TOTAL_FINDINGS:
            break

        stripped = line.strip()
        if not stripped:
            continue

        for rule in RULES:
            if len(issues) >= MAX_TOTAL_FINDINGS:
                break
            if rule_counts.get(rule["id"], 0) >= MAX_FINDINGS_PER_RULE:
                continue

            for pattern in rule["patterns"]:
                if re.search(pattern, stripped, re.IGNORECASE):
                    candidate = {
                        "file": file_path,
                        "line": line_no,
                        "start_line": line_no,
                        "end_line": line_no,
                        "code_snippet": stripped,
                        "cwe_id": rule["cwe_id"],
                        "severity": rule["severity"],
                        "title": rule["title"],
                        "explanation": rule["explanation"],
                        "suggested_fix": "",
                        "retrieved_context": [],
                    }
                    dk = _dedup_key(candidate)
                    if dk in seen_dedup:
                        continue
                    seen_dedup.add(dk)
                    rule_counts[rule["id"]] = rule_counts.get(rule["id"], 0) + 1
                    issues.append(candidate)
                    break

    return issues
