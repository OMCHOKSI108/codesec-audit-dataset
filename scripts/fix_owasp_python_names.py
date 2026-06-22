import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

IN_PATH = ROOT / "data/processed/owasp_benchmark_python/owasp_python_review.jsonl"
BACKUP_PATH = ROOT / "data/processed/owasp_benchmark_python/owasp_python_review.before_name_fix.jsonl"
OUT_PATH = ROOT / "data/processed/owasp_benchmark_python/owasp_python_review.jsonl"

SUMMARY_PATH = ROOT / "data/final/metadata/owasp_python_name_fix_summary.json"

CWE_NAME_MAP = {
    "CWE-22": "Path Traversal",
    "CWE-78": "OS Command Injection",
    "CWE-79": "Cross-Site Scripting",
    "CWE-89": "SQL Injection",
    "CWE-90": "LDAP Injection",
    "CWE-94": "Code Injection",
    "CWE-328": "Weak Hashing Algorithm",
    "CWE-330": "Use of Insufficiently Random Values",
    "CWE-501": "Trust Boundary Violation",
    "CWE-502": "Deserialization of Untrusted Data",
    "CWE-601": "Open Redirect",
    "CWE-611": "XML External Entity Injection",
    "CWE-614": "Sensitive Cookie Without Secure Flag",
    "CWE-643": "XPath Injection",
}

OWASP_CATEGORY_MAP = {
    "CWE-22": "A01: Broken Access Control",
    "CWE-78": "A03: Injection",
    "CWE-79": "A03: Injection",
    "CWE-89": "A03: Injection",
    "CWE-90": "A03: Injection",
    "CWE-94": "A03: Injection",
    "CWE-328": "A02: Cryptographic Failures",
    "CWE-330": "A02: Cryptographic Failures",
    "CWE-501": "A01: Broken Access Control",
    "CWE-502": "A08: Software and Data Integrity Failures",
    "CWE-601": "A01: Broken Access Control",
    "CWE-611": "A05: Security Misconfiguration",
    "CWE-614": "A05: Security Misconfiguration",
    "CWE-643": "A03: Injection",
}

SEVERITY_MAP = {
    "CWE-22": "medium",
    "CWE-78": "high",
    "CWE-79": "medium",
    "CWE-89": "high",
    "CWE-90": "high",
    "CWE-94": "critical",
    "CWE-328": "medium",
    "CWE-330": "medium",
    "CWE-501": "medium",
    "CWE-502": "high",
    "CWE-601": "medium",
    "CWE-611": "high",
    "CWE-614": "medium",
    "CWE-643": "high",
}


def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Missing file: {IN_PATH}")

    original_text = IN_PATH.read_text(encoding="utf-8")
    BACKUP_PATH.write_text(original_text, encoding="utf-8")

    total = 0
    fixed_names = 0
    fixed_categories = 0
    fixed_severity = 0
    unknown_cwe = 0

    records = []

    with BACKUP_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)
            total += 1

            cwe_id = record.get("cwe_id", "unknown")

            old_name = str(record.get("vulnerability_name", "")).strip().lower()
            if old_name in {"true", "false", "", "unknown"}:
                record["vulnerability_name"] = CWE_NAME_MAP.get(cwe_id, "Unknown Vulnerability")
                fixed_names += 1

            old_category = str(record.get("owasp_category", "")).strip().lower()
            if old_category in {"", "unknown"}:
                record["owasp_category"] = OWASP_CATEGORY_MAP.get(cwe_id, "unknown")
                fixed_categories += 1

            old_severity = str(record.get("severity", "")).strip().lower()
            if old_severity in {"", "unknown"}:
                record["severity"] = SEVERITY_MAP.get(cwe_id, "unknown")
                fixed_severity += 1

            if cwe_id == "unknown":
                unknown_cwe += 1

            metadata = record.setdefault("metadata", {})
            metadata["name_fixed_at"] = datetime.utcnow().isoformat() + "Z"

            records.append(record)

    with OUT_PATH.open("w", encoding="utf-8") as out:
        for record in records:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "input_path": str(IN_PATH.relative_to(ROOT)),
        "backup_path": str(BACKUP_PATH.relative_to(ROOT)),
        "output_path": str(OUT_PATH.relative_to(ROOT)),
        "total_records": total,
        "fixed_vulnerability_names": fixed_names,
        "fixed_owasp_categories": fixed_categories,
        "fixed_severity_values": fixed_severity,
        "unknown_cwe_count": unknown_cwe,
        "fixed_at": datetime.utcnow().isoformat() + "Z",
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("OWASP Python vulnerability name fix complete")
    print("=" * 70)
    print(f"Total records: {total}")
    print(f"Fixed vulnerability names: {fixed_names}")
    print(f"Fixed OWASP categories: {fixed_categories}")
    print(f"Fixed severity values: {fixed_severity}")
    print(f"Unknown CWE count: {unknown_cwe}")
    print(f"Backup saved to: {BACKUP_PATH}")
    print(f"Summary saved to: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
