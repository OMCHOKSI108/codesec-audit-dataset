# Dataset Plan — CodeSec Audit Dataset

## Goal

Build a curated dataset for an Enterprise Code Review & Security Auditor Agent.

The dataset will support:
1. Vulnerability detection
2. Security review explanation
3. Secure code repair
4. RAG-based security guidance retrieval

## Initial MVP Scope

### Languages
- Python
- C
- JavaScript later through synthetic generation

### First Public Sources
- CodeXGLUE Defect Detection
- OWASP Benchmark Python
- OWASP Cheat Sheet Series

### Later Sources
- OWASP Benchmark Java
- NIST Juliet Java
- NIST Juliet C/C++

## Final Outputs

### Review Dataset
Path:
`data/final/review/train.jsonl`
`data/final/review/validation.jsonl`
`data/final/review/test.jsonl`

Purpose:
Used for detecting and explaining vulnerabilities.

### Repair Dataset
Path:
`data/final/repair/train.jsonl`
`data/final/repair/validation.jsonl`
`data/final/repair/test.jsonl`

Purpose:
Used for vulnerable-code to secure-code repair examples.

### RAG Corpus
Path:
`data/final/rag/rag_corpus.jsonl`

Purpose:
Used for vector database ingestion using Qdrant or ChromaDB.

## Final Standard Schema

```json
{
  "id": "string",
  "source_name": "string",
  "source_type": "public_dataset | synthetic | manual",
  "language": "string",
  "framework": "string",
  "task": "vulnerability_detection | security_review | secure_code_repair | rag_context",
  "cwe_id": "string",
  "owasp_category": "string",
  "severity": "low | medium | high | critical | unknown",
  "is_vulnerable": true,
  "vulnerability_name": "string",
  "input_code": "string",
  "fixed_code": "string",
  "explanation": "string",
  "secure_pattern": "string",
  "tags": ["string"],
  "metadata": {}
}