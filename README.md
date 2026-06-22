# CodeSecAudit AI

**Rule-based + RAG security code review engine for Python.**

CodeSecAudit AI detects OWASP Top 10 vulnerabilities in Python code using
deterministic pattern matching (7 rules), optionally augmented with
retrieval-augmented generation (RAG) over OWASP cheat sheets (2,833 ChromaDB
docs). Ships with a CLI, FastAPI, Streamlit UI + dashboard, GitHub Action, and
a lightweight Docker image (~500 MB; RAG optional).

## Features

- **7 rule-based detectors** — CWE-94 (code injection), CWE-89 (SQLi),
  CWE-78 (command injection), CWE-328 (weak hash), CWE-798 (hardcoded creds),
  CWE-22 (path traversal), CWE-918 (SSRF)
- **Optional RAG** — ChromaDB index of OWASP cheat sheets used by the fixer
- **Autofix generation** — template-based suggestions per CWE
- **Risk scoring** — weighted severity → 0–100 score with verdict
- **Review history** — SQLite persistence via FastAPI CRUD endpoints
- **GitHub Action** — automatic PR comments (summary + inline, max 10 lines)
- **Streamlit apps** — review interface + analytics dashboard
- **Docker Compose** — 3-service stack (API, review UI, dashboard)

## Quick Start

```bash
# Install lightweight (rules-only, no heavy ML deps)
pip install -e ".[api,ui]"

# Start the API
uvicorn api.main:app --port 8003

# Start the review UI
streamlit run ui/app.py --server.port 8501

# Start the dashboard
streamlit run ui/dashboard.py --server.port 8502
```

## Usage

### CLI

```bash
python scripts/review_code.py path/to/code.py
```

### API

```bash
curl -X POST http://localhost:8003/review \
  -H "Content-Type: application/json" \
  -d '{"code": "eval(user_input)", "use_rag": false}'
```

### Python

```python
from review_engine.pipeline import review_code

result = review_code("eval(user_input)", use_rag=False)
print(result["summary"])  # Found 1 issue(s): CWE-94. Risk score: 25/100...
```

## Services

| Service    | Port  | Description                          |
|------------|-------|--------------------------------------|
| API        | 8003  | FastAPI review + history endpoints   |
| Review UI  | 8501  | Streamlit code review interface      |
| Dashboard  | 8502  | Analytics dashboard with charts      |

## Docker

See [docs/docker.md](docs/docker.md) for build options including RAG mode.

```bash
docker compose build
docker compose up -d
```

## Evaluation

```bash
python scripts/evaluate_reviewer.py
```

Runs 12 golden cases spanning all 7 supported CWEs. All pass.

## Project Structure

```
├── review_engine/       # Core: critic, fixer, retriever, pipeline, schemas
├── review_store/        # SQLite persistence layer
├── api/                 # FastAPI application
├── ui/                  # Streamlit apps (review + dashboard)
├── scripts/             # CLI, evaluation, smoke test, RAG index builder
├── eval/                # Golden test cases
├── docs/                # Documentation
└── data/                # RAG index, datasets (gitignored except index)
```

## GitHub App

The GitHub App is the primary way to automate PR reviews for your repositories.
Once installed, it listens on `pull_request` events and posts inline comments.

> **Status**: Coming soon. Until then, use the [GitHub Action](.github/workflows/pr_review.yml)
> as a manual MVP fallback.

[![Install GitHub App](https://img.shields.io/badge/GitHub%20App-Install-blue)]()

---

## Try Demo

Try the review engine live without installing anything:

[![Hugging Face Space](https://img.shields.io/badge/Hugging%20Face-Demo-yellow)]()

The demo runs the rules-only engine (no RAG, no auth, single-user).

---

## Deployment Architecture

| Component       | Host               | Purpose                         |
|-----------------|--------------------|---------------------------------|
| Demo (rules)    | Hugging Face Space | Public lightweight playground   |
| API + Dashboard | Render / Railway   | Production backend              |
| Database        | MongoDB Atlas      | Users, reviews, usage           |
| Email           | Resend             | Notifications                   |
| GitHub App      | GitHub Marketplace | Final PR integration            |

See [docs/deployment_strategy.md](docs/deployment_strategy.md) for details.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Key variables:

| Variable                   | Description                       |
|----------------------------|-----------------------------------|
| `PUBLIC_WEBSITE_URL`       | Public website URL                |
| `MONGODB_URI`              | MongoDB Atlas connection string   |
| `RESEND_API_KEY`           | Resend API key for emails         |
| `GITHUB_APP_ID`            | GitHub App ID                     |
| `GITHUB_CLIENT_ID`         | GitHub OAuth client ID            |
| `GITHUB_CLIENT_SECRET`     | GitHub OAuth client secret        |
| `GITHUB_WEBHOOK_SECRET`    | GitHub webhook secret token       |
| `GITHUB_PRIVATE_KEY_BASE64`| GitHub App private key (base64)   |
| `FREE_PR_REVIEWS_PER_MONTH`| Free tier PR review limit (30)    |
| `CODESEC_ENABLE_RAG`       | Enable RAG retrieval (`true`/`false`) |
| `OWNER_CONTACT_EMAIL`      | Contact email for limit overrides  |

Never commit real secrets to version control.

---

## Owner Contact

For questions, custom plans, or limit increases:

📧 **omchoksi108@gmail.com**

---

## RAG Index

The ChromaDB index (2,833 docs, 384-dim, cosine) is built from OWASP Python
cheat sheets and CodeXGLUE security commits. Build it locally:

```bash
python scripts/build_rag_index.py
```
