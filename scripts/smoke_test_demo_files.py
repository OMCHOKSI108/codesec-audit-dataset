import json
from pathlib import Path
from review_engine.pipeline import review_code

ROOT = Path(__file__).resolve().parents[1]
VULN_PATH = ROOT / "examples/vulnerable_pr_demo.py"
SAFE_PATH = ROOT / "examples/safe_pr_demo.py"


def review_file(filepath: str, label: str):
    code = Path(filepath).read_text(encoding="utf-8")
    result = review_code(code=code, file_path=filepath, use_rag=False)
    issues = result.get("issues", [])
    cwe_list = sorted(set(i["cwe_id"] for i in issues if i["cwe_id"]))
    print(f"\n{'=' * 60}")
    print(f"  {label}: {filepath}")
    print(f"{'=' * 60}")
    print(f"  Issues found: {len(issues)}")
    print(f"  Risk score:   {result['risk_score']}/100")
    print(f"  Verdict:      {result['verdict']}")
    print(f"  CWE types:    {cwe_list if cwe_list else '(none)'}")
    for i, issue in enumerate(issues, 1):
        line = issue.get("line", "?")
        cwe = issue.get("cwe_id", "")
        title = issue.get("title", "")
        snippet = issue.get("code_snippet", "")
        sev = issue.get("severity", "medium")
        print(f"\n  Issue #{i}: {cwe} {title} (line {line}, {sev})")
        print(f"    Snippet: {snippet}")


def main():
    review_file(str(VULN_PATH), "VULNERABLE DEMO")
    review_file(str(SAFE_PATH), "SAFE DEMO")
    print("\nSmoke test complete.")


if __name__ == "__main__":
    main()
