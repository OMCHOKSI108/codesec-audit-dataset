# Render Deployment

Deploy CodeSecAudit AI on Render with three services: API, Dashboard, and Review UI.

The RAG retrieval service remains on Hugging Face Space (already deployed at `https://OMCHOKSI108-codereview-agent.hf.space`).

## Option A: Blueprint Deploy (Recommended)

1. Push the repository to GitHub.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New → Blueprint**.
4. Select your repository (`OMCHOKSI108/codesec-audit-dataset`).
5. Render reads `render.yaml` and creates three services:

   | Service | Name | Purpose |
   |---|---|---|
   | API | `codesec-api` | FastAPI review + history endpoints |
   | Dashboard | `codesec-dashboard` | Streamlit analytics dashboard |
   | Review UI | `codesec-review-ui` | Streamlit review interface |

6. **Add the secret** `CODESEC_RAG_API_KEY` in the Render dashboard for `codesec-api` (under Environment → Secret Files). This is the API key shared with the HF Space RAG service.
7. **Update** `CODESEC_API_URL` on `codesec-dashboard` and `codesec-review-ui` to the actual URL of your deployed API service (e.g., `https://codesec-api.onrender.com`). This is set automatically by the blueprint but may need a suffix if the URL differs.
8. Click **Apply** and wait for the build (~3-5 min per service).

## Option B: Manual Service Creation

### 1. Create the API Service

| Setting | Value |
|---|---|
| **Type** | Web Service |
| **Name** | `codesec-api` |
| **Environment** | Docker |
| **Dockerfile Path** | `deploy/render/api.Dockerfile` |
| **Plan** | Free |
| **Health Check Path** | `/health` |

**Required env vars**:

```env
APP_ENV=production
CODESEC_ENABLE_RAG=true
CODESEC_RAG_MODE=remote
CODESEC_RAG_SERVICE_URL=https://OMCHOKSI108-codereview-agent.hf.space
CODESEC_RAG_API_KEY=<secret>
CODESEC_DEFAULT_TOP_K=3
DATABASE_BACKEND=sqlite
CODESEC_DB_PATH=/tmp/reviews.db
OWNER_CONTACT_EMAIL=omchoksi108@gmail.com
```

`CODESEC_RAG_API_KEY` must be set as a **secret** (not plain text). It must match the `RAG_API_KEY` set on the Hugging Face Space.

### 2. Create the Dashboard Service

| Setting | Value |
|---|---|
| **Type** | Web Service |
| **Name** | `codesec-dashboard` |
| **Environment** | Docker |
| **Dockerfile Path** | `deploy/render/dashboard.Dockerfile` |
| **Plan** | Free |

**Required env vars**:

```env
CODESEC_API_URL=https://codesec-api.onrender.com
```

Replace with your actual API URL after the API service deploys.

### 3. Create the Review UI Service

| Setting | Value |
|---|---|
| **Type** | Web Service |
| **Name** | `codesec-review-ui` |
| **Environment** | Docker |
| **Dockerfile Path** | `deploy/render/review-ui.Dockerfile` |
| **Plan** | Free |

**Required env vars**:

```env
CODESEC_API_URL=https://codesec-api.onrender.com
```

## Verify Deployment

After all services deploy, run the smoke test:

```bash
export RENDER_API_URL=https://codesec-api.onrender.com
export RENDER_DASHBOARD_URL=https://codesec-dashboard.onrender.com
export RENDER_REVIEW_UI_URL=https://codesec-review-ui.onrender.com

python scripts/check_render_deployment.py
```

Expected output:

```
[1/6] API /health .................... PASS
[2/6] API / .......................... PASS
[3/6] API /review/code ............... PASS
[4/6] API /stats ..................... PASS
[5/6] Dashboard URL .................. PASS
[6/6] Review UI URL .................. PASS
All checks passed.
```

## Architecture

```text
┌─────────────────────────────┐
│     Hugging Face Space      │
│  codesec-rag-service        │
│  /rag/search (RAG index)    │
│  2,833 OWASP chunks         │
└──────────┬──────────────────┘
           │ HTTP (outbound from Render)
           ▼
┌─────────────────────────────┐
│     Render — codesec-api     │
│  FastAPI review + history    │
│  SQLite at /tmp/reviews.db   │
│  Health: /health             │
└──────────┬──────────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌─────────┐
│ Dashboard│ │Review UI│
│streamlit │ │streamlit│
└──────────┘ └─────────┘
```

## Known Limitations on Render Free

| Limitation | Impact | Mitigation |
|---|---|---|
| **Spin-down after inactivity** | First request after idle period takes 30-60s | Set up external uptime monitor (e.g., UptimeRobot, cron-job.org) |
| **Ephemeral filesystem** | SQLite DB (`/tmp/reviews.db`) resets on each deploy or restart | Migrate to MongoDB Atlas for production persistence |
| **512 MB RAM** | May limit concurrent request handling | Rule-based engine is lightweight (~100 MB idle) |
| **No cron jobs on free** | Cannot run periodic tasks | Use external cron services if needed |

## Production Readiness Next Steps

1. **MongoDB Atlas** — Replace SQLite with MongoDB for persistent review storage.
2. **Resend Email** — Set `RESEND_API_KEY` and enable email workflows.
3. **GitHub App** — Register a GitHub App and set `GITHUB_*` env vars.
4. **Custom Domain** — Add a custom domain in Render dashboard.
5. **Paid Plan** — Upgrade from free to starter/individual for no spin-down.
