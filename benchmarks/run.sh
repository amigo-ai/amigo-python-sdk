#!/usr/bin/env bash
set -euo pipefail

if [ -z "${AMIGO_API_KEY:-}" ]; then
  echo "Error: Set AMIGO_API_KEY, AMIGO_API_KEY_ID, AMIGO_USER_ID, AMIGO_ORG_ID env vars"
  exit 1
fi

echo "=== Amigo Python SDK Benchmarks ==="
echo ""
echo "--- Token Refresh ---"
python benchmarks/token_refresh.py
echo ""
echo "--- Concurrent Requests ---"
python benchmarks/concurrent_requests.py
echo ""
echo "=== Done ==="
