# API Reference

Base URL: `http://localhost:8003` (local) or your deployed URL.

## `GET /`

Root endpoint with application info and configuration.

**Response**:
```json
{
  "app": "CodeSecAudit AI API",
  "version": "0.6.0",
  "description": "RAG-powered security code review engine",
  "uptime": "0h 12m 34s",
  "uptime_seconds": 754,
  "start_time_iso": "2026-06-22T12:00:00Z",
  "configuration": {
    "rag_index_path": "data/final/rag_index",
    "top_k_default": 3,
    "database": "data/app/reviews.db",
    "review_rules": 7,
    "rag_index_loaded": true
  }
}
```

---

## `GET /health`

Health check with RAG index status.

**Response**:
```json
{
  "status": "ok",
  "engine_version": "0.6.0",
  "collection": "owasp_rag",
  "documents": 2833,
  "uptime_seconds": 754
}
```

---

## `POST /review`

Review source code without saving to history.

**Request**:
```json
{
  "code": "eval(user_input)",
  "file_path": "demo.py",
  "top_k": 3,
  "use_rag": true
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `code` | string | — | Source code to analyze (required, min 1 char) |
| `file_path` | string | `null` | Source file path (for display) |
| `top_k` | integer | `3` | Number of RAG results (1–20) |
| `use_rag` | boolean | `true` | Enable RAG retrieval |

**Response**:
```json
{
  "summary": "Found 1 issue(s): CWE-94. Risk score: 35/100. Verdict: WARNING.",
  "risk_score": 35,
  "verdict": "WARNING",
  "issues": [
    {
      "cwe_id": "CWE-94",
      "severity": "critical",
      "message": "Code injection via eval()",
      "line": 1,
      "snippet": "eval(user_input)",
      "file_path": "demo.py",
      "suggested_fix": "Avoid using eval() with untrusted input. Use ast.literal_eval() or a safe parser instead."
    }
  ],
  "metadata": {
    "engine_version": "0.6.0",
    "rag_used": true,
    "rag_error": null,
    "total_issues_found": 1,
    "total_issues_reported": 1,
    "deduplication_skipped": 0,
    "limit_capped_by_rule": 0,
    "limit_capped_total": false
  }
}
```

---

## `POST /review/code`

Review source code and save the result to the review history database.

**Request**:
```json
{
  "code": "eval(user_input)",
  "file_path": "demo.py",
  "source": "api",
  "repo": "owner/repo",
  "pr_number": 12,
  "commit_sha": "abc123def456",
  "top_k": 3,
  "use_rag": false
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `code` | string | — | Source code to analyze (required) |
| `file_path` | string | `null` | Source file path |
| `source` | string | `"api"` | Origin (`api`, `cli`, `github-action`) |
| `repo` | string | `null` | GitHub `owner/repo` |
| `pr_number` | integer | `null` | Pull request number |
| `commit_sha` | string | `null` | Commit SHA |
| `top_k` | integer | `3` | Number of RAG results (1–20) |
| `use_rag` | boolean | `true` | Enable RAG retrieval |

**Response**:
```json
{
  "review_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "summary": "Found 1 issue(s): CWE-94. Risk score: 35/100. Verdict: WARNING.",
  "risk_score": 35,
  "verdict": "WARNING",
  "issues": [...],
  "metadata": {...},
  "created_at": "2026-06-22T12:34:56Z"
}
```

---

## `GET /reviews`

List past reviews, newest first.

**Query Parameters**:

| Parameter | Default | Max | Description |
|---|---|---|---|
| `limit` | 50 | 200 | Number of reviews to return |
| `offset` | 0 | — | Pagination offset |

**Request**:
```bash
curl "http://localhost:8003/reviews?limit=10&offset=0"
```

**Response**:
```json
{
  "reviews": [
    {
      "review_id": "a1b2c3d4-...",
      "source": "api",
      "repo": "owner/repo",
      "pr_number": 12,
      "file_path": "demo.py",
      "risk_score": 35,
      "verdict": "WARNING",
      "summary": "Found 1 issue(s): CWE-94...",
      "created_at": "2026-06-22T12:34:56Z"
    }
  ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

---

## `GET /reviews/{review_id}`

Get a single review with full issue details.

**Request**:
```bash
curl "http://localhost:8003/reviews/a1b2c3d4-..."
```

**Response**:
```json
{
  "review_id": "a1b2c3d4-...",
  "source": "api",
  "repo": "owner/repo",
  "pr_number": 12,
  "commit_sha": "abc123",
  "file_path": "demo.py",
  "risk_score": 35,
  "verdict": "WARNING",
  "summary": "Found 1 issue(s): CWE-94...",
  "issues": [
    {
      "cwe_id": "CWE-94",
      "severity": "critical",
      "message": "Code injection via eval()",
      "line": 1,
      "snippet": "eval(user_input)",
      "file_path": "demo.py",
      "suggested_fix": "Avoid using eval() with untrusted input..."
    }
  ],
  "metadata": {
    "engine_version": "0.6.0",
    "rag_used": false,
    "total_issues_found": 1,
    "total_issues_reported": 1
  },
  "created_at": "2026-06-22T12:34:56Z"
}
```

Returns `404` if review not found.

---

## `GET /stats`

Aggregated analytics from the review history database.

**Response**:
```json
{
  "total_reviews": 42,
  "verdict_counts": {
    "APPROVE": 15,
    "WARNING": 20,
    "REQUEST_CHANGES": 7
  },
  "average_risk_score": 28.5,
  "high_risk_reviews": 5,
  "total_issues": 63
}
```

---

## Error Responses

| Status | Description |
|---|---|
| `400` | Invalid request body (e.g., empty code) |
| `404` | Review not found |
| `422` | Validation error (e.g., `top_k` out of range) |
| `500` | Internal server error |
