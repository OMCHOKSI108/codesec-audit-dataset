from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class RetrievedContext(BaseModel):
    source: str = ""
    title: str = ""
    section: str = ""
    cwe_id: str = ""
    content: str = ""


class ReviewIssue(BaseModel):
    file: Optional[str] = None
    line: Optional[int] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    code_snippet: str = ""
    cwe_id: str = ""
    severity: str = "medium"
    title: str = ""
    explanation: str = ""
    suggested_fix: str = ""
    retrieved_context: list[RetrievedContext] = Field(default_factory=list)


class ReviewResult(BaseModel):
    summary: str = ""
    risk_score: int = 0
    verdict: str = "APPROVE"
    issues: list[ReviewIssue] = Field(default_factory=list)
    metadata: dict = Field(default_factory=lambda: {
        "engine_version": "0.6.0",
        "rag_used": False,
    })


class CodeReviewRequest(BaseModel):
    code: str = Field(min_length=1, description="Source code to analyze")
    file_path: Optional[str] = Field(default=None, description="Source file path")
    top_k: int = Field(default=3, ge=1, le=20, description="Number of RAG contexts")
    use_rag: bool = Field(default=True, description="Enable RAG retrieval")
