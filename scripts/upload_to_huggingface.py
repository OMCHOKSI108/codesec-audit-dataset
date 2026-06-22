import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, create_repo

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

RELEASE_DIR = ROOT / "release/codesec-audit-rag-v0.1.0"

HF_TOKEN = (
    os.getenv("HF_TOKEN")
    or os.getenv("HUGGINGFACE_TOKEN")
    or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    or os.getenv("HUGGINGFACE")
)

REPO_ID = os.getenv("HF_DATASET_REPO_ID", "OMCHOKSI04/CodeSecAudit-RAG")

if not HF_TOKEN:
    raise RuntimeError(
        "Missing Hugging Face token. Add one of these to .env: "
        "HF_TOKEN, HUGGINGFACE_TOKEN, HUGGINGFACEHUB_API_TOKEN, or HUGGINGFACE"
    )

if not RELEASE_DIR.exists():
    raise FileNotFoundError(f"Missing release folder: {RELEASE_DIR}")

api = HfApi(token=HF_TOKEN)

print(f"Creating or reusing Hugging Face dataset repo: {REPO_ID}")
create_repo(
    repo_id=REPO_ID,
    repo_type="dataset",
    token=HF_TOKEN,
    private=False,
    exist_ok=True,
)

print("Uploading release folder to Hugging Face...")
api.upload_folder(
    folder_path=str(RELEASE_DIR),
    repo_id=REPO_ID,
    repo_type="dataset",
    token=HF_TOKEN,
    commit_message="Upload CodeSecAudit-RAG v0.1.0 dataset release",
)

print("Done.")
print(f"Hugging Face dataset repo: https://huggingface.co/datasets/{REPO_ID}")
