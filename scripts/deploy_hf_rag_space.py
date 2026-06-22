"""Deploy the RAG service package to a Hugging Face Space."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "huggingface-rag-space"

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN") or ""
SPACE_ID = os.getenv("HF_RAG_SPACE_ID", "OMCHOKSI108/codesec-rag-service")
SPACE_PRIVATE = os.getenv("HF_SPACE_PRIVATE", "").lower() in ("1", "true", "yes")
RAG_API_KEY = os.getenv("RAG_API_KEY", "")
RAG_DATASET_REPO = os.getenv("RAG_DATASET_REPO", "OMCHOKSI108/CodeSecAudit-RAG")
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RAG_CORPUS_FILE = os.getenv("RAG_CORPUS_FILE", "rag/rag_corpus.jsonl.gz")

SECRETS = {
    "RAG_API_KEY": RAG_API_KEY,
    "RAG_DATASET_REPO": RAG_DATASET_REPO,
    "RAG_CORPUS_FILE": RAG_CORPUS_FILE,
    "RAG_EMBEDDING_MODEL": RAG_EMBEDDING_MODEL,
}


def step(msg: str):
    print(f"\n=== {msg} ===")


def run_prepare():
    step("Packaging RAG service files")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "prepare_hf_rag_space.py")],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        print("ERROR: prepare_hf_rag_space.py failed")
        sys.exit(1)
    print("Package ready at", DIST)


def deploy_hf():
    if not HF_TOKEN:
        print("ERROR: HF_TOKEN or HUGGINGFACE_TOKEN not set")
        return False

    try:
        from huggingface_hub import HfApi

        api = HfApi(token=HF_TOKEN)
    except ImportError:
        print("WARNING: huggingface_hub not installed, falling back to git-push instructions")
        return False

    create_repo = True
    try:
        info = api.space_info(SPACE_ID)
        print(f"Space {SPACE_ID} already exists (runtime: {info.runtime.phase if info.runtime else 'unknown'})")
        create_repo = False
    except Exception:
        print(f"Space {SPACE_ID} does not exist, will create")

    if create_repo:
        step(f"Creating Space: {SPACE_ID}")
        try:
            api.create_repo(
                repo_id=SPACE_ID,
                repo_type="space",
                space_sdk="docker",
                private=SPACE_PRIVATE,
                exist_ok=True,
            )
            print(f"Space created: https://huggingface.co/spaces/{SPACE_ID}")
        except Exception as e:
            print(f"ERROR: Failed to create space: {e}")
            return False

    step("Uploading package files")
    try:
        api.upload_folder(
            folder_path=str(DIST),
            repo_id=SPACE_ID,
            repo_type="space",
            commit_message="deploy CodeSecAudit RAG service",
        )
        print("Files uploaded successfully")
    except Exception as e:
        print(f"ERROR: Upload failed: {e}")
        return False

    step("Setting Space secrets")
    secret_added = 0
    for key, value in SECRETS.items():
        if not value:
            print(f"  SKIP: {key}=<empty> (not set)")
            continue
        try:
            api.add_space_secret(repo_id=SPACE_ID, key=key, value=value)
            print(f"  SET: {key}=<configured>")
            secret_added += 1
        except AttributeError:
            print("  WARNING: add_space_secret not available in this huggingface_hub version")
            print("  Manual steps required (see below)")
            break
        except Exception as e:
            print(f"  FAIL: {key}: {e}")

    if secret_added > 0:
        print(f"  {secret_added} secret(s) set successfully")
    else:
        print()
        print("To set secrets manually:")
        print(f"  1. Go to https://huggingface.co/spaces/{SPACE_ID}/settings")
        for key in SECRETS:
            print(f"  2. Add secret: {key}")
        print()

    step("Restarting Space")
    try:
        api.restart_space(repo_id=SPACE_ID)
        print("Space restart triggered")
    except Exception as e:
        print(f"  WARNING: Could not restart space: {e}")
        print("  Restart manually from the Space Settings page.")

    return True


def print_git_push_instructions():
    print()
    print("=" * 70)
    print("GIT PUSH FALLBACK INSTRUCTIONS")
    print("=" * 70)
    print()
    print("To deploy via git push instead:")
    print()
    print(f"  cd {DIST}")
    print("  git init")
    print(f"  git remote add origin https://huggingface.co/spaces/{SPACE_ID}")
    print('  git add .')
    print('  git commit -m "deploy CodeSecAudit RAG service"')
    print("  git push origin main")
    print()
    print("Then add secrets at https://huggingface.co/spaces/{SPACE_ID}/settings")
    for key in SECRETS:
        print(f"  - {key}")
    print()


def print_urls():
    print()
    print("=" * 70)
    print("DEPLOY SUMMARY")
    print("=" * 70)
    print()
    print(f"  Space page: https://huggingface.co/spaces/{SPACE_ID}")
    space_slug = SPACE_ID.replace("/", "-")
    print(f"  Direct URL: https://{space_slug}.hf.space")
    print()
    print("  Verify health:")
    print(f"    curl https://{space_slug}.hf.space/health")
    print()
    print("  Verify search:")
    print(f'    curl -X POST https://{space_slug}.hf.space/rag/search \\')
    print('      -H "Content-Type: application/json" \\')
    print('      -d \'{"query":"sql injection prepared statements","top_k":3}\'')


def main():
    print("=" * 70)
    print("CodeSecAudit RAG Service — Hugging Face Space Deployment")
    print("=" * 70)

    if not HF_TOKEN:
        print("WARNING: No HF_TOKEN set — will print git-push instructions instead.")
        print()

    run_prepare()
    deployed = deploy_hf()
    if not deployed:
        print_git_push_instructions()
    print_urls()

    if not deployed and not HF_TOKEN:
        sys.exit(0)


if __name__ == "__main__":
    main()
