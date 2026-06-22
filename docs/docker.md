# Docker Deployment

CodeSecAudit AI ships with a lightweight Docker image (~500 MB) that excludes heavy RAG
dependencies (PyTorch / sentence-transformers / ChromaDB). RAG support is optional and can
be enabled at build time.

## Quick Start (Lightweight Mode — Default)

Build and start all services (API + review UI + dashboard):

```bash
docker compose build
docker compose up -d
```

- API: http://localhost:8003
- Review UI (Streamlit): http://localhost:8501
- Dashboard (Streamlit): http://localhost:8502

This runs the review engine in **rules-only mode** — 7 OWASP detectors (CWE-94, CWE-89,
CWE-78, CWE-328, CWE-798, CWE-22, CWE-918) with no RAG retrieval.

## RAG Mode

To build with RAG support (adds PyTorch ~7 GB image, ~8 min build):

```bash
docker compose -f docker-compose.yml -f docker-compose.rag.yml build
docker compose -f docker-compose.yml -f docker-compose.rag.yml up -d
```

Or build a specific service with RAG:

```bash
INSTALL_RAG=true docker compose build api
```

## Build Args

| ARG           | Default  | Description                                |
|---------------|----------|--------------------------------------------|
| INSTALL_RAG   | `false`  | Install `chromadb` + `sentence-transformers` |

## Environment Variables

| Variable           | Default      | Services          | Description                       |
|--------------------|--------------|-------------------|-----------------------------------|
| `CODESEC_DB_PATH`  | _(internal)_ | api               | Path to SQLite review database    |
| `CODESEC_API_URL`  | localhost    | review-ui, dash   | API endpoint for Streamlit apps   |
| `CODESEC_ENABLE_RAG` | `true`    | api               | Default value for `use_rag` flag  |

## Smoke Test

```bash
./scripts/docker_smoke_test.sh
```

Verifies: health endpoint → review API → review detail → stats → streamlit UI pages.
