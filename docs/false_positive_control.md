# False Positive Control

CodeSecAudit AI provides three mechanisms to reduce false positives and control what gets reviewed.

---

## 1. `.codesecignore`

A `.gitignore`-style file in the repository root. Files matching any pattern are **skipped during PR review**.

### Example `.codesecignore`

```
docs/
notebooks/
release/
dist/
deploy/
data/
tests/
build/
node_modules/
scripts/check_*deployment*.py
```

### Pattern syntax

| Pattern | Meaning |
|---------|---------|
| `docs/` | Skip the `docs/` directory entirely |
| `*.min.js` | Skip any minified JS file |
| `scripts/check_*.py` | Skip any file matching glob in any directory |
| `/scripts/deploy_*.py` | Skip only in root `scripts/` directory |
| `.env*` | Skip any `.env*` file |

Lines starting with `#` are treated as comments.

---

## 2. `.codesec.yml`

Structured YAML config in the repository root for fine-grained control.

### Example `.codesec.yml`

```yaml
# File extensions to scan during PR review.
supported_extensions:
  - .py
  - .js
  - .ts
  - .jsx
  - .tsx

# Additional paths to ignore (same syntax as .codesecignore but YAML).
ignored_paths:
  - "docs/"
  - "notebooks/"
  - "release/"
  - "dist/"
  - "deploy/"
  - "data/"

# Max inline comments posted per PR (applies to PR review only).
max_inline_comments: 10

# If true, exit with non-zero status when issues are found (CI blocking mode).
fail_on_issues: false

# If false, skip example files during PR review.
scan_examples: false

# If false, skip test files during PR review.
scan_tests: false
```

### Precedence

1. `.codesec.yml` overrides `supported_extensions` and `max_inline_comments` from defaults.
2. `.codesecignore` patterns are **added** to the built-in ignore patterns (not replacing).
3. Both files are optional; defaults are used when either is absent.

---

## 3. Inline Suppression Comments

Place comments in source code to suppress detections on specific lines.

### Suppress all rules for a single line

```python
result = eval(user_input)  # codesec-ignore
```

### Suppress a specific CWE for a single line

```python
result = eval(user_input)  # codesec-ignore: CWE-94
```

### Suppress all rules on the *next* line

```python
# codesec-ignore-next-line
result = eval(user_input)
```

### Suppress a specific CWE on the *next* line

```python
# codesec-ignore-next-line: CWE-94
result = eval(user_input)
```

### How it works

1. The `_build_suppression_map()` function scans every line for suppression markers and builds a dict of `{line_number: set_of_cwe_ids_or_None}`.
2. `detect_issues()` checks each candidate issue against the map before adding it.
3. `None` means "suppress all rules for this line"; a set of CWE IDs means "suppress only those CWEs".

This works across all supported languages because the marker detection is comment-syntax agnostic.

---

### Related

- `docs/github_action.md` — CI integration
- `docs/api_reference.md` — API endpoints
- `scripts/test_suppression.py` — test suite
