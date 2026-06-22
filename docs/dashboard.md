# Review History Dashboard

Streamlit dashboard for CodeSecAudit AI review history and analytics.

## What It Shows

- API health and uptime
- Stats cards: total reviews, avg risk score, high risk reviews, total issues, verdict counts
- Charts: verdict distribution bar chart, risk score distribution bar chart
- Recent reviews table with filtering (verdict, minimum risk score, repo text search)
- Review detail viewer: full review record + issues table + CWE breakdown chart
- Manual refresh button

## How to Run

### 1. Start the API

```bash
uvicorn api.main:app --port 8003
```

### 2. (Optional) Seed sample data

```bash
curl -X POST http://localhost:8003/review/code \
  -H "Content-Type: application/json" \
  -d '{"code": "eval(user_input)", "file_path": "demo.py", "use_rag": false}'
```

Or via the GitHub dry-run:

```bash
python scripts/github_pr_review.py --dry-run --files examples/vulnerable_pr_demo.py --save
```

### 3. Start the dashboard

```bash
streamlit run ui/dashboard.py
```

Open `http://localhost:8501` in a browser.

## API Endpoints Used

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health check + uptime |
| `GET /stats` | Aggregated analytics |
| `GET /reviews` | List of recent reviews |
| `GET /reviews/{id}` | Full review with issues |

## Configuration

Set `CODESEC_API_URL` environment variable to change the API base URL:

```bash
export CODESEC_API_URL=http://localhost:8003
streamlit run ui/dashboard.py
```

## Filters

- **Verdict**: filter by APPROVE / WARNING / REQUEST_CHANGES
- **Min risk score**: slider to filter by minimum risk score
- **Repo search**: text match on repository name

Filtering is client-side (pandas).

## Limitations

- No authentication.
- No real-time updates (manual refresh required).
- Charts are Streamlit native (no Plotly dependency).
- Table shows max 200 reviews.
- Dashboard assumes API is at same host.
