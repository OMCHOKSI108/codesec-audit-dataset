#!/usr/bin/env bash
set -e

echo "Starting CodeSecAudit Website..."
exec gunicorn website.app:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 60 --access-logfile -
