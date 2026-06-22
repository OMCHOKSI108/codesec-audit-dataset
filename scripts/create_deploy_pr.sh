#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

BRANCH="deploy/hf-rag-service"
COMMIT_MSG="deploy: prepare Hugging Face RAG service"
PR_TITLE="Deploy Hugging Face RAG service"

PR_BODY="## Summary

- Fixes RAG health internals (public properties, no direct _embeddings access)
- Adds HF Space Docker README metadata (YAML frontmatter, security warnings)
- Adds HF Space deployment script (huggingface_hub + git-push fallback)
- Adds remote RAG verification scripts (service health + main API integration)
- Adds deployment docs (automated deploy, manual git push, local Docker test)

## Verification

- \`python scripts/prepare_hf_rag_space.py\`
- \`python -m compileall rag_service scripts\`
- \`python scripts/evaluate_reviewer.py\`
- \`python scripts/review_code.py --code \"eval(user_input)\" --json\`
"

echo "=== CodeSecAudit AI — Deploy RAG Service PR ==="
echo ""

# Check gh auth
if ! gh auth status 2>&1; then
    echo "ERROR: gh is not authenticated. Run 'gh auth login' first."
    exit 1
fi

# Check for git repo
if ! git rev-parse --is-inside-work-tree 2>/dev/null; then
    echo "ERROR: Not a git repository. Initialize git first:"
    echo "  git init"
    echo "  git remote add origin <your-repo-url>"
    echo "  git add . && git commit -m 'initial commit'"
    exit 1
fi

# Check for uncommitted changes
if git diff --quiet && git diff --cached --quiet; then
    echo "No changes to commit. Run the deployment scripts first."
    exit 0
fi

# Create and switch to branch
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "Branch $BRANCH already exists, switching to it"
    git checkout "$BRANCH"
else
    echo "Creating branch: $BRANCH"
    git checkout -b "$BRANCH"
fi

# Stage specific files
git add \
    rag_service/index.py \
    rag_service/main.py \
    deploy/huggingface-rag/README.md \
    scripts/prepare_hf_rag_space.py \
    scripts/deploy_hf_rag_space.py \
    scripts/check_remote_rag_service.py \
    scripts/check_main_api_remote_rag.py \
    scripts/create_deploy_pr.sh \
    scripts/test_remote_rag_client.py \
    scripts/test_rag_service.py \
    docs/rag_service.md \
    .gitignore \
    2>/dev/null || true

# Commit
if git diff --cached --quiet; then
    echo "No staged changes after filtering."
    echo "Stage all changes with 'git add .' or modify the file list in this script."
    exit 0
fi

echo "Committing changes..."
git commit -m "$COMMIT_MSG"

# Push
echo "Pushing branch: $BRANCH"
git push -u origin "$BRANCH" 2>/dev/null || {
    echo "WARNING: Push failed. You may need to set remote:"
    echo "  git remote add origin <your-repo-url>"
    exit 1
}

# Create PR
echo "Creating PR..."
gh pr create \
    --title "$PR_TITLE" \
    --body "$PR_BODY" \
    --base main \
    --head "$BRANCH"

echo ""
echo "Done! PR created for branch: $BRANCH"
