# Changelog

## v0.6.0 (2026-06-22)
- Separated lightweight and RAG dependency groups in `pyproject.toml`
- Made RAG imports lazy in `retriever.py`, `pipeline.py`, and `api/main.py`
- Updated Dockerfile with `ARG INSTALL_RAG=false` — default image excludes PyTorch
- Added `docker-compose.rag.yml` override for RAG-enabled builds
- Added `scripts/check_lightweight_mode.py` verification script
- Added `CODESEC_ENABLE_RAG` env var to API (defaults: true, overridable)
- Updated `docs/docker.md` with lightweight and RAG mode documentation
- Created portfolio-ready `README.md`
- Default Docker image size reduced from ~7 GB to ~500 MB

## v0.5.0 (2026-06-21)
- Docker Compose stack with 3 services (api, review-ui, dashboard)
- Named volume + healthcheck + smoke test script
- Streamlit dashboard with stats, charts, filters, review detail viewer

## v0.4.0 (2026-06-20)
- SQLite review history + FastAPI CRUD endpoints
- `GET /` root page with uptime/config
- `GET /stats` aggregation endpoint

## v0.3.0 (2026-06-19)
- Multi-hit detection (MAX_FINDINGS_PER_RULE=3, MAX_TOTAL_FINDINGS=20)
- Golden evaluation cases + evaluation script

## v0.2.0 (2026-06-18)
- GitHub Action MVP with summary + inline comments
- Patch parser + demo PR files + smoke test

## v0.1.0 (2026-06-17)
- Core review engine: 7 OWASP rule detectors, RAG retriever, fixer, risk scoring
- Dataset creation + publication to Hugging Face + Kaggle
- ChromaDB RAG index (2,833 docs)
