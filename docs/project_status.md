# Project Status

## Component Status

| Component | Status | Notes |
|---|---|---|
| Dataset (CodeSecAudit-RAG) | **Done** | 28,548 records, 2,833 RAG chunks, published to HF + Kaggle |
| Kaggle Notebook | **Done** | Dataset exploration + RAG prototype |
| Review Engine (core) | **Done** | Critic, fixer, retriever, risk scorer, pipeline |
| GitHub Action | **Done** | PR triggers, summary + inline comments, max caps |
| Inline PR Comments | **Done** | 10-comment cap, duplicate detection via fingerprint |
| Evaluation Framework | **Done** | 12 golden cases, all passing |
| Review History DB (SQLite) | **Done** | CRUD endpoints, pagination, stats |
| Streamlit Dashboard | **Done** | Stats cards, charts, filters, review detail viewer |
| Docker Compose | **Done** | 3-service stack, lightweight default, RAG optional |
| RAG Service (HF Space) | **Deployed** | Live at https://OMCHOKSI108-codereview-agent.hf.space |
| Remote RAG Client | **Done** | `search_remote_rag()`, `remote_rag_available()` in pipeline |
| Deployment Scripts | **Done** | `prepare_hf_rag_space.py`, `deploy_hf_rag_space.py`, smoke tests |
| Render / Railway Deployment | **Pending** | Not yet deployed |
| MongoDB Atlas Integration | **Pending** | Schema designed; code not implemented |
| Resend Email Implementation | **Pending** | Workflows designed; code not implemented |
| GitHub OAuth | **Pending** | Not yet implemented |
| GitHub App Install Flow | **Pending** | Not yet implemented |
| Usage Limit Enforcement | **Pending** | Schema designed; enforcement not yet built |

## Design Artifacts

| Artifact | File |
|---|---|
| SaaS Data Model (7 MongoDB collections) | [docs/saas_data_model.md](saas_data_model.md) |
| Email Workflows (4 email types) | [docs/email_workflows.md](email_workflows.md) |
| Usage Limits (free tier: 30 reviews/month) | [docs/usage_limits.md](usage_limits.md) |
| Deployment Strategy | [docs/deployment_strategy.md](deployment_strategy.md) |

## Known Gaps

- No authentication anywhere (API, dashboard, RAG service are public in demo mode)
- SQLite is single-writer; concurrent CI runs may queue
- No data retention policy; DB size grows unbounded
- GitHub Action uses `use_rag=False` until caching is configured
- Docker RAG mode adds ~7 GB and ~8 min build time
- HF Space Docker SDK has a known API bug with `huggingface_hub v1.19.0` (workaround: manual Space creation + git push)
