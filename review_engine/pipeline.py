from __future__ import annotations
import os
from typing import Optional

from review_engine.critic import detect_issues
from review_engine.fixer import generate_fix
from review_engine.risk_score import calculate_risk_score, decide_verdict

_RETRIEVER = None
_RAG_MODE = os.getenv("CODESEC_RAG_MODE", "local").lower()


def _is_remote_mode() -> bool:
    return _RAG_MODE == "remote"


def _get_retriever():
    global _RETRIEVER
    if _RETRIEVER is None:
        try:
            from review_engine.retriever import RAGRetriever
            _RETRIEVER = RAGRetriever()
        except (FileNotFoundError, ImportError) as e:
            _RETRIEVER = e
    return _RETRIEVER


def _remote_rag_search(query: str, top_k: int = 3) -> tuple[list[dict], Optional[str]]:
    from review_engine.remote_rag import search_remote_rag

    result = search_remote_rag(query, top_k=top_k)
    contexts = result.get("results", [])
    error = result.get("error")
    return contexts, error


def _get_contexts_for_issue(issue: dict, top_k: int) -> tuple[list[dict], Optional[str]]:
    cwe_id = issue["cwe_id"]
    query_parts = [issue["title"]]
    if cwe_id:
        query_parts.append(cwe_id)
    query = " ".join(query_parts)

    if _is_remote_mode():
        return _remote_rag_search(query, top_k=top_k)

    retriever = _get_retriever()
    if retriever is not None and not isinstance(retriever, Exception):
        contexts = retriever.search(query, top_k=top_k)
        return contexts, None

    return [], str(retriever) if isinstance(retriever, Exception) else None


def review_code(
    code: str,
    file_path: Optional[str] = None,
    use_rag: bool = True,
    top_k: int = 3,
) -> dict:
    issues = detect_issues(code, file_path=file_path)

    rag_used = False
    rag_error: Optional[str] = None

    if use_rag:
        contexts_for_issues = []
        for issue in issues:
            contexts, err = _get_contexts_for_issue(issue, top_k)
            contexts_for_issues.append(contexts)
            if err:
                rag_error = err
            if contexts:
                rag_used = True
                from review_engine.schemas import RetrievedContext
                for c in contexts:
                    issue["retrieved_context"].append(RetrievedContext(**c))
                issue["suggested_fix"] = generate_fix(issue, contexts)
            else:
                issue["suggested_fix"] = generate_fix(issue)
    else:
        for issue in issues:
            issue["suggested_fix"] = generate_fix(issue)

    risk_score = calculate_risk_score(issues)
    verdict = decide_verdict(risk_score)

    if not issues:
        summary = "No security issues detected."
    else:
        cwe_list = ", ".join(sorted(set(i["cwe_id"] for i in issues if i["cwe_id"])))
        summary = (
            f"Found {len(issues)} issue(s): {cwe_list}. "
            f"Risk score: {risk_score}/100. Verdict: {verdict}."
        )

    from review_engine.schemas import ReviewIssue, ReviewResult

    result = ReviewResult(
        summary=summary,
        risk_score=risk_score,
        verdict=verdict,
        issues=[ReviewIssue(**i) for i in issues],
        metadata={
            "engine_version": "0.6.0",
            "rag_used": rag_used,
            "rag_error": rag_error,
        },
    )

    return result.model_dump()
