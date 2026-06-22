#!/usr/bin/env bash
set -e
gunicorn website.app:app --bind 0.0.0.0:${PORT:-10000}
