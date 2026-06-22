import gzip
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import numpy as np
import requests
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DEFAULT_DATASET_REPO = "OMCHOKSI108/CodeSecAudit-RAG"
DEFAULT_CORPUS_FILE = "rag/rag_corpus.jsonl.gz"
DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class RagIndex:
    def __init__(self):
        self.dataset_repo: str = os.getenv("RAG_DATASET_REPO", DEFAULT_DATASET_REPO)
        self.corpus_file: str = os.getenv("RAG_CORPUS_FILE", DEFAULT_CORPUS_FILE)
        self.embed_model_name: str = os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_EMBED_MODEL)
        self.max_results: int = int(os.getenv("RAG_MAX_RESULTS", "8"))

        self._model: Optional[SentenceTransformer] = None
        self._chunks: list[dict] = []
        self._embeddings: Optional[np.ndarray] = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model: %s", self.embed_model_name)
            self._model = SentenceTransformer(self.embed_model_name)
        return self._model

    def load_corpus(self) -> int:
        url = f"https://huggingface.co/datasets/{self.dataset_repo}/resolve/main/{self.corpus_file}"
        logger.info("Downloading corpus from %s", url)
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        raw = gzip.decompress(resp.content)
        chunks = []
        for line in raw.decode("utf-8").splitlines():
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
        self._chunks = chunks
        logger.info("Loaded %d chunks", len(chunks))
        return len(chunks)

    def build_index(self) -> None:
        logger.info("Embedding %d chunks with %s ...", len(self._chunks), self.embed_model_name)
        texts = [c.get("content", "") or c.get("text", "") for c in self._chunks]
        self._embeddings = self.model.encode(texts, show_progress_bar=True)
        logger.info("Index built: shape=%s", self._embeddings.shape)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if self._embeddings is None or not self._chunks:
            return []

        k = min(top_k, self.max_results, len(self._chunks))
        query_vec = self.model.encode([query])[0]
        scores = np.dot(self._embeddings, query_vec) / (
            np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_vec) + 1e-12
        )
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for rank, idx in enumerate(top_indices, 1):
            c = self._chunks[idx]
            results.append({
                "rank": rank,
                "score": float(scores[idx]),
                "title": c.get("title", ""),
                "section_title": c.get("section_title", "") or c.get("section", ""),
                "cwe_id": c.get("cwe_id", ""),
                "content": c.get("content", "") or c.get("text", ""),
                "source_file": c.get("source_file", "") or c.get("source", ""),
            })
        return results

    @property
    def is_loaded(self) -> bool:
        return self._embeddings is not None

    @property
    def embedding_count(self) -> int:
        return len(self._embeddings) if self._embeddings is not None else 0

    @property
    def document_count(self) -> int:
        return len(self._chunks)

    @property
    def total_chunks(self) -> int:
        return len(self._chunks)
