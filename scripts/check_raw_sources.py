from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sources = {
    "CodeXGLUE Defect Detection": ROOT / "data/raw/codexglue_defect_detection",
    "NIST Juliet C/C++": ROOT / "data/raw/nist_juliet_c_cpp",
    "NIST Juliet Java": ROOT / "data/raw/nist_juliet_java",
    "OWASP Benchmark Java": ROOT / "data/raw/owasp_benchmark_java",
    "OWASP Benchmark Python": ROOT / "data/raw/owasp_benchmark_python",
    "OWASP Cheat Sheet Series": ROOT / "data/raw/owasp_cheatsheet_series",
}

print("Raw Source Verification")
print("=" * 60)

all_ok = True

for name, path in sources.items():
    exists = path.exists()
    status = "OK" if exists else "MISSING"
    print(f"{status:8} | {name:30} | {path}")

    if not exists:
        all_ok = False

print("=" * 60)

if all_ok:
    print("All expected raw sources are present.")
else:
    print("Some sources are missing.")