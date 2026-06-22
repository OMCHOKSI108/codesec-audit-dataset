# GitHub Action MVP — CodeSecAudit AI Review

## What Step 2 Does

Adds a GitHub Action that automatically reviews pull requests for security issues
using the `review_engine` package. When a PR is opened, synchronized, or reopened,
the action runs rule-based static analysis on changed code files and posts a
summary comment.

## Files Added

| File | Purpose |
|------|---------|
| `.github/workflows/codesec-audit.yml` | Workflow definition — triggers on PR, runs review |
| `scripts/github_pr_review.py` | Script that reads PR event, reviews files, posts comment |
| `docs/github_action_mvp.md` | This documentation |

## How the Workflow Triggers

Triggers on:

```
pull_request:
  types: [opened, synchronize, reopened]
```

Permissions:

- `contents: read` — to checkout the repo
- `pull-requests: write` — to post/update PR comments

## Supported Extensions

- `.py`
- `.js`, `.jsx`
- `.ts`, `.tsx`

## Ignored Paths

```
node_modules/   dist/           build/
.venv/          venv/           data/
release/        notebooks/      .ipynb_checkpoints/
__pycache__/    *.min.js        *.lock
package-lock.json               pnpm-lock.yaml
yarn.lock
```

## Step 3A Update (Line Number Detection)

The dry-run and summary report now include file/line locations for detected issues.

The markdown table uses a `Location` column showing `path/to/file.py:42` for each
detected issue. Inline GitHub review comments are still deferred to Step 3B.

## Step 3B Update (Inline Comments)

- The summary comment behavior is preserved — it is still created or updated.
- **Inline comments** are now posted directly on PR changed lines when:
  - The issue line is confirmed as an **added line** in the PR diff/patch.
  - The line has not already received an inline comment (duplicate detection via hidden fingerprint).
  - The total does not exceed the cap (`MAX_INLINE_COMMENTS = 10`).
- Non-commentable issues (lines not in diff) remain in the summary table only.
- The dry-run output now includes an **Inline Comment Plan** section showing which
  issues would receive inline comments and why.
- Patch parsing works by extracting added new-file line numbers from the unified
  diff `@@` hunk headers and `+` lines.

## Current Limitations

- **`use_rag=False`** in CI — avoids downloading the embedding model and ChromaDB
  index on every workflow run. RAG retrieval will be enabled in a future iteration
  after caching is set up.
- **No blocking mode** — the action always exits 0. Issues do not fail the build.
- **No paid LLMs** — all detection is rule-based, all fixes are template-based.

## Why `use_rag=False` in CI MVP

The RAG index requires:
1. Downloading `sentence-transformers/all-MiniLM-L6-v2` (~80 MB model)
2. Loading a 25 MB ChromaDB SQLite database

Both add significant startup time on every CI run. For the initial MVP, the
7 rule-based detectors are sufficient to demonstrate value. RAG can be enabled
later with GitHub Actions caching (`actions/cache`) for the model and index.

## How to Test Locally

### Test with explicit files:

```bash
pip install -e .
python scripts/github_pr_review.py --files /tmp/test.py --dry-run
```

### Test with recent git diff:

```bash
pip install -e .
python scripts/github_pr_review.py --dry-run
```

The `--dry-run` flag prints the markdown report to the terminal instead of
posting it to GitHub. It does not call the GitHub API.
