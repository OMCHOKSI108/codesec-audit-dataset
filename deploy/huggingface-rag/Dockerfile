FROM python:3.11-slim

WORKDIR /app

COPY rag_service/ rag_service/

RUN pip install --no-cache-dir \
    fastapi>=0.100.0 \
    uvicorn[standard]>=0.20.0 \
    sentence-transformers>=2.2.0 \
    numpy>=1.24.0 \
    requests>=2.31.0 \
    pydantic>=2.0.0

ENV RAG_BUILD_ON_START=true
ENV RAG_DATASET_REPO=OMCHOKSI108/CodeSecAudit-RAG
ENV RAG_CORPUS_FILE=rag/rag_corpus.jsonl.gz
ENV RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ENV RAG_INDEX_PATH=/tmp/codesec_rag_index

EXPOSE 7860

CMD ["uvicorn", "rag_service.main:app", "--host", "0.0.0.0", "--port", "7860"]
