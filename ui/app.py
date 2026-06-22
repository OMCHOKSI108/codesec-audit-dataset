import os
import streamlit as st
import requests
import json

API_URL = os.environ.get("CODESEC_API_URL", "http://localhost:8003")
TOP_K = 5

st.set_page_config(
    page_title="CodeSecAudit Review",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 CodeSecAudit: RAG-Powered Security Review")
st.markdown(
    "Paste source code below to retrieve relevant OWASP cheat sheet context. "
    "Start the API first with: "
    "`uvicorn api.main:app --port 8003`"
)

example_code = st.selectbox(
    "Load example", ["", "SQL Injection", "Path Traversal", "XSS eval()"]
)

examples = {
    "SQL Injection": '''app.get("/user/:id", function(req, res) {
  const query = "SELECT * FROM users WHERE id = " + req.params.id;
  db.execute(query, function(err, rows) {
    res.json(rows);
  });
});''',
    "Path Traversal": '''<%
String filePath = request.getParameter("path");
File file = new File(filePath);
FileInputStream fis = new FileInputStream(file);
%>''',
    "XSS eval()": '''eval("alert('hello ' + " + user_input + ")");
document.write(user_input);''',
}

top_k = st.slider("Number of contexts", 1, 10, TOP_K)

code = st.text_area(
    "Source code",
    value=examples.get(example_code, ""),
    height=250,
    placeholder="Paste your code here...",
)

if st.button("Review", type="primary"):
    if not code.strip():
        st.warning("Please enter some code to review.")
        st.stop()

    with st.spinner("Querying RAG index..."):
        try:
            resp = requests.post(
                f"{API_URL}/review",
                json={"code": code, "top_k": top_k},
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot connect to API at {API_URL}. Is the server running?")
            st.stop()
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    cwe_summary = result.get("cwe_summary", {})

    st.subheader("Detected CWEs")
    if cwe_summary:
        cols = st.columns(len(cwe_summary))
        for col, (cwe, count) in zip(cols, sorted(cwe_summary.items())):
            col.metric(cwe, count)
    else:
        st.info("No specific CWE types identified.")

    st.subheader(f"Top {len(result['contexts'])} Relevant Contexts")
    for i, ctx in enumerate(result["contexts"], 1):
        with st.expander(
            f"[{i}] {ctx['title']} → {ctx['section']}  ({ctx['cwe_id']})"
        ):
            st.markdown(f"**Source:** `{ctx['source']}`")
            st.markdown(f"**CWE:** {ctx['cwe_id']}")
            st.text_area(
                "Content",
                ctx["content"],
                height=200,
                key=f"ctx_{i}",
            )

    with st.expander("Raw API Response"):
        st.json(result)

st.markdown("---")
st.markdown("Built with [CodeSecAudit-RAG](https://huggingface.co/datasets/OMCHOKSI108/CodeSecAudit-RAG)")
