import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

CHEATSHEETS_DIR = ROOT / "data/raw/owasp_cheatsheet_series/cheatsheets"
OUT_PATH = ROOT / "data/final/rag/rag_corpus.jsonl"
SUMMARY_PATH = ROOT / "data/final/metadata/owasp_cheatsheets_rag_summary.json"

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

TARGET_KEYWORDS = [
    "sql",
    "injection",
    "command",
    "xss",
    "cross_site",
    "input_validation",
    "authentication",
    "authorization",
    "access",
    "password",
    "secrets",
    "secret",
    "file_upload",
    "ssrf",
    "deserialization",
    "xxe",
    "xml",
    "cryptographic",
    "crypto",
    "session",
    "cookie",
    "csrf",
    "logging",
    "error",
    "api",
    "rest",
    "jwt",
    "oauth",
    "docker",
    "kubernetes",
]

CWE_MAP = [
    (["sql injection", "sql"], "CWE-89", "SQL Injection", "A03: Injection"),
    (["command injection", "os command", "shell"], "CWE-78", "OS Command Injection", "A03: Injection"),
    (["ldap"], "CWE-90", "LDAP Injection", "A03: Injection"),
    (["xpath"], "CWE-643", "XPath Injection", "A03: Injection"),
    (["xss", "cross site scripting", "cross-site scripting"], "CWE-79", "Cross-Site Scripting", "A03: Injection"),
    (["code injection", "eval"], "CWE-94", "Code Injection", "A03: Injection"),
    (["path traversal", "directory traversal"], "CWE-22", "Path Traversal", "A01: Broken Access Control"),
    (["file upload", "upload"], "CWE-434", "Unrestricted File Upload", "A05: Security Misconfiguration"),
    (["ssrf", "server side request forgery", "server-side request forgery"], "CWE-918", "Server-Side Request Forgery", "A10: Server-Side Request Forgery"),
    (["deserialization", "deserialize"], "CWE-502", "Deserialization of Untrusted Data", "A08: Software and Data Integrity Failures"),
    (["xxe", "xml external entity"], "CWE-611", "XML External Entity Injection", "A05: Security Misconfiguration"),
    (["weak hash", "hashing", "password storage"], "CWE-328", "Weak Hashing Algorithm", "A02: Cryptographic Failures"),
    (["random", "randomness"], "CWE-330", "Use of Insufficiently Random Values", "A02: Cryptographic Failures"),
    (["cookie"], "CWE-614", "Sensitive Cookie Without Secure Flag", "A05: Security Misconfiguration"),
    (["open redirect", "redirect"], "CWE-601", "Open Redirect", "A01: Broken Access Control"),
    (["hardcoded", "secret", "secrets"], "CWE-798", "Hardcoded Credentials", "A02: Cryptographic Failures"),
    (["authorization", "access control"], "CWE-862", "Missing Authorization", "A01: Broken Access Control"),
    (["authentication", "session"], "CWE-287", "Improper Authentication", "A07: Identification and Authentication Failures"),
]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "untitled"


def clean_markdown(text: str) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_title_from_markdown(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line.replace("#", "").strip()
    return fallback.replace("_", " ").replace(".md", "").strip()


def should_include_file(path: Path, text: str) -> bool:
    name = path.name.lower()
    sample = text[:3000].lower()
    return any(k in name or k in sample for k in TARGET_KEYWORDS)


def infer_security_mapping(text: str, filename: str):
    haystack = f"{filename} {text}".lower()
    for keywords, cwe_id, vuln_name, owasp_category in CWE_MAP:
        if any(k in haystack for k in keywords):
            return cwe_id, vuln_name, owasp_category
    return "general", "General Secure Coding Guidance", "general"


def split_by_headings(markdown: str):
    lines = markdown.splitlines()
    sections = []
    current_heading = "Overview"
    current_lines = []

    for line in lines:
        if re.match(r"^#{2,6}\s+", line):
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
                current_lines = []
            current_heading = re.sub(r"^#{2,6}\s+", "", line).strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    return [(h, body) for h, body in sections if body.strip()]


def chunk_text(text: str, max_chars: int = 2200, overlap_chars: int = 250):
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_chars
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap_chars)

    return chunks


def make_id(source_file: str, section_title: str, chunk_index: int, content: str) -> str:
    raw = f"{source_file}|{section_title}|{chunk_index}|{content[:200]}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"owasp_cs_{digest}"


def extract_tags(filename: str, title: str, section_title: str, cwe_id: str, vuln_name: str):
    raw = f"{filename} {title} {section_title} {vuln_name}".lower()
    tags = {"owasp", "cheatsheet", "secure-coding", "rag-context"}

    keyword_tags = {
        "sql": "sql-injection",
        "xss": "xss",
        "csrf": "csrf",
        "ssrf": "ssrf",
        "jwt": "jwt",
        "oauth": "oauth",
        "password": "password-security",
        "secret": "secret-management",
        "upload": "file-upload",
        "cookie": "cookie-security",
        "session": "session-security",
        "crypto": "cryptography",
        "logging": "logging",
        "error": "error-handling",
        "api": "api-security",
        "access": "access-control",
        "authorization": "authorization",
        "authentication": "authentication",
        "deserialization": "deserialization",
        "xml": "xml-security",
        "docker": "docker",
        "kubernetes": "kubernetes",
    }

    for key, tag in keyword_tags.items():
        if key in raw:
            tags.add(tag)

    if cwe_id and cwe_id != "general":
        tags.add(cwe_id.lower())

    return sorted(tags)


def main():
    print("Converting OWASP Cheat Sheet Series to RAG corpus")
    print("=" * 70)

    if not CHEATSHEETS_DIR.exists():
        raise FileNotFoundError(f"Missing cheat sheets folder: {CHEATSHEETS_DIR}")

    md_files = sorted(CHEATSHEETS_DIR.glob("*.md"))

    included_files = []
    skipped_files = []
    records = []

    for md_path in md_files:
        raw_text = md_path.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_markdown(raw_text)

        if not cleaned:
            skipped_files.append(str(md_path.name))
            continue

        if not should_include_file(md_path, cleaned):
            skipped_files.append(str(md_path.name))
            continue

        included_files.append(str(md_path.name))

        title = get_title_from_markdown(cleaned, md_path.name)
        cwe_id, vulnerability_name, owasp_category = infer_security_mapping(cleaned[:5000], md_path.name)

        sections = split_by_headings(cleaned)

        for section_title, section_body in sections:
            section_body = section_body.strip()

            if len(section_body) < 120:
                continue

            chunks = chunk_text(section_body)

            for chunk_index, chunk in enumerate(chunks, start=1):
                record_id = make_id(md_path.name, section_title, chunk_index, chunk)

                content = f"{title}\n\nSection: {section_title}\n\n{chunk}".strip()

                record = {
                    "id": record_id,
                    "source_name": "OWASP Cheat Sheet Series",
                    "source_type": "public_documentation",
                    "doc_type": "secure_guidance",
                    "source_file": md_path.name,
                    "title": title,
                    "section_title": section_title,
                    "chunk_index": chunk_index,
                    "language": "general",
                    "framework": "general",
                    "task": "rag_context",
                    "cwe_id": cwe_id,
                    "vulnerability_name": vulnerability_name,
                    "owasp_category": owasp_category,
                    "content": content,
                    "positive_pattern": "",
                    "negative_pattern": "",
                    "tags": extract_tags(md_path.name, title, section_title, cwe_id, vulnerability_name),
                    "metadata": {
                        "raw_path": str(md_path.relative_to(ROOT)),
                        "content_chars": len(content),
                        "created_at": datetime.utcnow().isoformat() + "Z",
                    }
                }

                records.append(record)

    with OUT_PATH.open("w", encoding="utf-8") as out:
        for record in records:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "source": "OWASP Cheat Sheet Series",
        "input_dir": str(CHEATSHEETS_DIR.relative_to(ROOT)),
        "output_path": str(OUT_PATH.relative_to(ROOT)),
        "total_markdown_files": len(md_files),
        "included_files_count": len(included_files),
        "skipped_files_count": len(skipped_files),
        "total_rag_chunks": len(records),
        "included_files": included_files,
        "skipped_files_sample": skipped_files[:100],
        "top_cwe_counts": dict(Counter(r["cwe_id"] for r in records).most_common(30)),
        "top_vulnerability_names": dict(Counter(r["vulnerability_name"] for r in records).most_common(30)),
        "top_tags": dict(Counter(tag for r in records for tag in r["tags"]).most_common(50)),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Markdown files found: {len(md_files)}")
    print(f"Included files: {len(included_files)}")
    print(f"Skipped files: {len(skipped_files)}")
    print(f"RAG chunks created: {len(records)}")
    print(f"Output saved to: {OUT_PATH.relative_to(ROOT)}")
    print(f"Summary saved to: {SUMMARY_PATH.relative_to(ROOT)}")

    print("\nTop CWE counts:")
    for cwe, count in Counter(r["cwe_id"] for r in records).most_common(20):
        print(f"- {cwe}: {count}")

    print("\nTop vulnerability names:")
    for name, count in Counter(r["vulnerability_name"] for r in records).most_common(20):
        print(f"- {name}: {count}")


if __name__ == "__main__":
    main()
