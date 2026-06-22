import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data/raw/codexglue_defect_detection"
OUT_DIR = ROOT / "data/final/review"
META_DIR = ROOT / "data/final/metadata"

OUT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"[SKIP] Invalid JSON at {path}:{line_no} -> {exc}")


def normalize_record(record: dict, split: str, index: int) -> dict:
    code = record.get("func") or record.get("code") or ""
    target = record.get("target")

    is_vulnerable = bool(target == 1)

    original_id = record.get("id")
    project = record.get("project")
    commit_id = record.get("commit_id")

    return {
        "id": f"codexglue_{split}_{index:06d}",
        "source_name": "CodeXGLUE Defect Detection",
        "source_type": "public_dataset",
        "source_split": split,
        "original_id": original_id,
        "language": "c",
        "framework": "generic",
        "task": "vulnerability_detection",
        "cwe_id": "unknown",
        "owasp_category": "unknown",
        "severity": "unknown",
        "is_vulnerable": is_vulnerable,
        "vulnerability_name": "unknown_defect_or_vulnerability",
        "input_code": code,
        "fixed_code": "",
        "explanation": (
            "This example comes from CodeXGLUE defect detection. "
            "The original dataset provides a binary target label but does not provide a specific CWE label or secure fix."
        ),
        "secure_pattern": "",
        "tags": [
            "codexglue",
            "defect-detection",
            "c-language",
            "binary-label"
        ],
        "metadata": {
            "original_target": target,
            "project": project,
            "commit_id": commit_id,
            "normalized_at": datetime.utcnow().isoformat() + "Z"
        }
    }


def process_split(split: str):
    in_path = RAW_DIR / f"{split}.jsonl"
    out_path = OUT_DIR / f"{split}.jsonl"

    if not in_path.exists():
        print(f"[MISSING] {in_path}")
        return {
            "split": split,
            "status": "missing",
            "total": 0,
            "vulnerable": 0,
            "clean": 0
        }

    total = 0
    vulnerable = 0
    clean = 0

    with out_path.open("w", encoding="utf-8") as out:
        for index, record in enumerate(read_jsonl(in_path), start=1):
            normalized = normalize_record(record, split, index)

            if normalized["is_vulnerable"]:
                vulnerable += 1
            else:
                clean += 1

            total += 1
            out.write(json.dumps(normalized, ensure_ascii=False) + "\n")

    print(f"[OK] {split}: {total} records -> {out_path}")
    print(f"     vulnerable={vulnerable}, clean={clean}")

    return {
        "split": split,
        "status": "ok",
        "total": total,
        "vulnerable": vulnerable,
        "clean": clean,
        "output_path": str(out_path.relative_to(ROOT))
    }


def main():
    print("Normalizing CodeXGLUE Defect Detection")
    print("=" * 70)

    summary = {
        "source": "CodeXGLUE Defect Detection",
        "task": "vulnerability_detection",
        "language": "c",
        "splits": []
    }

    for split in ["train", "validation", "test"]:
        split_summary = process_split(split)
        summary["splits"].append(split_summary)

    summary_path = META_DIR / "codexglue_normalization_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=" * 70)
    print(f"Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()
