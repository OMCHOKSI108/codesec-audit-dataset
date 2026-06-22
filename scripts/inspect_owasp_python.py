from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/owasp_benchmark_python"

print("OWASP Benchmark Python Inspection")
print("=" * 70)
print(f"Raw path: {RAW_DIR}")
print(f"Exists: {RAW_DIR.exists()}")

print("\nTop-level folders/files:")
for p in sorted(RAW_DIR.iterdir()):
    print(f"- {p.name}/" if p.is_dir() else f"- {p.name}")

testcode_dir = RAW_DIR / "testcode"
py_files = list(testcode_dir.rglob("*.py")) if testcode_dir.exists() else []

print("\nPython test files:")
print(f"Count: {len(py_files)}")

if py_files:
    print("Sample files:")
    for p in py_files[:10]:
        print(f"- {p.relative_to(RAW_DIR)}")

print("\nCandidate metadata/result files:")
candidate_exts = {".csv", ".json", ".yaml", ".yml", ".xml", ".txt"}
candidate_files = [
    p for p in RAW_DIR.rglob("*")
    if p.is_file() and p.suffix.lower() in candidate_exts
]

for p in sorted(candidate_files)[:100]:
    rel = p.relative_to(RAW_DIR)
    size_kb = p.stat().st_size / 1024
    print(f"- {rel} ({size_kb:.1f} KB)")

print("\nCSV previews:")
csv_files = [p for p in candidate_files if p.suffix.lower() == ".csv"]

for csv_path in csv_files[:20]:
    print("\n" + "-" * 70)
    print(f"CSV: {csv_path.relative_to(RAW_DIR)}")

    try:
        with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            print(f"Columns: {reader.fieldnames}")

            for i, row in enumerate(reader):
                print("First row:")
                print(json.dumps(row, indent=2)[:1500])
                break
    except Exception as exc:
        print(f"Could not read CSV: {exc}")
