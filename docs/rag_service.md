# RAG Service Architecture

> **Production**: Always set `RAG_API_KEY` on the RAG Space. Without it, the service is **public** — anyone with the Space URL can query your RAG index. The main API should also set `CODESEC_RAG_API_KEY` to match.

## Why Separate RAG?

RAG dependencies (sentence-transformers, ChromaDB, PyTorch) add ~7 GB to the
Docker image. For free-tier deployment, they should live in exactly one place:
the Hugging Face Space RAG service.

All other services (API, dashboard, website) stay lightweight (~500 MB) and
call the RAG service over HTTP when needed.

## Architecture

```
GitHub PR / API review
        │
        ▼
  critic detects issue
        │
        ▼
  CODESEC_RAG_MODE=remote ────► RAG Service (HF Space)
        │                            │
        │                     POST /rag/search
        │                     X-CodeSec-RAG-Key
        │                            │
        │                     returns OWASP guidance
        │                            │
        ◄────────────────────────────┘
        │
        ▼
  fixer uses retrieved guidance
        │
        ▼
  review result includes context + better suggested fix
```

## Local Run

```bash
# Install deps
pip install fastapi uvicorn sentence-transformers numpy requests pydantic

# Start the RAG service
uvicorn rag_service.main:app --port 7860
```

The service downloads the corpus from Hugging Face on startup and builds a
cosine-similarity index with all-MiniLM-L6-v2 embeddings.

## Test Locally

```bash
curl http://localhost:7860/health

curl -X POST http://localhost:7860/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query":"sql injection prepared statements","top_k":3}'
```

## Deploy to Hugging Face Space

### Method A — Python deploy script (recommended)

Requires `huggingface_hub` installed. Automates packaging, Space creation, file upload, and secrets.

```bash
export HF_TOKEN="your_huggingface_write_token"
export HF_RAG_SPACE_ID="OMCHOKSI108/codesec-rag-service"
export RAG_API_KEY="your-shared-rag-key"

python scripts/deploy_hf_rag_space.py
```

If `HF_TOKEN` is not set, the script falls back to printing git-push instructions (Method B).

The script:
1. Runs `prepare_hf_rag_space.py` to package files
2. Creates the Space if it doesn't exist (Docker SDK, port 7860)
3. Uploads all package files
4. Sets Space secrets: `RAG_API_KEY`, `RAG_DATASET_REPO`, `RAG_CORPUS_FILE`, `RAG_EMBEDDING_MODEL`
5. Restarts the Space
6. Prints the Space URL and direct URL

### Method B — Git push (fallback)

```bash
# 1. Package the Space files
python scripts/prepare_hf_rag_space.py

# 2. Push to Hugging Face
cd dist/huggingface-rag-space
git init
git remote add origin https://huggingface.co/spaces/OMCHOKSI108/codesec-rag-service
git add .
git commit -m "deploy CodeSecAudit RAG service"
git push origin main
```

Then add secrets manually at https://huggingface.co/spaces/OMCHOKSI108/codesec-rag-service/settings:
| Secret | Required | Description |
|---|---|---|
| `RAG_API_KEY` | **Production** | Shared API key for request auth. If empty, public. |
| `RAG_DATASET_REPO` | No | HF dataset repo (default: `OMCHOKSI108/CodeSecAudit-RAG`) |
| `RAG_CORPUS_FILE` | No | Path to corpus in repo |
| `RAG_EMBEDDING_MODEL` | No | Sentence-transformer model name |

### Method C — Manual upload

1. Package the Space files:
   ```bash
   python scripts/prepare_hf_rag_space.py
   ```
2. Create a new Space at https://huggingface.co/new-space
3. Choose **Docker** SDK
4. Upload all files from `dist/huggingface-rag-space/` via the HF UI
5. Add Secrets in Space Settings
6. Space builds and starts on port 7860.

### Test the Space locally with Docker

```bash
# Build the Docker image
cd dist/huggingface-rag-space
docker build -t codesec-rag-space .

# Run with an API key
docker run -p 7860:7860 --env RAG_API_KEY=test-key codesec-rag-space
```

Then test in another terminal:

```bash
curl http://localhost:7860/health

curl -X POST http://localhost:7860/rag/search \
  -H "Content-Type: application/json" \
  -H "X-CodeSec-RAG-Key: test-key" \
  -d '{"query":"sql injection prepared statements","top_k":3}'
```

### Verify the remote service

```bash
export CODESEC_RAG_SERVICE_URL=https://your-space.hf.space
export CODESEC_RAG_API_KEY=your-key

python scripts/check_remote_rag_service.py
```

Expected output:

```
Checking remote RAG service at: https://your-space.hf.space

[1/2] Health check:
  status:        ok
  total_chunks:  2833
  index_loaded:  True
  uptime:        42s

[2/2] Search test:
  results:       3
  query_time_ms: 198.45
  total_chunks:  2833
  model:         sentence-transformers/all-MiniLM-L6-v2
  top_result:
    rank:   1
    score:  0.7651
    title:  SQL Injection Prevention Cheat Sheet
    cwe_id: CWE-89
    source: SQL_Injection_Prevention_Cheat_Sheet.md

OK: Remote RAG service is healthy and responding
```

## Connect Main API

```bash
# In your main API .env:
CODESEC_ENABLE_RAG=true
CODESEC_RAG_MODE=remote
CODESEC_RAG_SERVICE_URL=https://your-space.hf.space
CODESEC_RAG_API_KEY=your-internal-key
```

## Fallback Behavior

If the remote RAG service is unreachable:

- The review **still completes** (rule-only mode).
- `metadata["rag_error"]` is set to `"Remote RAG service unavailable: ..."`.
- No retrieved context is added to issues.

## Local RAG Mode

For local development (with chromadb installed):

```bash
CODESEC_ENABLE_RAG=true
CODESEC_RAG_MODE=local
```

This uses the existing `review_engine.retriever.RAGRetriever` with the local
ChromaDB index.

## Environment Variables

### Main API (.env)

| Variable | Description |
|---|---|
| `CODESEC_ENABLE_RAG` | Enable RAG (true/false) |
| `CODESEC_RAG_MODE` | `local` (ChromaDB) or `remote` (HF Space) |
| `CODESEC_RAG_SERVICE_URL` | Remote RAG service URL |
| `CODESEC_RAG_API_KEY` | API key for remote RAG service |
| `CODESEC_RAG_TIMEOUT` | HTTP timeout in seconds (default: 15) |
| `CODESEC_DEFAULT_TOP_K` | Default number of results |

### RAG Service (Hugging Face Space)

| Variable | Required | Description |
|---|---|---|
| `RAG_API_KEY` | **Production** | API key for request auth. **Must be set in production.** If empty, anyone with the URL can query your RAG index. |
| `RAG_DATASET_REPO` | No | HF dataset repo (default: `OMCHOKSI108/CodeSecAudit-RAG`) |
| `RAG_CORPUS_FILE` | No | Path to corpus file in repo |
| `RAG_EMBEDDING_MODEL` | No | Sentence-transformer model name |
| `RAG_INDEX_PATH` | No | Temp path for index (unused with numpy impl) |
| `RAG_BUILD_ON_START` | No | Build index on startup (true/false) |
| `RAG_TOP_K_DEFAULT` | No | Default top-k |
| `RAG_MAX_RESULTS` | No | Max results per query |
