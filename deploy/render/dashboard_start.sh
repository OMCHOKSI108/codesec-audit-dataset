#!/usr/bin/env bash
set -e
streamlit run ui/dashboard.py --server.address 0.0.0.0 --server.port "${PORT:-8502}" --server.headless true
