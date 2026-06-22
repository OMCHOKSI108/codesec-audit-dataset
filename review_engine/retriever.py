from __future__ import annotations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX_PATH = str(ROOT / "data/final/rag_index")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "owasp_rag"


class RAGRetriever:
    def __init__(self, index_path: str = DEFAULT_INDEX_PATH):
        import chromadb
        from chromadb.config import Settings

        index_dir = Path(index_path)
        if not index_dir.exists():
            raise FileNotFoundError(
                f"ChromaDB index not found at {index_path}. "
                "Run `python scripts/build_rag_index.py` first."
            )

        self._client = chromadb.PersistentClient(
            path=index_path,
            settings=Settings(anonymized_telemetry=False),
        )

        existing = [c.name for c in self._client.list_collections()]
        if COLLECTION_NAME not in existing:
            raise FileNotFoundError(
                f"Collection '{COLLECTION_NAME}' not found in ChromaDB at {index_path}. "
                "Run `python scripts/build_rag_index.py` first."
            )

        self._collection = self._client.get_collection(COLLECTION_NAME)
        self._model = None

    def _get_model(self):
        from sentence_transformers import SentenceTransformer

        if self._model is None:
            self._model = SentenceTransformer(EMBED_MODEL)
        return self._model

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        model = self._get_model()
        query_emb = model.encode([query]).tolist()
        results = self._collection.query(
            query_embeddings=query_emb,
            n_results=top_k,
        )

        contexts: list[dict] = []
        if not results["ids"][0]:
            return contexts

        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            contexts.append({
                "source": meta.get("source_file", ""),
                "title": meta.get("title", ""),
                "section": meta.get("section_title", ""),
                "cwe_id": meta.get("cwe_id", ""),
                "content": doc,
            })

        return contexts

    @property
    def collection_name(self) -> str:
        return COLLECTION_NAME

    @property
    def document_count(self) -> int:
        return self._collection.count()
