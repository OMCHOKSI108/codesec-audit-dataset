# Render Deployment

These files configure CodeSecAudit AI for deployment on Render.

## Services

| Service | Dockerfile | Start Script | Purpose |
|---|---|---|---|
| API | `api.Dockerfile` | `api_start.sh` | FastAPI review + history endpoints |
| Dashboard | `dashboard.Dockerfile` | `dashboard_start.sh` | Streamlit analytics dashboard |
| Review UI | `review-ui.Dockerfile` | `review_ui_start.sh` | Streamlit review interface |

## Blueprint

The root `render.yaml` defines all three services as a blueprint group.

See [docs/render_deployment.md](../../docs/render_deployment.md) for full instructions.
