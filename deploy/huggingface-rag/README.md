---
title: CodeSecAudit RAG Service
emoji: 🛡️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# CodeSecAudit RAG Service

Remote RAG microservice for OWASP cheat sheet retrieval. Deployed as a Hugging Face Space with Docker SDK.

## Deploy

1. Create a new Space at https://huggingface.co/new-space
2. Choose **Docker** (not Streamlit/Gradio)
3. Set Space SDK to **Docker**
4. Copy these files:
   - `Dockerfile`
   - `start.sh`
   - The entire `rag_service/` directory

   Or use the automated script: `python scripts/deploy_hf_rag_space.py`

5. Add Secrets in Space Settings:

   | Secret | Required | Description |
   |---|---|---|
   | `RAG_API_KEY` | **Production** | Shared API key for request auth. If empty, the service is **public** — anyone can search. |
   | `RAG_DATASET_REPO` | No | HF dataset repo (default: `OMCHOKSI108/CodeSecAudit-RAG`) |
   | `RAG_EMBEDDING_MODEL` | No | Sentence-transformer model (default: `sentence-transformers/all-MiniLM-L6-v2`) |

   > **Production**: Always set `RAG_API_KEY`. Without it, the service is public and anyone with the URL can query your RAG index.

6. Space will build and start on port 7860.

## Health check

```bash
curl https://your-space.hf.space/health
```

## Search

```bash
curl -X POST https://your-space.hf.space/rag/search \
  -H "Content-Type: application/json" \
  -H "X-CodeSec-RAG-Key: your-key" \
  -d '{"query":"sql injection prepared statements","top_k":3}'
```
