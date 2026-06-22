# GitHub Action — CodeSecAudit AI Review

## Workflow File

`.github/workflows/codesec-audit.yml`

```yaml
name: CodeSecAudit AI Review
on:
  pull_request:
    types: [opened, synchronize, reopened]
permissions:
  contents: read
  pull-requests: write
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install package
        run: |
          pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Run security review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_EVENT_PATH: ${{ github.event_path }}
          GITHUB_SHA: ${{ github.sha }}
          GITHUB_BASE_REF: ${{ github.base_ref }}
          GITHUB_HEAD_REF: ${{ github.head_ref }}
        run: python scripts/github_pr_review.py
```

## Triggers

- `opened` — new pull request
- `synchronize` — new commits pushed to the PR branch
- `reopened` — closed PR reopened

## Permissions

- `contents: read` — to checkout the repository
- `pull-requests: write` — to post and update PR comments

## Supported File Types

- `.py`, `.js`, `.jsx`, `.ts`, `.tsx`

## Ignored Paths

```
node_modules/   dist/           build/
.venv/          venv/           data/
release/        notebooks/      .ipynb_checkpoints/
__pycache__/    *.min.js        *.lock
package-lock.json               pnpm-lock.yaml
yarn.lock
```

Files larger than 200 KB are also skipped.

## Output

### Summary Comment

After the action completes, a PR comment is posted containing:

- **Verdict** (APPROVE / WARNING / REQUEST_CHANGES)
- **Risk score** (0–100)
- **Issues Found** table with columns: Location, CWE, Severity, Issue, Suggested Fix
- **Notes** section with engine version, RAG status, and limits info

### Inline Comments

Inline comments are posted directly on vulnerable added lines in the PR diff:

- Only on **added lines** (green `+` lines in the diff)
- Deduplication: same `path + line + CWE` is skipped
- Cap: maximum **10 inline comments** per PR
- Non-commentable issues (not in diff) remain in the summary table only

### Fingerprint Deduplication

Each inline comment includes a hidden fingerprint. If a comment with the same path, line number, and CWE already exists, the new comment is skipped. This prevents duplicate comments when new commits are pushed.

## Dry Run

Test locally without calling the GitHub API:

```bash
python scripts/github_pr_review.py --files examples/vulnerable_pr_demo.py --dry-run
```

The `--dry-run` flag:
- Prints the summary markdown to the terminal
- Shows the Inline Comment Plan table
- Does not call any GitHub API
- Does not save to the review database (use `--save` to save)

```bash
# Dry run with recent git diff
python scripts/github_pr_review.py --dry-run

# Dry run with save to review DB
python scripts/github_pr_review.py --dry-run --files examples/vulnerable_pr_demo.py --save
```

## Limitations

- **`use_rag=False` in CI** — RAG retrieval is disabled in the GitHub Action to avoid downloading the embedding model (~80 MB) and ChromaDB index on every run. Will be enabled after `actions/cache` is configured.
- **Non-blocking** — the action always exits 0. Issues do not fail the build or block merging.
- **No paid LLMs** — all detection is rule-based, all fixes are template-based.
- **Inline comment cap** — maximum 10 inline comments per PR. Additional issues are summarized in the table only.
- **Summary only fallback** — if the GitHub API fails to return patch data, the script falls back to git-based detection, producing a summary comment without inline comments.
