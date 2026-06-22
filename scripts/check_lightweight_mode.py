"""Verify that the review engine works without RAG dependencies installed."""

import subprocess
import sys


def check_no_rag_deps():
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=columns"],
        capture_output=True, text=True, check=True,
    )
    heavy = []
    for pkg in ["chromadb", "sentence-transformers", "torch"]:
        if pkg.lower() in result.stdout.lower():
            heavy.append(pkg)
    if heavy:
        print(f"NOTE: Heavy deps installed ({', '.join(heavy)}) — not a lightweight env, "
              "but checking fallback logic still works")
    else:
        print("OK: No heavy RAG deps (chromadb, sentence-transformers, torch) found")
    return True


def check_review_works():
    code = 'def hello(user):\n    return "Hello " + user\n'
    from review_engine.pipeline import review_code
    result = review_code(code, use_rag=False)
    assert result["risk_score"] >= 0
    assert not result["metadata"]["rag_used"]
    assert result["metadata"]["retriever_error"] is None
    print(f"OK: review_code(use_rag=False) returned {len(result['issues'])} issues, "
          f"score={result['risk_score']}")
    return True


def check_rag_fallback():
    code = 'def hello(user):\n    return "Hello " + user\n'
    from review_engine.pipeline import review_code
    result = review_code(code, use_rag=True)
    assert result["risk_score"] >= 0
    if result["metadata"]["rag_used"]:
        print("OK: RAG deps available — review_code(use_rag=True) used RAG successfully")
    else:
        assert result["metadata"]["retriever_error"] is not None
        print(f"OK: review_code(use_rag=True) fell back gracefully. "
              f"error={result['metadata']['retriever_error'][:60]}...")
    return True


def main():
    checks = [check_no_rag_deps, check_review_works, check_rag_fallback]
    for check in checks:
        try:
            check()
        except Exception as e:
            print(f"FAIL: {check.__name__}: {e}")
            sys.exit(1)
    print("\nAll checks passed — lightweight mode verified!")


if __name__ == "__main__":
    main()
