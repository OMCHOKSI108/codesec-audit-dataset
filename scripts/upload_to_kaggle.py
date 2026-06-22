import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

RELEASE_DIR = ROOT / "release/codesec-audit-rag-v0.1.0"

username = os.getenv("KAGGLE_USERNAME")
key = os.getenv("KAGGLE_KEY") or os.getenv("KAGGLE_API_TOKEN")

if not username or not key:
    raise RuntimeError(
        "Missing Kaggle credentials. Add KAGGLE_USERNAME and KAGGLE_KEY or KAGGLE_API_TOKEN to .env."
    )

if not RELEASE_DIR.exists():
    raise FileNotFoundError(f"Missing release folder: {RELEASE_DIR}")

metadata_path = RELEASE_DIR / "dataset-metadata.json"
if not metadata_path.exists():
    raise FileNotFoundError(f"Missing Kaggle metadata file: {metadata_path}")

env = os.environ.copy()
env["KAGGLE_USERNAME"] = username
env["KAGGLE_API_TOKEN"] = key

print("Checking whether Kaggle dataset already exists...")
dataset_id = f"{username}/codesec-audit-rag"

list_cmd = ["kaggle", "datasets", "files", dataset_id]
exists = subprocess.run(
    list_cmd,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

if exists.returncode == 0:
    print("Dataset exists. Creating a new version...")
    cmd = [
        "kaggle",
        "datasets",
        "version",
        "-p",
        str(RELEASE_DIR),
        "-m",
        "Update CodeSecAudit-RAG v0.1.0 release",
        "-r",
        "zip",
    ]
else:
    print("Dataset does not exist or is not accessible. Creating new private dataset...")
    cmd = [
        "kaggle",
        "datasets",
        "create",
        "-p",
        str(RELEASE_DIR),
        "-r",
        "zip",
    ]

print("Running:", " ".join(cmd[:-1]), "<release_dir>")
result = subprocess.run(cmd, env=env, text=True)

if result.returncode != 0:
    raise SystemExit(result.returncode)

print("Done.")
print(f"Kaggle dataset target: https://www.kaggle.com/datasets/{dataset_id}")
