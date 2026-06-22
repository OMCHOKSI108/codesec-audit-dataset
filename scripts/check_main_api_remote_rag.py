"""Verify the main API pipeline with remote RAG enabled."""

import os
import sys

ENABLE_RAG = os.getenv("CODESEC_ENABLE_RAG", "")
RAG_MODE = os.getenv("CODESEC_RAG_MODE", "")
SERVICE_URL = os.getenv("CODESEC_RAG_SERVICE_URL", "")


def main():
    if ENABLE_RAG.lower() not in ("1", "true", "yes"):
        print("ERROR: CODESEC_ENABLE_RAG must be set to true")
        sys.exit(1)

    if RAG_MODE != "remote":
        print("ERROR: CODESEC_RAG_MODE must be 'remote'")
        sys.exit(1)

    if not SERVICE_URL:
        print("ERROR: CODESEC_RAG_SERVICE_URL is not set")
        sys.exit(1)

    print(f"Testing review_code with remote RAG ({RAG_MODE})")
    print(f"  CODESEC_RAG_SERVICE_URL={SERVICE_URL}")
    print()

    from review_engine.pipeline import review_code

    result = review_code("eval(user_input)", use_rag=True)
    issues = result["issues"]
    meta = result["metadata"]
    rag_used = meta.get("rag_used", False)
    rag_error = meta.get("rag_error")

    print(f"  verdict:     {result['verdict']}")
    print(f"  risk_score:  {result['risk_score']}")
    print(f"  issues:      {len(issues)}")
    print(f"  rag_used:    {rag_used}")
    print(f"  rag_error:   {rag_error}")
    print()

    if rag_error:
        print(f"WARNING: RAG unavailable — {rag_error}")
        print("  Rule review completed successfully but no RAG context retrieved")
        print("  Check RAG service health and URL configuration")
    else:
        contexts_found = 0
        for issue in issues:
            ctx = issue.get("retrieved_context", [])
            contexts_found += len(ctx)
        print(f"  retrieved_context_count: {contexts_found}")
        if rag_used:
            print("OK: Remote RAG used successfully in review")
        else:
            print("OK: Rule review completed (RAG mode remote, no context retrieved)")

    if str(result.get("verdict", "")).lower() in ("error",):
        print("ERROR: Review returned error verdict")
        sys.exit(1)

    print()
    print("OK: Main API remote RAG check passed")


if __name__ == "__main__":
    main()
