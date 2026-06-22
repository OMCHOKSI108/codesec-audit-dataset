import json
import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from review_engine.pipeline import review_code as engine_review
from review_store import init_db, save_review, get_review, list_reviews, get_stats, get_db_path

INDEX_DIR = "data/final/rag_index"
TOP_K = 3
START_TIME = time.time()
ENABLE_RAG = os.getenv("CODESEC_ENABLE_RAG", "true").lower() in ("1", "true", "yes")

app = FastAPI(
    title="CodeSecAudit API",
    description="Review source code for security issues using OWASP cheat sheet RAG",
    version="0.6.0",
)

_retriever = None


def _get_retriever():
    from review_engine.retriever import RAGRetriever

    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever(index_path=INDEX_DIR)
    return _retriever


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    uptime_seconds = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    from review_engine.critic import RULES
    return {
        "app": "CodeSecAudit AI API",
        "version": "0.6.0",
        "description": "RAG-powered security code review engine",
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "uptime_seconds": uptime_seconds,
        "start_time_iso": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(START_TIME)
        ),
        "configuration": {
            "rag_index_path": INDEX_DIR,
            "top_k_default": TOP_K,
            "database": str(get_db_path()),
            "review_rules": len(RULES),
            "rag_index_loaded": _retriever is not None,
        },
    }


class ReviewRequest(BaseModel):
    code: str = Field(min_length=1, description="Source code to analyze")
    file_path: str | None = Field(default=None, description="Source file path")
    top_k: int = Field(default=TOP_K, ge=1, le=20)
    use_rag: bool = Field(default=ENABLE_RAG)


class ReviewResponse(BaseModel):
    summary: str
    risk_score: int
    verdict: str
    issues: list[dict]
    metadata: dict


class HealthResponse(BaseModel):
    status: str
    engine_version: str
    collection: str
    documents: int
    uptime_seconds: int = 0


class ReviewCodeRequest(BaseModel):
    code: str = Field(min_length=1, description="Source code to analyze")
    file_path: Optional[str] = Field(default=None, description="Source file path")
    source: str = Field(default="api", description="Origin of the review (api, cli, github-action)")
    repo: Optional[str] = Field(default=None, description="GitHub repository full name")
    pr_number: Optional[int] = Field(default=None, description="Pull request number")
    commit_sha: Optional[str] = Field(default=None, description="Commit SHA")
    top_k: int = Field(default=TOP_K, ge=1, le=20)
    use_rag: bool = Field(default=ENABLE_RAG)


class ReviewCodeResponse(BaseModel):
    review_id: str
    summary: str
    risk_score: int
    verdict: str
    issues: list[dict]
    metadata: dict
    created_at: str


@app.get("/health", response_model=HealthResponse)
def health():
    try:
        r = _get_retriever()
        doc_count = r.document_count
    except Exception:
        doc_count = 0

    uptime_seconds = int(time.time() - START_TIME)
    return HealthResponse(
        status="ok",
        engine_version="0.6.0",
        collection="owasp_rag",
        documents=doc_count,
        uptime_seconds=uptime_seconds,
    )


@app.post("/review", response_model=ReviewResponse)
def review(req: ReviewRequest):
    result = engine_review(
        code=req.code,
        file_path=req.file_path,
        use_rag=req.use_rag,
        top_k=req.top_k,
    )

    return ReviewResponse(
        summary=result["summary"],
        risk_score=result["risk_score"],
        verdict=result["verdict"],
        issues=[i.model_dump() if hasattr(i, "model_dump") else i for i in result["issues"]],
        metadata=result["metadata"],
    )


@app.post("/review/code", response_model=ReviewCodeResponse)
def review_code(req: ReviewCodeRequest):
    result = engine_review(
        code=req.code,
        file_path=req.file_path,
        use_rag=req.use_rag,
        top_k=req.top_k,
    )

    saved = save_review(
        review_result=result,
        source=req.source,
        repo=req.repo,
        pr_number=req.pr_number,
        commit_sha=req.commit_sha,
        file_path=req.file_path,
    )

    return ReviewCodeResponse(
        review_id=saved["review_id"],
        summary=saved["summary"],
        risk_score=saved["risk_score"],
        verdict=saved["verdict"],
        issues=saved["issues"],
        metadata=saved["metadata"],
        created_at=saved["created_at"],
    )


@app.get("/reviews")
def list_reviews_endpoint(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return list_reviews(limit=limit, offset=offset)


@app.get("/reviews/{review_id}")
def get_review_endpoint(review_id: str):
    record = get_review(review_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return record


@app.get("/stats")
def stats_endpoint():
    return get_stats()
