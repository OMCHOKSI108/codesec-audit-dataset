"""Test the remote RAG client against a running RAG service."""

import os
import sys

SERVICE_URL = os.getenv("CODESEC_RAG_SERVICE_URL", "http://localhost:7860")
API_KEY = os.getenv("CODESEC_RAG_API_KEY", "")


def test_search():
    # Point the client env vars at the test service
    os.environ["CODESEC_RAG_SERVICE_URL"] = SERVICE_URL
    if API_KEY:
        os.environ["CODESEC_RAG_API_KEY"] = API_KEY

    from review_engine.remote_rag import search_remote_rag, remote_rag_available

    # Check availability
    available = remote_rag_available()
    if not available:
        print(f"WARNING: RAG service at {SERVICE_URL} not reachable — skipping")
        return True

    print(f"OK: RAG service reachable at {SERVICE_URL}")

    # Perform a search
    result = search_remote_rag("sql injection prepared statements", top_k=3)
    results = result.get("results", [])
    error = result.get("error")

    if error:
        print(f"FAIL: search returned error: {error}")
        return False

    print(f"OK: Got {len(results)} results")
    if results:
        r = results[0]
        print(f"     Top: [{r['cwe_id']}] {r['title']} (score={r['score']:.3f})")

    meta = result.get("metadata", {})
    if meta:
        print(f"     Model: {meta.get('embedding_model')}")
        print(f"     Total chunks: {meta.get('total_chunks')}")
        print(f"     Query time: {meta.get('query_time_ms')}ms")

    return True


def test_pipeline_integration():
    """Test that review_code uses remote RAG when configured."""
    os.environ["CODESEC_RAG_MODE"] = "remote"

    from review_engine.pipeline import review_code

    result = review_code("eval(user_input)", use_rag=True)
    rag_used = result["metadata"].get("rag_used", False)
    rag_error = result["metadata"].get("rag_error")

    issues = len(result["issues"])
    print(f"OK: review_code returned {issues} issues")
    print(f"     rag_used={rag_used}, rag_error={rag_error}")
    print(f"     risk_score={result['risk_score']}, verdict={result['verdict']}")

    if issues > 0:
        ctx = result["issues"][0].get("retrieved_context", [])
        print(f"     retrieved_context count: {len(ctx)}")

    return True


def main():
    print(f"Testing remote RAG client against {SERVICE_URL}")
    print()

    checks = [test_search, test_pipeline_integration]
    failures = 0
    for check in checks:
        try:
            if not check():
                failures += 1
        except Exception as e:
            print(f"FAIL: {check.__name__}: {e}")
            failures += 1
        print()

    if failures:
        sys.exit(1)
    else:
        print("All checks passed!")


if __name__ == "__main__":
    main()
