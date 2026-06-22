# Evaluation

Golden cases in `eval/golden_cases.jsonl` are used to verify the reviewer's correctness
after changes.

## Run

```bash
pip install -e .            # if not already installed
python scripts/evaluate_reviewer.py
```

The script loads each golden case, runs it through `review_code(code=..., use_rag=False)`,
and compares the result against the expected values.

## Golden Case Fields

| Field | Description |
|---|---|
| `id` | Unique identifier |
| `description` | Human-readable description |
| `file_path` | Simulated file path passed to the reviewer |
| `code` | Source code to review |
| `expected_issues` | Exact expected issue count (if deterministic) |
| `expected_min_issues` / `expected_max_issues` | Allowed issue count range (alternative to exact) |
| `expected_verdict` | One of `APPROVE`, `WARNING`, `REQUEST_CHANGES` |
| `expected_cwes` | List of expected CWE IDs |

## What Is Tested

- All 7 rule-based detectors fire correctly
- Multi-hit detection: up to `MAX_FINDINGS_PER_RULE=3` per rule, `MAX_TOTAL_FINDINGS=20` total
- Duplicate deduplication: same `(file, line, cwe_id, snippet)` is reported only once
- Safe code produces zero issues
- Verdict thresholds are respected (score 60+ → REQUEST_CHANGES, 20-59 → WARNING, <20 → APPROVE)

## Adding a New Case

1. Append a JSON object to `eval/golden_cases.jsonl`
2. Run `python scripts/evaluate_reviewer.py` to confirm it passes
3. Commit both the new case and any reviewer changes together
