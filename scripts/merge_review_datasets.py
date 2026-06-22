import json
import random
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]

CODEX_DIR = ROOT / "data/final/review"
OWASP_PATH = ROOT / "data/processed/owasp_benchmark_python/owasp_python_review.jsonl"

OUT_DIR = ROOT / "data/final/review_combined"
META_DIR = ROOT / "data/final/metadata"

OUT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_PATH = META_DIR / "review_combined_summary.json"

SEED = 42
random.seed(SEED)


def read_jsonl(path: Path):
    records = []
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    return records


def write_jsonl(path: Path, records):
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def split_owasp_records(records):
    groups = defaultdict(list)

    for record in records:
        key = (
            record.get("cwe_id", "unknown"),
            str(record.get("is_vulnerable", "unknown"))
        )
        groups[key].append(record)

    train, validation, test = [], [], []

    for key, group in groups.items():
        random.shuffle(group)
        n = len(group)

        train_n = int(n * 0.8)
        val_n = int(n * 0.1)

        if n >= 3 and val_n == 0:
            val_n = 1

        test_n_start = train_n + val_n

        train.extend(group[:train_n])
        validation.extend(group[train_n:test_n_start])
        test.extend(group[test_n_start:])

    random.shuffle(train)
    random.shuffle(validation)
    random.shuffle(test)

    return {
        "train": train,
        "validation": validation,
        "test": test,
    }


def add_merge_metadata(records, merged_split):
    now = datetime.utcnow().isoformat() + "Z"

    for r in records:
        metadata = r.setdefault("metadata", {})
        metadata["combined_dataset_split"] = merged_split
        metadata["combined_at"] = now

    return records


def summarize(records):
    return {
        "total": len(records),
        "source_counts": dict(Counter(r.get("source_name", "unknown") for r in records)),
        "language_counts": dict(Counter(r.get("language", "unknown") for r in records)),
        "task_counts": dict(Counter(r.get("task", "unknown") for r in records)),
        "vulnerable_counts": dict(Counter(str(r.get("is_vulnerable", "unknown")) for r in records)),
        "top_cwe_counts": dict(Counter(r.get("cwe_id", "unknown") for r in records).most_common(30)),
        "top_vulnerability_names": dict(Counter(r.get("vulnerability_name", "unknown") for r in records).most_common(30)),
    }


def main():
    print("Merging review datasets")
    print("=" * 70)

    codex = {
        "train": read_jsonl(CODEX_DIR / "train.jsonl"),
        "validation": read_jsonl(CODEX_DIR / "validation.jsonl"),
        "test": read_jsonl(CODEX_DIR / "test.jsonl"),
    }

    owasp_records = read_jsonl(OWASP_PATH)
    owasp_split = split_owasp_records(owasp_records)

    combined = {}

    for split in ["train", "validation", "test"]:
        codex_records = codex[split]
        owasp_records_for_split = owasp_split[split]

        merged = codex_records + owasp_records_for_split
        random.shuffle(merged)

        merged = add_merge_metadata(merged, split)
        combined[split] = merged

        out_path = OUT_DIR / f"{split}.jsonl"
        write_jsonl(out_path, merged)

        print(f"[OK] {split}: {len(merged)} records")
        print(f"     CodeXGLUE: {len(codex_records)}")
        print(f"     OWASP Python: {len(owasp_records_for_split)}")
        print(f"     Output: {out_path.relative_to(ROOT)}")

    summary = {
        "dataset_name": "CodeSecAudit Review Combined",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "seed": SEED,
        "inputs": {
            "codexglue": str(CODEX_DIR.relative_to(ROOT)),
            "owasp_python": str(OWASP_PATH.relative_to(ROOT)),
        },
        "outputs": {
            split: str((OUT_DIR / f"{split}.jsonl").relative_to(ROOT))
            for split in ["train", "validation", "test"]
        },
        "splits": {
            split: summarize(records)
            for split, records in combined.items()
        }
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("=" * 70)
    print(f"Summary saved to: {SUMMARY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
