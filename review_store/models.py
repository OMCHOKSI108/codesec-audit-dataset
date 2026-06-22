from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class ReviewRecordCreate(BaseModel):
    source: str = "api"
    repo: Optional[str] = None
    pr_number: Optional[int] = None
    commit_sha: Optional[str] = None
    file_path: Optional[str] = None


class ReviewRecord(BaseModel):
    id: str
    source: str
    repo: Optional[str] = None
    pr_number: Optional[int] = None
    commit_sha: Optional[str] = None
    file_path: Optional[str] = None
    risk_score: int
    verdict: str
    summary: str
    issues_json: str
    metadata_json: str
    created_at: str


class ReviewListItem(BaseModel):
    id: str
    source: str
    repo: Optional[str] = None
    pr_number: Optional[int] = None
    risk_score: int
    verdict: str
    summary: str
    created_at: str


class ReviewStats(BaseModel):
    total_reviews: int = 0
    verdict_counts: dict[str, int] = Field(default_factory=lambda: {
        "APPROVE": 0, "WARNING": 0, "REQUEST_CHANGES": 0,
    })
    average_risk_score: float = 0.0
    high_risk_reviews: int = 0
    total_issues: int = 0
