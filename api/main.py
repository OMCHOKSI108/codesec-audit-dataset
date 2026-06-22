import hashlib
import hmac
import json
import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
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


# --- GitHub App Webhook ---

@app.post("/webhook/github")
async def github_webhook(request: Request):
    secret = os.environ.get("GITHUB_APP_WEBHOOK_SECRET", "")
    signature = request.headers.get("X-Hub-Signature-256", "")
    event_type = request.headers.get("X-GitHub-Event", "")
    body = await request.body()

    if secret and signature:
        expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    if not event_type or event_type == "ping":
        return {"status": "ok", "event": event_type}

    payload = json.loads(body)
    from review_engine.github_app import handle_event
    result = handle_event(event_type, payload)
    return result


class ManifestRequest(BaseModel):
    manifest: dict


@app.get("/register/github-app")
def register_github_app():
    manifest = {
        "name": "codesec-audit-ai",
        "url": "https://codesec-api.onrender.com",
        "hook_attributes": {
            "url": "https://codesec-api.onrender.com/webhook/github",
            "active": True,
        },
        "redirect_url": "https://codesec-api.onrender.com/register/github-app/callback",
        "public": False,
        "default_permissions": {
            "contents": "read",
            "pull_requests": "write",
            "issues": "write",
            "checks": "write",
        },
        "default_events": ["pull_request", "ping"],
        "description": "Automated OWASP-based security code review.",
    }
    import urllib.parse
    url = f"https://github.com/settings/apps/new?manifest={urllib.parse.quote(json.dumps(manifest))}"
    return {
        "message": "Open this URL in your browser to register the GitHub App",
        "url": url,
    }


@app.get("/register/github-app/callback")
def github_app_callback(code: str = Query(...)):
    import urllib.request
    try:
        req = urllib.request.Request(
            f"https://api.github.com/app-manifests/{code}/conversions",
            method="POST",
            headers={"Accept": "application/vnd.github.v3+json",
                     "User-Agent": "codesec-audit-ai"},
        )
        resp = urllib.request.urlopen(req, timeout=30)
        creds = json.loads(resp.read())
        return {
            "message": "GitHub App registered! Set these as Render env vars:",
            "env_vars": {
                "GITHUB_APP_ID": str(creds["id"]),
                "GITHUB_APP_PRIVATE_KEY": creds["pem"],
                "GITHUB_APP_WEBHOOK_SECRET": creds.get("webhook_secret", ""),
            },
            "app_slug": creds.get("slug", ""),
            "html_url": creds.get("html_url", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
