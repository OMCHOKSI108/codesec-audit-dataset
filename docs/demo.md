# Demo

## Local Demo (No Docker)

```bash
# Install
pip install -e ".[dev]"

# CLI review
python scripts/review_code.py --code "eval(user_input)" --json
```

Expected output: JSON with 1 issue (CWE-94), risk score 35, verdict WARNING.

### Manual review with file

```bash
python scripts/review_code.py --file examples/vulnerable_pr_demo.py --json
```

Expected: multiple CWEs (94, 328, 798, 22, 78), risk score > 50, verdict REQUEST_CHANGES.

### Safe file

```bash
python scripts/review_code.py --file examples/safe_pr_demo.py --json
```

Expected: 0 issues, risk score 0, verdict APPROVE.

## Docker Demo

```bash
# Start all services
docker compose up --build

# In another terminal
curl -X POST http://localhost:8003/review \
  -H "Content-Type: application/json" \
  -d '{"code": "eval(user_input)"}'
```

### Access the services

| Service | URL |
|---|---|
| API | http://localhost:8003 |
| API docs (Swagger) | http://localhost:8003/docs |
| Review UI | http://localhost:8501 |
| Dashboard | http://localhost:8502 |

### Dashboard after seeding data

```bash
# Submit a few reviews
curl -X POST http://localhost:8003/review/code \
  -H "Content-Type: application/json" \
  -d '{"code": "eval(user_input)", "file_path": "demo.py", "use_rag": false}'

curl -X POST http://localhost:8003/review/code \
  -H "Content-Type: application/json" \
  -d '{"code": "def add(a, b): return a + b", "file_path": "safe.py", "use_rag": false}'
```

Then open http://localhost:8502 for the dashboard.

## GitHub Dry-Run Demo

```bash
# Simulates what the GitHub Action produces
python scripts/github_pr_review.py --files examples/vulnerable_pr_demo.py --dry-run
```

Expected output:
- Summary markdown with verdict, risk score, issue table
- Inline Comment Plan showing which lines would get comments

## Smoke Test

```bash
./scripts/docker_smoke_test.sh
```

Verifies: health endpoint → review API → review detail → stats → Streamlit UI pages.

## RAG Service Demo

```bash
# Health
curl https://OMCHOKSI108-codereview-agent.hf.space/health

# Search
curl -X POST https://OMCHOKSI108-codereview-agent.hf.space/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "SQL injection prevention", "top_k": 2}'
```

## Kaggle Notebook

Explore the dataset, RAG corpus, and prototype Critic → Retriever → Fixer pipeline:

- **Kaggle**: https://www.kaggle.com/code/omchoksi04/codereview
- **Local export**: [`notebooks/codereview.ipynb`](../notebooks/codereview.ipynb)
- **Notebook docs**: [`notebooks/README.md`](../notebooks/README.md)

## Screenshot Checklist

See [docs/screenshots/README.md](screenshots/README.md) for the full screenshot capture guide.
