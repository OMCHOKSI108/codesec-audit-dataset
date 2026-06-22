from __future__ import annotations
from typing import Any

FIX_TEMPLATES: dict[str, str] = {
    "CWE-94": (
        "Replace eval()/exec() with a safe alternative:\n"
        "- For JSON: use `JSON.parse()` instead of `eval()`.\n"
        "- For arithmetic: use a proper expression parser like `expr-eval`.\n"
        "- For dynamic property access: use bracket notation with an allowlist.\n"
        "- Never trust user input as executable code."
    ),
    "CWE-89": (
        "Use parameterized queries (prepared statements) instead of string concatenation:\n"
        "- SQLite: `cursor.execute(\"SELECT * FROM users WHERE id = ?\", (user_id,))`\n"
        "- Node.js: `db.execute(\"SELECT * FROM users WHERE id = ?\", [userId])`\n"
        "- Python: `cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))`\n"
        "- Java: `PreparedStatement ps = conn.prepareStatement(\"SELECT * FROM users WHERE id = ?\");`"
    ),
    "CWE-78": (
        "Avoid shell=True and use safe argument-passing APIs:\n"
        "- Python: `subprocess.run([\"ls\", \"-l\", filepath], capture_output=True)` instead of `subprocess.run(f\"ls -l {filepath}\", shell=True)`\n"
        "- Java: Use `ProcessBuilder` with a list of arguments instead of `Runtime.exec(String)`.\n"
        "- Validate and sanitize all user input before passing to any command execution function."
    ),
    "CWE-328": (
        "Replace weak hashing algorithms with cryptographically strong alternatives:\n"
        "- For password storage: use `bcrypt`, `argon2`, or `PBKDF2`.\n"
        "- For integrity checks: use SHA-256 or SHA-3.\n"
        "- Never use MD5 or SHA-1 in security-sensitive contexts."
    ),
    "CWE-798": (
        "Move secrets to environment variables or a secrets manager:\n"
        "- Set `export SECRET_KEY=your_key` in the environment (not in code).\n"
        "- Read with `os.environ.get(\"SECRET_KEY\")`.\n"
        "- For production, use a secrets manager like HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault."
    ),
    "CWE-22": (
        "Validate and sanitize file paths:\n"
        "- Resolve the absolute path and verify it starts with an allowed base directory.\n"
        "- Use `os.path.realpath()` or `Path.resolve()` before using the path.\n"
        "- Reject paths containing `..` or other traversal sequences.\n"
        "- Use a pre-defined allowlist of permitted filenames where possible."
    ),
    "CWE-918": (
        "Validate and restrict outbound URLs:\n"
        "- Use an allowlist of permitted hostnames/domains.\n"
        "- Validate that the URL starts with `https://` and matches expected patterns.\n"
        "- Block requests to private IP ranges (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16).\n"
        "- Use a dedicated HTTP client with restricted redirect following."
    ),
}

GENERAL_FIX = (
    "Review the code to ensure no user input reaches sensitive functions without "
    "proper validation, sanitization, or escaping."
)


def generate_fix(issue: dict, contexts: list[dict] | None = None) -> str:
    cwe_id = issue.get("cwe_id", "")
    fix = FIX_TEMPLATES.get(cwe_id)

    if fix:
        return fix

    if contexts:
        for ctx in contexts:
            if ctx.get("cwe_id") == cwe_id and ctx.get("content", "").strip():
                snippet = ctx["content"].strip()[:300]
                return f"Refer to OWASP guidance:\n{snippet}..."

    return GENERAL_FIX
