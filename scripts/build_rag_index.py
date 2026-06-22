import json
import time
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

ROOT = Path(__file__).resolve().parents[1]

RAG_PATH = ROOT / "data/final/rag/rag_corpus.jsonl"
INDEX_DIR = ROOT / "data/final/rag_index"
SUMMARY_PATH = ROOT / "data/final/metadata/rag_index_build_summary.json"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64
COLLECTION_NAME = "owasp_rag"

INDEX_DIR.mkdir(parents=True, exist_ok=True)

def load_records(path: Path):
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def main():
    print("Phase 3B: Building ChromaDB RAG Index")
    print("=" * 70)

    print(f"Loading RAG corpus from: {RAG_PATH}")
    records = load_records(RAG_PATH)
    print(f"Records: {len(records)}")

    print(f"\nLoading embedding model: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)
    print(f"  Model dimension: {model.get_sentence_embedding_dimension()}")

    print(f"\nInitializing ChromaDB at: {INDEX_DIR}")
    client = chromadb.PersistentClient(
        path=str(INDEX_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    existing = client.list_collections()
    if COLLECTION_NAME in [c.name for c in existing]:
        print(f"  Collection '{COLLECTION_NAME}' exists. Deleting...")
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = []
    metadatas = []
    documents = []

    for r in records:
        doc = r.get("content", "")
        if not doc.strip():
            continue

        ids.append(r["id"])
        metadatas.append({
            "source_file": r.get("source_file", ""),
            "title": r.get("title", ""),
            "section_title": r.get("section_title", ""),
            "cwe_id": r.get("cwe_id", ""),
            "vulnerability_name": r.get("vulnerability_name", ""),
            "owasp_category": r.get("owasp_category", ""),
            "chunk_index": r.get("chunk_index", 0),
        })
        documents.append(doc)

    print(f"Documents to index: {len(documents)}")

    print("\nEmbedding and adding to ChromaDB in batches...")
    start = time.time()

    for i in range(0, len(documents), BATCH_SIZE):
        batch_docs = documents[i : i + BATCH_SIZE]
        batch_ids = ids[i : i + BATCH_SIZE]
        batch_meta = metadatas[i : i + BATCH_SIZE]

        embeddings = model.encode(batch_docs, show_progress_bar=False).tolist()

        collection.add(
            embeddings=embeddings,
            documents=batch_docs,
            metadatas=batch_meta,
            ids=batch_ids,
        )

        print(f"  Batch {i // BATCH_SIZE + 1}: {len(batch_docs)} docs", end="\r")

    elapsed = time.time() - start
    print(f"\nIndexing complete in {elapsed:.2f}s")

    count = collection.count()
    print(f"Collection size: {count}")

    summary = {
        "collection_name": COLLECTION_NAME,
        "embedding_model": EMBED_MODEL,
        "embedding_dimension": model.get_sentence_embedding_dimension(),
        "index_location": str(INDEX_DIR),
        "documents_indexed": count,
        "time_seconds": round(elapsed, 2),
        "documents_per_second": round(count / elapsed, 2),
    }

    with SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary saved to: {SUMMARY_PATH.relative_to(ROOT)}")

    print("\n--- Testing query ---")
    test_query = "How do I prevent SQL injection?"
    query_emb = model.encode([test_query])
    results = collection.query(query_embeddings=query_emb.tolist(), n_results=3)
    print(f"Query: {test_query}")
    for j, doc in enumerate(results["documents"][0][:3]):
        meta = results["metadatas"][0][j]
        print(f"\n  Result {j+1}: {meta['title']} > {meta['section_title']}")
        print(f"  CWE: {meta['cwe_id']}")
        print(f"  Snippet: {doc[:200]}...")

    print("\n" + "=" * 70)
    print("RAG index build: COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
