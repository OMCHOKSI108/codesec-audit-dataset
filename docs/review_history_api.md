# Review History API

Persistent review history for CodeSecAudit AI using SQLite.

## Purpose

Every review result is saved to a local SQLite database, enabling:

- Review history lookup by ID
- Listing past reviews with pagination
- Basic analytics (total reviews, verdict distribution, average risk score)
- Future dashboard data source

## Database

- **Engine**: SQLite (MVP). Future migration to PostgreSQL planned.
- **Path**: `data/app/reviews.db`
- **Created automatically** on API startup.

### Schema

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT (UUID) | Primary key |
| `source` | TEXT | api, cli, github-action, etc. |
| `repo` | TEXT NULL | GitHub `owner/repo` |
| `pr_number` | INTEGER NULL | Pull request number |
| `commit_sha` | TEXT NULL | Commit SHA |
| `file_path` | TEXT NULL | Source file path |
| `risk_score` | INTEGER | 0–100 |
| `verdict` | TEXT | APPROVE / WARNING / REQUEST_CHANGES |
| `summary` | TEXT | Human-readable summary |
| `issues_json` | TEXT | JSON array of issue objects |
| `metadata_json` | TEXT | JSON object (engine version, rag_used, etc.) |
| `created_at` | TEXT | ISO 8601 timestamp |

Indexes: `created_at`, `repo`, `verdict`, `risk_score`.

## API Endpoints

### `POST /review/code`

Submit code for review. Result is saved to the database.

```json
{
  "code": "eval(user_input)",
  "file_path": "demo.py",
  "source": "api",
  "repo": "owner/repo",
  "pr_number": 12,
  "commit_sha": "abc123",
  "use_rag": false
}
```

Response includes `review_id`:

```json
{
  "review_id": "a1b2c3d4-...",
  "summary": "Found 1 issue(s): CWE-94. Risk score: 35/100. Verdict: WARNING.",
  "risk_score": 35,
  "verdict": "WARNING",
  "issues": [...],
  "metadata": {...},
  "created_at": "2026-06-22T..."
}
```

### `GET /reviews`

List recent reviews (newest first).

| Parameter | Default | Max |
|---|---|---|
| `limit` | 50 | 200 |
| `offset` | 0 | — |

```bash
curl "http://localhost:8003/reviews?limit=10&offset=0"
```

### `GET /reviews/{review_id}`

Get a single review with full issue details.

```bash
curl "http://localhost:8003/reviews/a1b2c3d4-..."
```

Returns `404` if not found.

### `GET /stats`

Basic analytics:

```json
{
  "total_reviews": 10,
  "verdict_counts": {
    "APPROVE": 3,
    "WARNING": 5,
    "REQUEST_CHANGES": 2
  },
  "average_risk_score": 42.5,
  "high_risk_reviews": 2,
  "total_issues": 14
}
```

### Legacy Endpoints (unchanged)

- `GET /health` — health check
- `POST /review` — original review endpoint (no persistence)

## Example curl Commands

```bash
# Review and save
curl -X POST http://localhost:8003/review/code \
  -H "Content-Type: application/json" \
  -d '{"code": "eval(user_input)", "file_path": "demo.py", "use_rag": false}'

# List recent reviews
curl http://localhost:8003/reviews

# Get by ID
curl http://localhost:8003/reviews/<review_id>

# Stats
curl http://localhost:8003/stats

# Legacy endpoints still work
curl http://localhost:8003/health
curl -X POST http://localhost:8003/review \
  -H "Content-Type: application/json" \
  -d '{"code": "eval(user_input)"}'
```

## Limitations

- SQLite is single-writer; concurrent CI runs may queue.
- No authentication or access control.
- No data retention policy; DB grows unbounded.
- Analytics are basic counts only.

## Future

- Migrate to PostgreSQL for concurrency and reliability.
- Add authentication scoped to repo/org.
- Add data retention and pruning.
