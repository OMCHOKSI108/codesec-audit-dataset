import json
import argparse
from pathlib import Path

from review_engine.pipeline import review_code as engine_review

TOP_K = 3


def format_report(result: dict, code: str) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("  CodeSecAudit: RAG Security Review")
    lines.append("=" * 72)
    lines.append(f"\n--- Submitted Code ---\n{code.strip()[:300]}")
    if len(code.strip()) > 300:
        lines.append("  ... (truncated)")

    lines.append("")
    lines.append(f"--- Summary ---")
    lines.append(f"  {result['summary']}")
    lines.append(f"  Risk Score: {result['risk_score']}/100")
    lines.append(f"  Verdict: {result['verdict']}")
    lines.append(f"  RAG Used: {result['metadata']['rag_used']}")

    if result["metadata"].get("retriever_error"):
        lines.append(f"  RAG Error: {result['metadata']['retriever_error']}")

    issues = result.get("issues", [])
    if not issues:
        lines.append("\n✓ No security issues detected. Code looks clean.")
    else:
        for i, issue in enumerate(issues, 1):
            lines.append(f"\n--- Issue #{i} ---")
            lines.append(f"  Title: {issue['title']}")
            lines.append(f"  CWE: {issue['cwe_id']}  |  Severity: {issue['severity']}")
            fpath = issue.get("file")
            lnum = issue.get("line")
            if fpath and lnum:
                lines.append(f"  Location: {fpath}:{lnum}")
            elif lnum:
                lines.append(f"  Line: {lnum}")
            if issue.get("code_snippet"):
                lines.append(f"  Snippet: {issue['code_snippet']}")
            lines.append(f"  Explanation: {issue['explanation']}")
            lines.append(f"\n  Suggested Fix:")
            for fix_line in issue['suggested_fix'].strip().split("\n"):
                lines.append(f"    {fix_line.strip()}")

            ctx = issue.get("retrieved_context", [])
            if ctx:
                lines.append(f"\n  RAG Context ({len(ctx)} retrieved):")
                for j, c in enumerate(ctx[:2], 1):
                    lines.append(f"    [{j}] {c['title']} > {c['section']} ({c['cwe_id']})")

    lines.append("")
    lines.append("=" * 72)
    lines.append("Review complete.")
    lines.append("=" * 72)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="CodeSecAudit: RAG-based Security Code Reviewer"
    )
    parser.add_argument("file", nargs="?", metavar="FILE", help="Path to source code file to review")
    parser.add_argument("--file", dest="file_alt", help=argparse.SUPPRESS)
    parser.add_argument("--code", help="Inline code string to review")
    parser.add_argument("--top-k", type=int, default=TOP_K, help="Number of RAG contexts")
    parser.add_argument("--no-rag", action="store_true", help="Disable RAG retrieval")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    file_path_arg = args.file or args.file_alt
    if file_path_arg:
        code = Path(file_path_arg).read_text(encoding="utf-8")
        file_path = file_path_arg
    elif args.code:
        code = args.code
        file_path = None
    else:
        code = """app.get("/user/:id", function(req, res) {
  const query = "SELECT * FROM users WHERE id = " + req.params.id;
  db.execute(query, function(err, rows) {
    res.json(rows);
  });
});"""
        file_path = None

    result = engine_review(
        code=code,
        file_path=file_path,
        use_rag=not args.no_rag,
        top_k=args.top_k,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_report(result, code))


if __name__ == "__main__":
    main()
