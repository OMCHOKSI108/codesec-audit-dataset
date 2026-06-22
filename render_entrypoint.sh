#!/usr/bin/env bash
set -e

SERVICE="${RENDER_SERVICE:-api}"

case "$SERVICE" in
  api)
    exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8003}"
    ;;
  dashboard)
    exec streamlit run ui/dashboard.py --server.address 0.0.0.0 --server.port "${PORT:-8502}" --server.headless true
    ;;
  review-ui)
    exec streamlit run ui/app.py --server.address 0.0.0.0 --server.port "${PORT:-8501}" --server.headless true
    ;;
  *)
    echo "Unknown RENDER_SERVICE: $SERVICE (use: api, dashboard, review-ui)"
    exit 1
    ;;
esac
