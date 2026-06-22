#!/usr/bin/env bash
set -euo pipefail

API_URL="${CODESEC_API_URL:-http://localhost:8003}"

echo "============================================"
echo " CodeSecAudit AI — Docker Smoke Test"
echo "============================================"
echo ""

# 1. Health check
echo "--- Checking /health ---"
HEALTH=$(curl -sf "$API_URL/health" || echo "")
if [ -z "$HEALTH" ]; then
  echo "FAIL: API not reachable at $API_URL/health"
  exit 1
fi
echo "PASS: API is healthy"
echo ""

# 2. Root endpoint
echo "--- Checking / ---"
ROOT=$(curl -sf "$API_URL/" || echo "")
if [ -z "$ROOT" ]; then
  echo "FAIL: Root endpoint not reachable"
  exit 1
fi
echo "PASS: Root endpoint works"
echo ""

# 3. Create a sample review
echo "--- Creating sample review ---"
REVIEW=$(curl -sf -X POST "$API_URL/review/code" \
  -H "Content-Type: application/json" \
  -d '{"code":"eval(user_input)","file_path":"demo.py","source":"docker-test","repo":"local/docker","pr_number":1,"use_rag":false}' || echo "")
if [ -z "$REVIEW" ]; then
  echo "FAIL: Could not create review"
  exit 1
fi
REVIEW_ID=$(echo "$REVIEW" | python3 -c "import sys,json; print(json.load(sys.stdin).get('review_id',''))" 2>/dev/null || echo "")
if [ -z "$REVIEW_ID" ]; then
  echo "FAIL: No review_id in response"
  exit 1
fi
echo "PASS: Review created: $REVIEW_ID"
echo ""

# 4. Stats endpoint
echo "--- Checking /stats ---"
STATS=$(curl -sf "$API_URL/stats" || echo "")
if [ -z "$STATS" ]; then
  echo "FAIL: Stats endpoint not reachable"
  exit 1
fi
echo "PASS: Stats endpoint works"
echo ""

# 5. List reviews
echo "--- Checking /reviews ---"
REVIEWS=$(curl -sf "$API_URL/reviews" || echo "")
if [ -z "$REVIEWS" ]; then
  echo "FAIL: Reviews endpoint not reachable"
  exit 1
fi
echo "PASS: Reviews endpoint works"
echo ""

echo "============================================"
echo " All smoke tests passed!"
echo "============================================"
echo ""
echo "URLs:"
echo "  API:         http://localhost:8003"
echo "  Review UI:   http://localhost:8501"
echo "  Dashboard:   http://localhost:8502"
echo "  API docs:    http://localhost:8003/docs"
