import os
import json
from datetime import datetime

import streamlit as st
import pandas as pd
import requests

API_BASE_URL = os.getenv("CODESEC_API_URL", "http://localhost:8003")

st.set_page_config(
    page_title="CodeSecAudit Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 CodeSecAudit AI — Review History Dashboard")
st.markdown(
    "AI Pull Request Reviewer analytics and saved review history. "
    "API: `{}`".format(API_BASE_URL)
)


def _get(path: str, timeout: int = 10):
    resp = requests.get(f"{API_BASE_URL}{path}", timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, data: dict, timeout: int = 30):
    resp = requests.post(
        f"{API_BASE_URL}{path}", json=data, timeout=timeout
    )
    resp.raise_for_status()
    return resp.json()


# --- Helpers ---

def fmt_time(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return iso or ""


def severity_color(sev: str) -> str:
    return {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵",
    }.get(sev.lower(), "⚪")


def verdict_color(v: str) -> str:
    return {
        "APPROVE": "🟢",
        "WARNING": "🟡",
        "REQUEST_CHANGES": "🔴",
    }.get(v, "⚪")


# --- Sidebar ---

st.sidebar.header("Controls")
if st.sidebar.button("🔄 Refresh dashboard"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("**Filters**")

# --- Health check ---

health_ok = False
try:
    health = _get("/health")
    health_ok = health.get("status") == "ok"
except Exception:
    health_ok = False

if health_ok:
    uptime = health.get("uptime_seconds", 0)
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)
    st.sidebar.success(
        f"✅ API connected\n"
        f"v{health.get('engine_version', '?')}  |  "
        f"uptime: {hours}h {minutes}m"
    )
else:
    st.sidebar.error("❌ API unavailable")
    st.warning(
        "Cannot connect to the API at {}. "
        "Start the API with: `uvicorn api.main:app --port 8003`".format(API_BASE_URL)
    )
    st.stop()

# --- Stats cards ---

try:
    stats = _get("/stats")
except Exception:
    stats = {
        "total_reviews": 0,
        "average_risk_score": 0.0,
        "high_risk_reviews": 0,
        "total_issues": 0,
        "verdict_counts": {"APPROVE": 0, "WARNING": 0, "REQUEST_CHANGES": 0},
    }

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Reviews", stats.get("total_reviews", 0))
col2.metric("Avg Risk Score", f'{stats.get("average_risk_score", 0.0):.1f}/100')
col3.metric("High Risk Reviews", stats.get("high_risk_reviews", 0))
col4.metric("Total Issues", stats.get("total_issues", 0))

vc = stats.get("verdict_counts", {})
vc_cols = st.columns(3)
for i, (verdict, count) in enumerate(
    sorted(vc.items(), key=lambda x: ["REQUEST_CHANGES", "WARNING", "APPROVE"].index(x[0]))
):
    vc_cols[i].metric(f"{verdict_color(verdict)} {verdict}", count)

st.markdown("---")

# --- Charts ---

try:
    reviews_raw = _get("/reviews?limit=200")
except Exception:
    reviews_raw = []

st.subheader("Analytics")

chart_col1, chart_col2 = st.columns(2)

if reviews_raw:
    df = pd.DataFrame(reviews_raw)

    with chart_col1:
        verdict_counts = df["verdict"].value_counts()
        st.bar_chart(
            verdict_counts,
            height=300,
        )

    with chart_col2:
        if "risk_score" in df.columns:
            risk_bins = pd.cut(
                df["risk_score"],
                bins=[0, 20, 40, 60, 80, 101],
                labels=["0-19", "20-39", "40-59", "60-79", "80-100"],
                right=False,
            )
            risk_dist = risk_bins.value_counts().sort_index()
            st.bar_chart(risk_dist, height=300)
        else:
            st.info("No risk score data available")
else:
    st.info("No review data available for charts")
    chart_col1.info("No data")
    chart_col2.info("No data")

st.markdown("---")

# --- Filters ---

st.subheader("Recent Reviews")

filters_ok = True
try:
    reviews = _get("/reviews?limit=200")
    if not isinstance(reviews, list):
        reviews = []
except Exception:
    reviews = []
    filters_ok = False

if not filters_ok:
    st.error("Failed to load reviews")
    st.stop()

filter_col1, filter_col2, filter_col3 = st.columns(3)
verdict_filter = filter_col1.selectbox(
    "Verdict filter", ["All", "APPROVE", "WARNING", "REQUEST_CHANGES"]
)
min_risk = filter_col2.slider("Minimum risk score", 0, 100, 0)
repo_search = filter_col3.text_input("Repo search (text)")

if reviews:
    df_all = pd.DataFrame(reviews)

    if verdict_filter != "All":
        df_all = df_all[df_all["verdict"] == verdict_filter]

    if min_risk > 0:
        df_all = df_all[df_all["risk_score"] >= min_risk]

    if repo_search:
        df_all = df_all[
            df_all["repo"]
            .fillna("")
            .str.contains(repo_search, case=False, na=False)
        ]

    display_cols = [
        "id", "created_at", "repo", "pr_number", "file_path",
        "risk_score", "verdict", "summary",
    ]
    show_cols = [c for c in display_cols if c in df_all.columns]

    if "created_at" in df_all.columns:
        df_all["created_at"] = df_all["created_at"].apply(fmt_time)

    st.dataframe(
        df_all[show_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.TextColumn("ID", width="small"),
            "created_at": st.column_config.TextColumn("Created", width="medium"),
            "summary": st.column_config.TextColumn("Summary", width="large"),
        },
    )

    st.markdown(f"**{len(df_all)}** review(s) shown")
else:
    st.info(
        "No reviews found. "
        "Create sample data with: `python scripts/github_pr_review.py "
        "--dry-run --files examples/vulnerable_pr_demo.py --save`"
    )

st.markdown("---")

# --- Review detail viewer ---

st.subheader("Review Detail Viewer")

review_ids = [r.get("id", "") for r in reviews if r.get("id")] if reviews else []
selected_id = st.selectbox(
    "Select review ID",
    [""] + review_ids,
    format_func=lambda x: x[:8] + "..." if x and len(x) > 8 else x or "None",
)

if selected_id:
    try:
        detail = _get(f"/reviews/{selected_id}")
    except Exception:
        st.error("Failed to load review detail")
        st.stop()

    st.json({
        "id": detail.get("id"),
        "source": detail.get("source"),
        "repo": detail.get("repo"),
        "pr_number": detail.get("pr_number"),
        "commit_sha": detail.get("commit_sha"),
        "created_at": fmt_time(detail.get("created_at", "")),
        "risk_score": detail.get("risk_score"),
        "verdict": detail.get("verdict"),
        "summary": detail.get("summary"),
    })

    issues = detail.get("issues", [])
    st.markdown(f"### Issues ({len(issues)})")

    if issues:
        issue_rows = []
        for iss in issues:
            issue_rows.append({
                "File": iss.get("file", ""),
                "Line": iss.get("line", ""),
                "CWE": iss.get("cwe_id", ""),
                "Severity": f"{severity_color(iss.get('severity', ''))} {iss.get('severity', '').capitalize()}",
                "Title": iss.get("title", ""),
                "Explanation": iss.get("explanation", ""),
                "Suggested Fix": iss.get("suggested_fix", ""),
            })
        df_issues = pd.DataFrame(issue_rows)
        st.dataframe(
            df_issues,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Explanation": st.column_config.TextColumn("Explanation", width="large"),
                "Suggested Fix": st.column_config.TextColumn("Suggested Fix", width="large"),
            },
        )

        # CWEs in detail
        cwe_counts = pd.Series(
            [i.get("cwe_id", "unknown") for i in issues]
        ).value_counts()
        st.bar_chart(cwe_counts, height=200)
    else:
        st.info("No issues found.")
else:
    st.info("Select a review ID above to view details.")

st.markdown("---")
st.caption(
    "CodeSecAudit AI — v0.6.0  |  "
    "[Docs](docs/review_history_api.md)  |  "
    "DB: `data/app/reviews.db`"
)
