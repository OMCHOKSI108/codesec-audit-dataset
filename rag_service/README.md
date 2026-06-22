# CodeSecAudit RAG Service

Remote RAG microservice for OWASP cheat sheet retrieval.

## Run locally

```bash
pip install fastapi uvicorn sentence-transformers numpy requests pydantic
uvicorn rag_service.main:app --port 7860
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/rag/search` | POST | Search RAG corpus |

### POST /rag/search

```json
{"query": "sql injection prepared statements", "top_k": 3}
```

Set `RAG_API_KEY` env var and pass `X-CodeSec-RAG-Key` header to protect the endpoint.
