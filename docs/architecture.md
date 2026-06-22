# Architecture

## High-Level System Diagram

```mermaid
flowchart TD
    A[GitHub Pull Request] --> B[GitHub Action / Future GitHub App]
    B --> C[Changed Files + Diff Parser]
    C --> D[review_engine Critic]
    D --> E[Remote RAG Service on Hugging Face]
    E --> F[OWASP Secure Coding Guidance]
    D --> G[Fixer + Risk Scoring]
    F --> G
    G --> H[PR Summary Comment]
    G --> I[Inline PR Comments]
    G --> J[FastAPI Review History API]
    J --> K[SQLite MVP / MongoDB SaaS]
    K --> L[Streamlit Dashboard]
    K --> M[Analytics API]
    L --> M
```

## Component Overview

| Component | Language | Role |
|---|---|---|
| `review_engine` | Python | Core: critic, fixer, retriever, risk scorer, pipeline |
| `rag_service` | Python | Standalone FastAPI microservice for RAG (HF Space) |
| `review_store` | Python | SQLite persistence with repository pattern |
| `api` | Python | FastAPI application exposing review + history endpoints |
| `ui` (review) | Python | Streamlit interface for submitting code reviews |
| `ui` (dashboard) | Python | Streamlit interface for analytics and history |
| `scripts/` | Python | CLI, evaluation, deploy, smoke test helpers |
| `.github/workflows/` | YAML | GitHub Action definition |

## Review Pipeline

```mermaid
sequenceDiagram
    participant PR as Pull Request
    participant GA as GitHub Action
    participant RE as review_engine
    participant RS as RAG Service
    participant DB as Review Store
    participant UI as Dashboard

    PR->>GA: opened / synchronize
    GA->>RE: review_code(code, use_rag)
    RE->>RE: critic.scan() → list of issues
    alt RAG mode = remote
        RE->>RS: POST /rag/search (query)
        RS-->>RE: OWASP guidance chunks
    else RAG mode = local
        RE->>RE: RAGRetriever.search()
    end
    RE->>RE: fixer.generate_fixes(issues, guidance)
    RE->>RE: risk_score.compute(issues) → score + verdict
    RE-->>GA: ReviewResult
    GA->>GA: post summary comment
    GA->>GA: post inline comments (max 10)
    GA->>DB: save review record
    DB-->>UI: analytics data
```

## RAG Service Architecture

```mermaid
flowchart LR
    A[Client] --> B[FastAPI /rag/search]
    B --> C{API Key Check}
    C -->|Missing / Invalid| D[401 Unauthorized]
    C -->|Optional / Matching| E[RagIndex]
    E --> F[Corpus JSONL from HF Dataset]
    E --> G[all-MiniLM-L6-v2 Embeddings]
    E --> H[Numpy Cosine Similarity Search]
    H --> I[Top-K Results]
    I --> B
```

The RAG service:
- Loads the corpus from Hugging Face Dataset (`OMCHOKSI108/CodeSecAudit-RAG`) on startup
- Embeds all chunks using `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- Searches via numpy cosine similarity (no heavy DB driver)
- Supports optional `X-CodeSec-RAG-Key` auth header (production: required)
- Returns up to `top_k` results with rank, score, title, CWE ID, and content

### Why a separate service?

RAG dependencies (sentence-transformers, PyTorch) add ~7 GB to the Docker image. By deploying the RAG service as a **separate Hugging Face Space**, the main API and dashboard stay lightweight (~500 MB) and call RAG over HTTP when needed.

## SaaS Future Architecture

```mermaid
flowchart TD
    A[GitHub App Webhook] --> B[API Server - Render]
    B --> C[MongoDB Atlas]
    B --> D[Resend Email]
    B --> E[RAG Service - HF Space]
    C --> F[Users Collection]
    C --> G[Installations Collection]
    C --> H[Reviews Collection]
    C --> I[Usage Events Collection]
    C --> J[Plans Collection]
    C --> K[Email Events Collection]
    F --> L[Dashboard - Streamlit]
    L --> M[GitHub OAuth Login]
    L --> N[Usage Stats + Analytics]
    D --> O[Welcome Email]
    D --> P[Limit Reached Email]
    D --> Q[Usage Guide Email]
```

See [docs/deployment_strategy.md](deployment_strategy.md) and [docs/saas_data_model.md](saas_data_model.md) for full details.

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Rule-based detection (no LLM API) | Zero cost per review, deterministic, no API keys needed |
| Remote RAG via HTTP | Keeps main image ~500 MB; RAG deps live only on HF Space |
| Numpy cosine similarity over ChromaDB | Simpler, no heavy DB driver, 2,833 chunks fit in memory |
| SQLite MVP → MongoDB SaaS | SQLite is zero-config for development; MongoDB for production scale |
| `use_rag=False` in CI | Avoids downloading embedding model on every workflow run |
| Non-blocking CI (exit 0) | Prevents broken builds from false positives |
