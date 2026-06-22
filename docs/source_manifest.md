# Source Manifest — CodeSec Audit Dataset

## Current Raw Sources

### 1. CodeXGLUE Defect Detection
- Raw path: `data/raw/codexglue_defect_detection`
- Current size: 25M
- Format: JSONL
- Usage: Vulnerable vs non-vulnerable code classification baseline
- Priority: High
- Processing phase: Phase 1

### 2. OWASP Benchmark Python
- Raw path: `data/raw/owasp_benchmark_python`
- Current size: 17M
- Format: Python source files + benchmark metadata/results
- Usage: Python SAST/security review examples
- Priority: High
- Processing phase: Phase 1

### 3. OWASP Cheat Sheet Series
- Raw path: `data/raw/owasp_cheatsheet_series`
- Current size: 2.3G
- Format: Markdown documentation
- Usage: RAG security knowledge base
- Priority: High
- Processing phase: Phase 1

### 4. OWASP Benchmark Java
- Raw path: `data/raw/owasp_benchmark_java`
- Current size: 130M
- Format: Java source files + results/scorecards
- Usage: Java SAST benchmark and later evaluation
- Priority: Medium
- Processing phase: Phase 2

### 5. NIST Juliet Java
- Raw path: `data/raw/nist_juliet_java`
- Current size: 239M
- Format: CWE-based Java test case folders
- Usage: CWE-labeled Java examples
- Priority: Medium
- Processing phase: Phase 2

### 6. NIST Juliet C/C++
- Raw path: `data/raw/nist_juliet_c_cpp`
- Current size: 113M
- Format: CWE-based C/C++ test cases
- Usage: C/C++ vulnerability dataset
- Priority: Low for MVP
- Processing phase: Phase 3

## MVP Decision

For the first MVP, process only:
1. CodeXGLUE Defect Detection
2. OWASP Benchmark Python
3. OWASP Cheat Sheet Series

Reason:
These are enough to build the first version of the AI Code Security Auditor dataset:
- detection examples
- Python security examples
- RAG security knowledge base