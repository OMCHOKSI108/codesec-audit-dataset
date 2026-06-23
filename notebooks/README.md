# Notebooks

## CodeSecAudit AI Dataset + RAG Exploration

| Field | Value |
|-------|-------|
| **Title** | CodeSecAudit AI Dataset + RAG Exploration |
| **Author** | Om Choksi |
| **Platform** | Kaggle |
| **Kaggle Link** | [https://www.kaggle.com/code/omchoksi04/codereview](https://www.kaggle.com/code/omchoksi04/codereview) |
| **Local Export** | [`codereview.ipynb`](codereview.ipynb) |

### What it demonstrates

The notebook is the experimentation phase of the CodeSecAudit AI system. It proves the core dataset + RAG + reviewer logic end-to-end:

1. **Dataset Loading** — Loads the `OMCHOKSI108/CodeSecAudit-RAG` dataset (28,548 records from CodeXGLUE + OWASP Benchmark Python) directly from Hugging Face.
2. **CodeSecAudit-RAG Exploration** — Explores dataset quality, source distributions (CodeXGLUE vs OWASP), language balance (C vs Python), label distributions (vulnerable vs clean), CWE coverage, severity breakdown, and OWASP categories using interactive Plotly visualizations.
3. **RAG Corpus Inspection** — Loads and inspects the 2,833 OWASP Cheat Sheet Series chunks that power the retrieval-augmented guidance.
4. **Semantic Search** — Builds a ChromaDB vector index using `all-MiniLM-L6-v2` embeddings (384-dim) and runs similarity search queries against the OWASP corpus.
5. **Critic → Retriever → Fixer Prototype** — Runs a lightweight end-to-end pipeline: the Critic scans code for CWE patterns, the Retriever fetches relevant OWASP guidance, and the Fixer generates suggested remediations.
6. **Evaluation Examples** — Tests the pipeline against known vulnerable and safe code samples with structured output.

### Pipeline Path

```
Notebook prototype → CLI reviewer → FastAPI API → Streamlit UI → GitHub PR bot → Docker deployment
```

### File

- `codereview.ipynb` — Exported Kaggle notebook (local copy for reference)

### Note

The live notebook is hosted on Kaggle. The local `.ipynb` export may lag behind the latest Kaggle version. Run or fork the notebook directly on Kaggle for the most up-to-date interactive experience.
