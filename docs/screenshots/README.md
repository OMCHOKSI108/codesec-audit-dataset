# Screenshots

This directory should contain screenshots for documentation, demos, and the README.

## Screenshot Checklist

Capture the following screenshots and save them in this directory:

| # | Screenshot | Description | Status |
|---|---|---|---|
| 1 | `pr-summary-comment.png` | GitHub PR page showing the CodeSecAudit summary comment at the bottom | Pending |
| 2 | `inline-comment-eval.png` | Inline comment on an `eval()` line in the PR diff view | Pending |
| 3 | `github-action-run.png` | Successful GitHub Action run log in the Actions tab | Pending |
| 4 | `dashboard-stats.png` | Streamlit dashboard with stats cards, verdict chart, and recent reviews | Pending |
| 5 | `review-detail.png` | Review detail page showing full issue breakdown | Pending |
| 6 | `api-docs.png` | FastAPI Swagger UI at `/docs` showing all endpoints | Pending |
| 7 | `kaggle-notebook.png` | Kaggle notebook preview showing dataset exploration | Pending |
| 8 | `hf-dataset.png` | Hugging Face dataset page for CodeSecAudit-RAG | Pending |
| 9 | `rag-service-health.png` | RAG service health endpoint response | Pending |

## How to Capture

### GitHub Screenshots (1–3)

1. Create a test PR with `examples/vulnerable_pr_demo.py`
2. Wait for the GitHub Action to complete
3. Capture the PR comments section (screenshot 1)
4. Click on an inline comment in the Files Changed tab (screenshot 2)
5. Go to the Actions tab and open the workflow run (screenshot 3)

### Dashboard (4–5)

1. Run `docker compose up --build`
2. Submit a few reviews:
   ```bash
   curl -X POST http://localhost:8003/review/code -H "Content-Type: application/json" \
     -d '{"code": "eval(user_input)", "file_path": "demo.py"}'
   ```
3. Open http://localhost:8502 and capture the dashboard (screenshot 4)
4. Click a review to open the detail view (screenshot 5)

### API Docs (6)

1. Run `docker compose up --build`
2. Open http://localhost:8003/docs
3. Capture the Swagger UI page (screenshot 6)

### External Services (7–9)

1. Open https://www.kaggle.com/code/omchoksi04/codereview and capture (screenshot 7)
2. Open https://huggingface.co/datasets/OMCHOKSI108/CodeSecAudit-RAG and capture (screenshot 8)
3. Run `curl https://OMCHOKSI108-codereview-agent.hf.space/health` and capture the response (screenshot 9)
