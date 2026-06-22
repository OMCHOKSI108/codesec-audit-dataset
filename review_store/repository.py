from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from review_store.db import get_connection
from review_store.models import ReviewRecord, ReviewListItem, ReviewStats


def save_review(
    review_result: dict,
    source: str = "api",
    repo: Optional[str] = None,
    pr_number: Optional[int] = None,
    commit_sha: Optional[str] = None,
    file_path: Optional[str] = None,
) -> dict:
    review_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    issues = review_result.get("issues", [])
    issues_json = json.dumps(issues, default=str)
    metadata = review_result.get("metadata", {})
    metadata_json = json.dumps(metadata, default=str)

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO reviews
                (id, source, repo, pr_number, commit_sha, file_path,
                 risk_score, verdict, summary, issues_json, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                source,
                repo,
                pr_number,
                commit_sha,
                file_path,
                review_result["risk_score"],
                review_result["verdict"],
                review_result["summary"],
                issues_json,
                metadata_json,
                created_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "review_id": review_id,
        "summary": review_result["summary"],
        "risk_score": review_result["risk_score"],
        "verdict": review_result["verdict"],
        "issues": issues,
        "metadata": metadata,
        "created_at": created_at,
    }


def get_review(review_id: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM reviews WHERE id = ?", (review_id,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_record(row)
    finally:
        conn.close()


def list_reviews(limit: int = 50, offset: int = 0) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, source, repo, pr_number, risk_score, verdict, summary, created_at "
            "FROM reviews ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stats() -> dict:
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as cnt FROM reviews").fetchone()["cnt"]

        verdict_rows = conn.execute(
            "SELECT verdict, COUNT(*) as cnt FROM reviews GROUP BY verdict"
        ).fetchall()
        verdict_counts = {"APPROVE": 0, "WARNING": 0, "REQUEST_CHANGES": 0}
        for row in verdict_rows:
            verdict_counts[row["verdict"]] = row["cnt"]

        avg_risk = conn.execute(
            "SELECT COALESCE(AVG(risk_score), 0) as avg FROM reviews"
        ).fetchone()["avg"]

        high_risk = conn.execute(
            "SELECT COUNT(*) as cnt FROM reviews WHERE risk_score >= 60"
        ).fetchone()["cnt"]

        total_issues: int = 0
        total_issue_count = conn.execute(
            "SELECT COALESCE(SUM(json_array_length(issues_json)), 0) FROM reviews"
        ).fetchone()
        if total_issue_count is not None:
            total_issues = total_issue_count[0]

        return {
            "total_reviews": total,
            "verdict_counts": verdict_counts,
            "average_risk_score": round(float(avg_risk), 1),
            "high_risk_reviews": high_risk,
            "total_issues": total_issues,
        }
    finally:
        conn.close()


def _row_to_record(row) -> dict:
    return {
        "id": row["id"],
        "source": row["source"],
        "repo": row["repo"],
        "pr_number": row["pr_number"],
        "commit_sha": row["commit_sha"],
        "file_path": row["file_path"],
        "risk_score": row["risk_score"],
        "verdict": row["verdict"],
        "summary": row["summary"],
        "issues": json.loads(row["issues_json"]),
        "metadata": json.loads(row["metadata_json"]),
        "created_at": row["created_at"],
    }
