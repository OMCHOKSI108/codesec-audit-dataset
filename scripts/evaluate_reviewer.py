import json
import sys
from pathlib import Path

from review_engine.pipeline import review_code


GOLDEN_PATH = Path(__file__).resolve().parent.parent / "eval" / "golden_cases.jsonl"


def load_golden_cases(path: Path) -> list[dict]:
    cases = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def evaluate_case(case: dict) -> dict:
    code = case["code"]
    file_path = case.get("file_path")
    result = review_code(code=code, file_path=file_path, use_rag=False)

    actual_issues = len(result["issues"])
    actual_verdict = result["verdict"]
    actual_cwes = sorted(set(i["cwe_id"] for i in result["issues"]))

    expected_issues = case.get("expected_issues")
    expected_min = case.get("expected_min_issues")
    expected_max = case.get("expected_max_issues")
    expected_verdict = case["expected_verdict"]
    expected_cwes = case.get("expected_cwes", [])

    passed = True
    details = []

    if expected_issues is not None and actual_issues != expected_issues:
        if expected_min is not None and expected_max is not None:
            if not (expected_min <= actual_issues <= expected_max):
                passed = False
                details.append(
                    f"issue count {actual_issues} not in [{expected_min}, {expected_max}]"
                )
        else:
            passed = False
            details.append(
                f"expected {expected_issues} issues, got {actual_issues}"
            )
    elif expected_min is not None and expected_max is not None:
        if not (expected_min <= actual_issues <= expected_max):
            passed = False
            details.append(
                f"issue count {actual_issues} not in [{expected_min}, {expected_max}]"
            )

    if actual_verdict != expected_verdict:
        passed = False
        details.append(
            f"expected verdict '{expected_verdict}', got '{actual_verdict}'"
        )

    if set(actual_cwes) != set(expected_cwes):
        passed = False
        details.append(
            f"expected CWEs {set(expected_cwes)}, got {set(actual_cwes)}"
        )

    return {
        "id": case["id"],
        "description": case.get("description", ""),
        "passed": passed,
        "details": details,
        "actual_issues": actual_issues,
        "actual_verdict": actual_verdict,
        "actual_cwes": actual_cwes,
        "expected_cwes": expected_cwes,
        "risk_score": result["risk_score"],
    }


def print_report(results: list[dict]):
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed

    print("=" * 72)
    print("  CodeSecAudit AI — Evaluation Report")
    print("=" * 72)
    print(f"\n  Golden cases : {len(results)}")
    print(f"  Passed       : {passed}")
    print(f"  Failed       : {failed}")
    if failed:
        print(f"  Pass rate    : {passed / len(results) * 100:.1f}%")
    print()

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['id']}: {r['description']}")
        if not r["passed"]:
            for d in r["details"]:
                print(f"        {d}")
        print(
            f"        issues={r['actual_issues']}, verdict={r['actual_verdict']}, "
            f"cwes={r['actual_cwes']}"
        )
        print()

    print("=" * 72)

    if failed:
        sys.exit(1)


def main():
    cases = load_golden_cases(GOLDEN_PATH)
    results = [evaluate_case(case) for case in cases]
    print_report(results)


if __name__ == "__main__":
    main()
