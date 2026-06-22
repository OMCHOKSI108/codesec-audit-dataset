import gzip
import json
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

VERSION = "v0.1.0"
RELEASE_DIR = ROOT / "release" / f"codesec-audit-rag-{VERSION}"

INPUTS = {
    "review_train": ROOT / "data/final/review_combined/train.jsonl",
    "review_validation": ROOT / "data/final/review_combined/validation.jsonl",
    "review_test": ROOT / "data/final/review_combined/test.jsonl",
    "rag_corpus": ROOT / "data/final/rag/rag_corpus.jsonl",
}

METADATA_FILES = [
    ROOT / "data/final/metadata/review_combined_summary.json",
    ROOT / "data/final/metadata/owasp_cheatsheets_rag_summary.json",
    ROOT / "data/final/metadata/codexglue_normalization_summary.json",
    ROOT / "data/final/metadata/owasp_python_normalization_summary.json",
]


README = """---
license: other
language:
- en
task_categories:
- text-classification
- question-answering
- text-generation
- feature-extraction
pretty_name: CodeSecAudit-RAG
size_categories:
- 10K<n<100K
tags:
- code-security
- vulnerability-detection
- rag
- secure-coding
- owasp
- cwe
- code-review
- cybersecurity
---

# CodeSecAudit-RAG

CodeSecAudit-RAG is a curated defensive dataset for building an Enterprise Code Review and Security Auditor Agent. It combines vulnerability-detection examples with a retrieval-ready secure-coding knowledge corpus.

The dataset is designed for practical AIML and MLOps workflows such as vulnerability detection, security review explanation, and RAG-based secure coding guidance retrieval.

## Dataset Components

### 1. Review Dataset

Files:

- `review_combined/train.jsonl.gz`
- `review_combined/validation.jsonl.gz`
- `review_combined/test.jsonl.gz`

Total records: 28,548

Sources:

- CodeXGLUE Defect Detection: large binary vulnerable/non-vulnerable C examples
- OWASP Benchmark Python: CWE-labeled Python benchmark examples

The review dataset supports binary vulnerability detection and CWE-aware security review.

### 2. RAG Corpus

File:

- `rag/rag_corpus.jsonl.gz`

Total chunks: 2,833

Source:

- OWASP Cheat Sheet Series

The RAG corpus contains secure coding guidance chunks for retrieval-augmented generation. It covers topics such as SQL injection prevention, XSS, code injection, OS command injection, authentication, authorization, secrets management, file upload security, SSRF, deserialization, and cryptographic failures.

## Intended Use

This dataset is intended for defensive security research and educational AI engineering projects, including:

- vulnerability detection
- secure code review
- security explanation generation
- RAG-based secure coding assistants
- MLOps and dataset engineering demonstrations

## Not Intended For

This dataset is not intended for building offensive exploitation tools, malware generation systems, or automated attack systems. The dataset should be used for defensive code review, secure coding education, and vulnerability remediation workflows.

## Schema

Review records include:

- `id`
- `source_name`
- `source_type`
- `source_split`
- `original_id`
- `language`
- `framework`
- `task`
- `cwe_id`
- `owasp_category`
- `severity`
- `is_vulnerable`
- `vulnerability_name`
- `input_code`
- `fixed_code`
- `explanation`
- `secure_pattern`
- `tags`
- `metadata`

RAG records include:

- `id`
- `source_name`
- `source_type`
- `doc_type`
- `source_file`
- `title`
- `section_title`
- `chunk_index`
- `language`
- `framework`
- `task`
- `cwe_id`
- `vulnerability_name`
- `owasp_category`
- `content`
- `positive_pattern`
- `negative_pattern`
- `tags`
- `metadata`

## Dataset Statistics

Review dataset:

| Split | Records |
|---|---:|
| Train | 22,827 |
| Validation | 2,846 |
| Test | 2,875 |
| Total | 28,548 |

RAG corpus:

| Component | Count |
|---|---:|
| RAG chunks | 2,833 |
| Covered CWE types | 16 |
| Average chunk size | ~869 characters |

## Loading Example

```python
from datasets import load_dataset

review = load_dataset(
    "json",
    data_files={
        "train": "review_combined/train.jsonl.gz",
        "validation": "review_combined/validation.jsonl.gz",
        "test": "review_combined/test.jsonl.gz",
    }
)

rag = load_dataset(
    "json",
    data_files={"train": "rag/rag_corpus.jsonl.gz"}
)
```

## Limitations

CodeXGLUE provides binary labels but does not provide exact CWE labels, so those records use `cwe_id: unknown`. OWASP Benchmark Python provides stronger CWE-specific labels. The RAG corpus is documentation-derived and should be used as retrieval context rather than ground-truth model labels.

## Source and License Notice

This is a curated derivative dataset built from public security datasets and documentation. Users should review the original source licenses before redistribution or commercial use. The dataset card intentionally uses `license: other` because the final package combines sources with different licensing terms.

## Author

Created and curated by Om Choksi.
"""

LICENSE_NOTICE = """# License and Source Notice

CodeSecAudit-RAG is a curated derivative dataset created from multiple public sources.

## Included Sources

1. CodeXGLUE Defect Detection

   * Used for binary vulnerable/non-vulnerable code examples.
   * CWE labels are not provided by this source in the normalized records.

2. OWASP Benchmark Python

   * Used for CWE-labeled Python security benchmark examples.

3. OWASP Cheat Sheet Series

   * Used for retrieval-ready secure coding guidance chunks.

## License Warning

This release uses `license: other` because the package combines sources with different licensing terms. Before commercial use or redistribution, review the license terms of every upstream source.

## Responsible Use

This dataset is intended for defensive security, secure coding education, vulnerability detection, and code review automation. It should not be used for offensive exploitation, malware generation, or unauthorized testing.
"""

def gzip_copy(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open("rb") as f_in:
        with gzip.open(dst, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

def count_jsonl_gz(path: Path) -> int:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())

def main():
    print("Creating release package")
    print("=" * 70)

    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)

    (RELEASE_DIR / "review_combined").mkdir(parents=True)
    (RELEASE_DIR / "rag").mkdir(parents=True)
    (RELEASE_DIR / "metadata").mkdir(parents=True)

    for name, path in INPUTS.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing required input: {path}")

    gzip_copy(INPUTS["review_train"], RELEASE_DIR / "review_combined/train.jsonl.gz")
    gzip_copy(INPUTS["review_validation"], RELEASE_DIR / "review_combined/validation.jsonl.gz")
    gzip_copy(INPUTS["review_test"], RELEASE_DIR / "review_combined/test.jsonl.gz")
    gzip_copy(INPUTS["rag_corpus"], RELEASE_DIR / "rag/rag_corpus.jsonl.gz")

    for meta in METADATA_FILES:
        if meta.exists():
            shutil.copy2(meta, RELEASE_DIR / "metadata" / meta.name)

    (RELEASE_DIR / "README.md").write_text(README, encoding="utf-8")
    (RELEASE_DIR / "DATASET_CARD.md").write_text(README, encoding="utf-8")
    (RELEASE_DIR / "LICENSE_NOTICE.md").write_text(LICENSE_NOTICE, encoding="utf-8")

    kaggle_metadata = {
        "title": "CodeSecAudit-RAG",
        "subtitle": "Defensive code security review dataset with RAG-ready secure coding guidance",
        "description": (
            "CodeSecAudit-RAG is a curated defensive dataset for building an Enterprise Code Review "
            "and Security Auditor Agent. It includes a combined vulnerability review dataset and an "
            "OWASP Cheat Sheet based RAG corpus. Intended for secure coding education, vulnerability "
            "detection, security review explanation, and defensive AI engineering workflows."
        ),
        "id": "OMCHOKSI04/codesec-audit-rag",
        "licenses": [{"name": "other"}],
        "keywords": [
            "cybersecurity",
            "code",
            "security",
            "rag",
            "machine learning",
            "nlp",
            "artificial intelligence"
        ],
        "resources": [
            {
                "path": "review_combined/train.jsonl.gz",
                "description": "Training split for vulnerability detection and security review."
            },
            {
                "path": "review_combined/validation.jsonl.gz",
                "description": "Validation split for vulnerability detection and security review."
            },
            {
                "path": "review_combined/test.jsonl.gz",
                "description": "Test split for vulnerability detection and security review."
            },
            {
                "path": "rag/rag_corpus.jsonl.gz",
                "description": "RAG-ready secure coding guidance corpus from OWASP Cheat Sheet Series."
            },
            {
                "path": "README.md",
                "description": "Dataset card and usage documentation."
            },
            {
                "path": "LICENSE_NOTICE.md",
                "description": "Source and license transparency notice."
            }
        ]
    }

    (RELEASE_DIR / "dataset-metadata.json").write_text(
        json.dumps(kaggle_metadata, indent=2),
        encoding="utf-8"
    )

    release_summary = {
        "dataset": "CodeSecAudit-RAG",
        "version": VERSION,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "files": {
            "review_combined/train.jsonl.gz": count_jsonl_gz(RELEASE_DIR / "review_combined/train.jsonl.gz"),
            "review_combined/validation.jsonl.gz": count_jsonl_gz(RELEASE_DIR / "review_combined/validation.jsonl.gz"),
            "review_combined/test.jsonl.gz": count_jsonl_gz(RELEASE_DIR / "review_combined/test.jsonl.gz"),
            "rag/rag_corpus.jsonl.gz": count_jsonl_gz(RELEASE_DIR / "rag/rag_corpus.jsonl.gz"),
        }
    }

    (RELEASE_DIR / "metadata/release_summary.json").write_text(
        json.dumps(release_summary, indent=2),
        encoding="utf-8"
    )

    print(f"Release folder created: {RELEASE_DIR.relative_to(ROOT)}")
    print(json.dumps(release_summary, indent=2))

if __name__ == "__main__":
    main()
