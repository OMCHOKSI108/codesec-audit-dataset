import csv
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data/raw/owasp_benchmark_python"
TESTCODE_DIR = RAW_DIR / "testcode"

OUT_DIR = ROOT / "data/processed/owasp_benchmark_python"
META_DIR = ROOT / "data/final/metadata"

OUT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

OUT_PATH = OUT_DIR / "owasp_python_review.jsonl"
SUMMARY_PATH = META_DIR / "owasp_python_normalization_summary.json"


CWE_NAME_MAP = {
    "CWE-22": "Path Traversal",
    "CWE-23": "Relative Path Traversal",
    "CWE-36": "Absolute Path Traversal",
    "CWE-78": "OS Command Injection",
    "CWE-79": "Cross-Site Scripting",
    "CWE-80": "Cross-Site Scripting",
    "CWE-83": "Cross-Site Scripting",
    "CWE-89": "SQL Injection",
    "CWE-90": "LDAP Injection",
    "CWE-94": "Code Injection",
    "CWE-327": "Broken or Risky Cryptographic Algorithm",
    "CWE-328": "Weak Hashing Algorithm",
    "CWE-330": "Use of Insufficiently Random Values",
    "CWE-352": "Cross-Site Request Forgery",
    "CWE-434": "Unrestricted File Upload",
    "CWE-601": "Open Redirect",
    "CWE-614": "Sensitive Cookie Without Secure Flag",
    "CWE-918": "Server-Side Request Forgery"
}


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def extract_digits(text):
    text = normalize_text(text)
    nums = re.findall(r"\d+", text)
    return nums[-1] if nums else ""


def extract_cwe(text):
    text = normalize_text(text)
    match = re.search(r"CWE[-_ ]?(\d+)", text, flags=re.IGNORECASE)
    if match:
        return f"CWE-{match.group(1)}"
    return ""


def infer_cwe_from_text(text):
    text = normalize_text(text).lower()

    keyword_map = [
        ("sql", "CWE-89"),
        ("path", "CWE-22"),
        ("traversal", "CWE-22"),
        ("command", "CWE-78"),
        ("xss", "CWE-80"),
        ("cross site scripting", "CWE-80"),
        ("ldap", "CWE-90"),
        ("crypto", "CWE-327"),
        ("hash", "CWE-328"),
        ("redirect", "CWE-601"),
        ("upload", "CWE-434"),
        ("csrf", "CWE-352"),
        ("ssrf", "CWE-918"),
        ("random", "CWE-330"),
        ("cookie", "CWE-614"),
    ]

    for key, cwe in keyword_map:
        if key in text:
            return cwe

    return ""


def infer_owasp_category(cwe_id):
    mapping = {
        "CWE-22": "A01: Broken Access Control",
        "CWE-23": "A01: Broken Access Control",
        "CWE-36": "A01: Broken Access Control",
        "CWE-78": "A03: Injection",
        "CWE-79": "A03: Injection",
        "CWE-80": "A03: Injection",
        "CWE-83": "A03: Injection",
        "CWE-89": "A03: Injection",
        "CWE-90": "A03: Injection",
        "CWE-94": "A03: Injection",
        "CWE-327": "A02: Cryptographic Failures",
        "CWE-328": "A02: Cryptographic Failures",
        "CWE-330": "A02: Cryptographic Failures",
        "CWE-352": "A01: Broken Access Control",
        "CWE-434": "A05: Security Misconfiguration",
        "CWE-601": "A01: Broken Access Control",
        "CWE-614": "A05: Security Misconfiguration",
        "CWE-918": "A10: Server-Side Request Forgery",
    }
    return mapping.get(cwe_id, "unknown")


def infer_severity(cwe_id):
    high = {"CWE-89", "CWE-78", "CWE-94", "CWE-918", "CWE-434"}
    medium = {"CWE-22", "CWE-23", "CWE-36", "CWE-80", "CWE-79", "CWE-90", "CWE-327", "CWE-328", "CWE-352", "CWE-601"}

    if cwe_id in high:
        return "high"
    if cwe_id in medium:
        return "medium"
    return "unknown"


def truthy_value(value):
    value = normalize_text(value).lower()

    if value in {"true", "yes", "1", "vulnerable", "bad", "fail", "positive"}:
        return True

    if value in {"false", "no", "0", "clean", "safe", "good", "pass", "negative"}:
        return False

    return None


def find_metadata_csvs():
    csvs = []
    for p in RAW_DIR.rglob("*.csv"):
        name = p.name.lower()
        rel = str(p.relative_to(RAW_DIR)).lower()

        if any(key in name or key in rel for key in [
            "expected",
            "benchmark",
            "test",
            "result",
            "score",
            "truth"
        ]):
            csvs.append(p)

    return sorted(csvs)


def build_label_map():
    label_map = {}
    csv_files = find_metadata_csvs()

    for csv_path in csv_files:
        try:
            with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames:
                    continue

                columns = [c for c in reader.fieldnames if c]

                for row in reader:
                    combined = " ".join(normalize_text(v) for v in row.values())

                    id_candidates = []
                    for col in columns:
                        col_lower = col.lower()
                        value = normalize_text(row.get(col))

                        if any(k in col_lower for k in ["test", "case", "file", "name", "id"]):
                            digits = extract_digits(value)
                            if digits:
                                id_candidates.append(digits)

                    if not id_candidates:
                        digits = extract_digits(combined)
                        if digits:
                            id_candidates.append(digits)

                    if not id_candidates:
                        continue

                    cwe_id = ""
                    vulnerability_name = ""

                    for col in columns:
                        col_lower = col.lower()
                        value = normalize_text(row.get(col))

                        if "cwe" in col_lower:
                            cwe_id = extract_cwe(value) or (f"CWE-{value}" if value.isdigit() else "") or infer_cwe_from_text(value)

                        if any(k in col_lower for k in ["category", "vulnerability", "weakness", "test type"]):
                            vulnerability_name = value

                    if not cwe_id:
                        cwe_id = extract_cwe(combined) or infer_cwe_from_text(combined)

                    if not vulnerability_name:
                        vulnerability_name = CWE_NAME_MAP.get(cwe_id, "unknown")

                    is_vulnerable = None

                    for col in columns:
                        col_lower = col.lower()
                        value = row.get(col)

                        if any(k in col_lower for k in [
                            "real",
                            "expected",
                            "vulnerable",
                            "true",
                            "result",
                            "answer",
                            "label"
                        ]):
                            maybe = truthy_value(value)
                            if maybe is not None:
                                is_vulnerable = maybe
                                break

                    if is_vulnerable is None:
                        is_vulnerable = True

                    for case_id in id_candidates:
                        label_map[case_id] = {
                            "cwe_id": cwe_id or "unknown",
                            "vulnerability_name": vulnerability_name or CWE_NAME_MAP.get(cwe_id, "unknown"),
                            "is_vulnerable": is_vulnerable,
                            "label_source": str(csv_path.relative_to(ROOT)),
                            "raw_metadata": row
                        }

        except Exception as exc:
            print(f"[WARN] Could not parse CSV {csv_path}: {exc}")

    return label_map, csv_files


def read_code(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def normalize_file(py_path, index, label_map):
    rel_path = py_path.relative_to(RAW_DIR)
    filename = py_path.name
    stem = py_path.stem

    case_digits = extract_digits(stem) or extract_digits(filename)
    labels = label_map.get(case_digits, {})

    code = read_code(py_path)

    cwe_id = labels.get("cwe_id") or infer_cwe_from_text(str(rel_path) + " " + code[:500])
    if not cwe_id:
        cwe_id = "unknown"

    vulnerability_name = labels.get("vulnerability_name") or CWE_NAME_MAP.get(cwe_id, "unknown")
    is_vulnerable = labels.get("is_vulnerable", True)

    return {
        "id": f"owasp_python_{index:06d}",
        "source_name": "OWASP Benchmark Python",
        "source_type": "public_dataset",
        "source_split": "processed",
        "original_id": case_digits or stem,
        "language": "python",
        "framework": "generic",
        "task": "security_review",
        "cwe_id": cwe_id,
        "owasp_category": infer_owasp_category(cwe_id),
        "severity": infer_severity(cwe_id),
        "is_vulnerable": bool(is_vulnerable),
        "vulnerability_name": vulnerability_name,
        "input_code": code,
        "fixed_code": "",
        "explanation": (
            "This example was normalized from OWASP Benchmark Python. "
            "It is intended for security review and vulnerability detection. "
            "A secure repair is not included in this source-specific normalized record."
        ),
        "secure_pattern": "",
        "tags": [
            "owasp",
            "benchmark-python",
            "python",
            cwe_id.lower() if cwe_id != "unknown" else "unknown-cwe"
        ],
        "metadata": {
            "raw_path": str(rel_path),
            "label_source": labels.get("label_source", ""),
            "normalized_at": datetime.utcnow().isoformat() + "Z"
        }
    }


def main():
    print("Normalizing OWASP Benchmark Python")
    print("=" * 70)

    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Missing raw directory: {RAW_DIR}")

    if not TESTCODE_DIR.exists():
        raise FileNotFoundError(f"Missing testcode directory: {TESTCODE_DIR}")

    label_map, csv_files = build_label_map()

    print(f"Metadata CSV files found: {len(csv_files)}")
    for p in csv_files:
        print(f"- {p.relative_to(RAW_DIR)}")

    print(f"Label map entries created: {len(label_map)}")

    py_files = sorted(TESTCODE_DIR.rglob("*.py"))
    print(f"Python files found in testcode/: {len(py_files)}")

    total = 0
    vulnerable = 0
    clean = 0
    cwe_counts = {}

    with OUT_PATH.open("w", encoding="utf-8") as out:
        for index, py_path in enumerate(py_files, start=1):
            record = normalize_file(py_path, index, label_map)

            total += 1

            if record["is_vulnerable"]:
                vulnerable += 1
            else:
                clean += 1

            cwe = record["cwe_id"]
            cwe_counts[cwe] = cwe_counts.get(cwe, 0) + 1

            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "source": "OWASP Benchmark Python",
        "output_path": str(OUT_PATH.relative_to(ROOT)),
        "total_records": total,
        "vulnerable": vulnerable,
        "clean": clean,
        "metadata_csv_files": [str(p.relative_to(ROOT)) for p in csv_files],
        "label_map_entries": len(label_map),
        "cwe_counts": dict(sorted(cwe_counts.items(), key=lambda x: x[0])),
        "normalized_at": datetime.utcnow().isoformat() + "Z"
    }

    with SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=" * 70)
    print(f"Output saved to: {OUT_PATH}")
    print(f"Summary saved to: {SUMMARY_PATH}")
    print(f"Total records: {total}")
    print(f"Vulnerable: {vulnerable}")
    print(f"Clean: {clean}")
    print("Top CWE counts:")
    for cwe, count in sorted(cwe_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"- {cwe}: {count}")


if __name__ == "__main__":
    main()
