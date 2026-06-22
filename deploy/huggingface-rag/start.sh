#!/usr/bin/env bash
set -euo pipefail

echo "=== CodeSecAudit RAG Service ==="
echo "Dataset : ${RAG_DATASET_REPO:-OMCHOKSI108/CodeSecAudit-RAG}"
echo "Model   : ${RAG_EMBEDDING_MODEL:-sentence-transformers/all-MiniLM-L6-v2}"
echo "Port    : 7860"
echo ""

uvicorn rag_service.main:app --host 0.0.0.0 --port 7860
