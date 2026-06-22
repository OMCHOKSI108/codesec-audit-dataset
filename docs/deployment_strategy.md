# Deployment Strategy

## Overview

CodeSecAudit AI uses a multi-environment deployment model:

| Environment   | Host              | Purpose                        |
|---------------|-------------------|--------------------------------|
| Demo          | Hugging Face Space | Public lightweight playground   |
| Production    | Render / Railway   | API + dashboard + website       |
| Database      | MongoDB Atlas      | Users, installations, reviews   |
| Email         | Resend             | Transactional notifications     |
| GitHub App    | GitHub             | Final PR integration            |

---

## 1. Hugging Face Space — Public Demo

A read-only Streamlit Space that lets anyone try the review engine without
installing anything.

- Runs the lightweight (rules-only) engine — no RAG, no MongoDB, no auth.
- Pre-filled code samples demonstrate all 7 CWE detectors.
- Links to the production app and GitHub App install page.
- Rebuilt from `main` on each push.

**Limitations**: No PR integration, no review history, no RAG, single-user.

---

## 2. Render / Railway — Production API + Dashboard

The production backend runs on Render (or Railway) with these processes:

| Service     | Type   | Port  | Command                                      |
|-------------|--------|-------|----------------------------------------------|
| API         | Web    | 8003  | `uvicorn api.main:app --host 0.0.0.0 --port $PORT` |
| Dashboard   | Web    | 8502  | `streamlit run ui/dashboard.py --server.port $PORT` |
| Website     | Static | —     | Landing page (optional)                      |

Key configuration:

- `APP_ENV=production`
- `MONGODB_URI` — MongoDB Atlas connection string
- `RESEND_API_KEY` — for transactional emails
- `CODESEC_ENABLE_RAG=false` — default lightweight; RAG requires at least 4 GB RAM

Health checks and auto-scaling follow platform defaults.

---

## 3. MongoDB Atlas — Data Layer

All persistent data lives in MongoDB Atlas:

- **Users** — GitHub OAuth users (id, email, plan, usage counters)
- **Installations** — GitHub App installs per org/user
- **Repositories** — Repos with PR review activity
- **Reviews** — Full review results (mirrored from SQLite for historical data)
- **Usage events** — PR review consumption (1 event per reviewed PR)
- **Plans** — Tier definitions (free = 30 reviews/month, etc.)
- **Email events** — Sent email audit trail

See [saas_data_model.md](saas_data_model.md) for full schema.

---

## 4. Resend — Email

Transactional emails sent via Resend:

- Welcome email after GitHub App install
- Usage guide email (4 min after first review)
- Limit-reached notification
- Manual upgrade / contact owner prompt

See [email_workflows.md](email_workflows.md) for full workflow definitions.

---

## 5. GitHub App — Final PR Integration

Once the SaaS backend is ready, a GitHub App replaces the current GitHub Action
MVP. The App:

- Listens on `pull_request` webhooks (opened, synchronized)
- Calls the production API to review PR diffs
- Posts summary + inline comments as a GitHub App Check Run
- Respects usage limits (blocks if free tier exhausted)
- Provides seamless installation via GitHub Marketplace

**Until the GitHub App is built**, the current GitHub Action remains the MVP
fallback for PR reviews. Users can install it via the existing `.github/`
workflow files.

---

## Architecture Diagram (Text)

```
┌──────────────┐       ┌──────────────┐
│  GitHub App   │──────▶│   API / DB    │
│  (webhooks)   │       │  (Render)    │
└──────────────┘       └──────┬───────┘
                              │
                    ┌─────────▼─────────┐
                    │   MongoDB Atlas    │
                    │  (users, reviews)  │
                    └─────────┬─────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
   ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
   │  Dashboard   │    │  Website     │    │   Resend    │
   │ (Streamlit)  │    │  (landing)   │    │   Email     │
   └──────────────┘    └──────────────┘    └──────────────┘
```

**Demo** (Hugging Face Space) runs independently — no MongoDB, no GitHub App,
no auth — just the Streamlit review UI with the rules-only engine.
