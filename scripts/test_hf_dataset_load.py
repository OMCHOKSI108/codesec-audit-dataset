from datasets import load_dataset
from collections import Counter

REPO_ID = "OMCHOKSI108/CodeSecAudit-RAG"

def check_schema(records, name):
    required_keys = {
        "id", "source_name", "source_type", "task", "cwe_id",
        "vulnerability_name", "is_vulnerable" if "is_vulnerable" in (records[0] if records else {}) else "content"
    }
    all_keys = set()
    for r in records:
        all_keys.update(r.keys())

    missing = required_keys - all_keys
    print(f"  Records: {len(records)}")
    print(f"  Keys ({len(all_keys)}): {sorted(all_keys)[:15]}...")
    print(f"  Missing required keys: {missing if missing else 'None'}")

    return len(records)

def main():
    print("=" * 70)
    print("Phase 3A: Testing Hugging Face Dataset Load")
    print(f"Repo: {REPO_ID}")
    print("=" * 70)

    print("\n--- Loading review_combined ---")
    review = load_dataset(
        "json",
        data_files={
            "train": f"https://huggingface.co/datasets/{REPO_ID}/resolve/main/review_combined/train.jsonl.gz",
            "validation": f"https://huggingface.co/datasets/{REPO_ID}/resolve/main/review_combined/validation.jsonl.gz",
            "test": f"https://huggingface.co/datasets/{REPO_ID}/resolve/main/review_combined/test.jsonl.gz",
        }
    )

    total = 0
    for split in ["train", "validation", "test"]:
        ds = review[split]
        cwe_counts = Counter(ds["cwe_id"])
        vuln_counts = Counter(ds["is_vulnerable"])
        lang_counts = Counter(ds["language"])

        n = check_schema(ds, split)
        total += n
        print(f"  Languages: {dict(lang_counts.most_common(3))}")
        print(f"  Top CWEs: {cwe_counts.most_common(5)}")
        print(f"  Vulnerable: {dict(vuln_counts)}")
        print(f"  Sample id: {ds[0]['id']}")
        print()

    print(f"Total review records: {total}")

    print("\n--- Loading rag_corpus ---")
    rag = load_dataset(
        "json",
        data_files={
            "train": f"https://huggingface.co/datasets/{REPO_ID}/resolve/main/rag/rag_corpus.jsonl.gz",
        }
    )["train"]

    n = check_schema(rag, "rag_corpus")
    cwe_counts = Counter(rag["cwe_id"])
    print(f"  Top CWEs: {cwe_counts.most_common(5)}")
    print(f"  Sample id: {rag[0]['id']}")
    print(f"  Sample title: {rag[0]['title']}")

    print("\n" + "=" * 70)
    print("Dataset load test: PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
