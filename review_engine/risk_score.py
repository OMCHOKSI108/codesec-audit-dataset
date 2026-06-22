from __future__ import annotations

SEVERITY_POINTS = {
    "critical": 35,
    "high": 25,
    "medium": 15,
    "low": 5,
}


def calculate_risk_score(issues: list[dict]) -> int:
    total = 0
    for issue in issues:
        sev = issue.get("severity", "medium")
        total += SEVERITY_POINTS.get(sev, 0)
    return min(total, 100)


def decide_verdict(risk_score: int) -> str:
    if risk_score >= 60:
        return "REQUEST_CHANGES"
    if risk_score >= 20:
        return "WARNING"
    return "APPROVE"
