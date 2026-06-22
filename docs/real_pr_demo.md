# Real PR Demo — CodeSecAudit AI

This document provides exact steps to create a test pull request and verify that
CodeSecAudit AI works inside GitHub PRs.

## Expected Findings

When the demo vulnerable file is added via PR, the GitHub Action should detect:

| CWE | Issue | Severity |
|-----|-------|----------|
| CWE-94 | Code Injection via `eval()` | critical |
| CWE-328 | Weak Hashing (`md5`, `sha1`) | high |
| CWE-798 | Hardcoded Credential / Secret | critical |
| CWE-22 | Path Traversal via Unsafe File Access | high |
| CWE-78 | OS Command Injection via subprocess/shell | critical |

## Manual Steps

### 1. Create a new branch

```bash
git checkout -b demo/codesec-pr-review
```

### 2. Add the demo files

```bash
git add examples/vulnerable_pr_demo.py examples/safe_pr_demo.py docs/real_pr_demo.md
git commit -m "demo: add CodeSecAudit vulnerable PR test files"
git push origin demo/codesec-pr-review
```

### 3. Open a pull request

Open a PR from `demo/codesec-pr-review` into your default branch using the
GitHub web UI or `gh` CLI.

### 4. Wait for the GitHub Action

The workflow `.github/workflows/codesec-audit.yml` triggers automatically on
`opened`, `synchronize`, and `reopened`.

Expected duration: ~1–2 minutes (first run may take longer to install deps).

### 5. Confirm summary comment

After the action completes, a summary PR comment appears containing:

- Verdict
- Risk score
- Issues Found table with Location, CWE, Severity, Issue, Suggested Fix
- Notes

### 6. Confirm inline comments

Inline comments should appear directly on vulnerable lines in the diff:

| File | Line | Issue |
|------|------|-------|
| `examples/vulnerable_pr_demo.py` | 8 | CWE-798 Hardcoded Secret |
| `examples/vulnerable_pr_demo.py` | 11 | CWE-94 Code Injection via `eval()` |
| `examples/vulnerable_pr_demo.py` | 15 | CWE-328 Weak Hashing (`md5`) |
| `examples/vulnerable_pr_demo.py` | 18 | CWE-78 OS Command Injection |
| `examples/vulnerable_pr_demo.py` | 29 | CWE-328 Weak Hashing (`sha1`) |

Issues on lines that are not part of the added diff (e.g. lines 21, 24) will
remain in the summary table only.

### 7. Capture screenshots

Screenshot checklist:

- [ ] PR overview page showing the CodeSecAudit check
- [ ] GitHub Action successful run log
- [ ] CodeSecAudit summary comment at the bottom of the PR
- [ ] Inline comment on `eval(` line (line 11)
- [ ] Inline comment on `hashlib.md5(` line (line 15)
- [ ] Inline comment on `API_SECRET_KEY` line (line 8)

### 8. Close the test PR

After verification, close the test PR without merging:

```bash
gh pr close demo/codesec-pr-review
```

Or close via the GitHub web UI.

## Local Dry-Run

Before pushing, test locally:

```bash
python scripts/github_pr_review.py --files examples/vulnerable_pr_demo.py --dry-run
```

Expected output:

- Summary markdown with multiple issues
- Inline Comment Plan table with `dry-run-local` status

Also verify the CLI reviewer:

```bash
python scripts/review_code.py --file examples/vulnerable_pr_demo.py --json
```

Expected JSON contains `CWE-94`, `CWE-328`, `CWE-798`, etc.

## Troubleshooting

### Action did not run

- Ensure the workflow file exists on the **default branch** (not just the PR branch).
- The workflow triggers on `pull_request: [opened, synchronize, reopened]`.
- Check the repository's Actions tab for any disabled workflows.

### No inline comments

- Inline comments only appear on **added lines** in the PR diff.
- Check that the issue line number is in the diff's added lines (green `+` lines).
- If using the GitHub API fallback (not git), the API must return `patch` data.
- Verify the file is in a supported extension (`.py`, `.js`, `.ts`, `.jsx`, `.tsx`).

### Permission error

- The workflow needs `pull-requests: write` permission.
- Check repository Settings → Actions → General → Workflow permissions.
- `GITHUB_TOKEN` should have read/write access to pull requests.

### No supported files changed

- The action only reviews files with supported extensions.
- Check that the changed file has one of: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`.
- Files in ignored directories (`data/`, `node_modules/`, etc.) are skipped.
- Files larger than 200 KB are skipped.

### Duplicate comment skipped

- If an inline comment with the same path + line + CWE already exists, it is skipped.
- This is intentional — update the file on a new line to trigger a new comment.
- Or delete the existing inline comment manually before re-running.

### Summary only / no inline comments in fallback mode

- If the GitHub API call to fetch PR files with patches fails, the script falls
  back to git-based detection, which only produces a summary comment.
- Check the Action log for API error messages.
