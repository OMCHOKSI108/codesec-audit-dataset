import logging
import os
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from rag_service.index import DEFAULT_DATASET_REPO, DEFAULT_EMBED_MODEL, RagIndex
from rag_service.schemas import (
    SearchMetadata,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

START_TIME = time.time()

app = FastAPI(
    title="CodeSecAudit RAG Service",
    description="Remote RAG retrieval service for OWASP cheat sheets",
    version="0.6.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

index = RagIndex()
api_key = os.getenv("RAG_API_KEY", "")


def _verify_key(request: Request) -> None:
    if not api_key:
        return
    key = request.headers.get("X-CodeSec-RAG-Key", "")
    if key != api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.on_event("startup")
def startup():
    build_on_start = os.getenv("RAG_BUILD_ON_START", "true").lower() in ("1", "true", "yes")
    if build_on_start:
        logger.info("RAG_BUILD_ON_START=true — loading corpus and building index")
        try:
            n = index.load_corpus()
            logger.info("Loaded %d chunks from dataset", n)
            index.build_index()
            logger.info("Index built successfully (%d chunks, %d embeddings)",
                        index.total_chunks, index.embedding_count)
        except Exception as e:
            logger.error("Failed to build index on startup: %s", e)
    else:
        logger.info("RAG_BUILD_ON_START=false — index not loaded")


@app.get("/")
def root():
    return {
        "service": "CodeSecAudit RAG Service",
        "version": "0.6.0",
        "status": "ok",
        "embedding_model": os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_EMBED_MODEL),
        "dataset_repo": os.getenv("RAG_DATASET_REPO", DEFAULT_DATASET_REPO),
        "total_chunks": index.total_chunks,
        "api_key_protected": bool(api_key),
        "uptime_seconds": int(time.time() - START_TIME),
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "index_loaded": index.is_loaded,
        "total_chunks": index.total_chunks,
        "embedding_count": index.embedding_count,
        "embedding_model": os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_EMBED_MODEL),
        "uptime_seconds": int(time.time() - START_TIME),
    }


@app.post("/rag/search", response_model=SearchResponse)
def search(req: SearchRequest, request: Request):
    _verify_key(request)
    t0 = time.time()
    results = index.search(req.query, top_k=req.top_k)
    elapsed = (time.time() - t0) * 1000

    return SearchResponse(
        query=req.query,
        top_k=req.top_k,
        results=[SearchResultItem(**r) for r in results],
        metadata=SearchMetadata(
            embedding_model=os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_EMBED_MODEL),
            dataset_repo=os.getenv("RAG_DATASET_REPO", DEFAULT_DATASET_REPO),
            total_chunks=index.total_chunks,
            query_time_ms=round(elapsed, 2),
        ),
    )
