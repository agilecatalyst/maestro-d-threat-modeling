#!/usr/bin/env bash
# Quick stack smoke — API health + catalog list (no LLM pipeline).
set -euo pipefail

API="${API_URL:-http://127.0.0.1:8000}"

echo "→ GET $API/health"
health="$(curl -sf "$API/health")"
echo "$health" | grep -q '"status":"healthy"' || {
  echo "API unhealthy: $health" >&2
  exit 1
}

echo "→ GET $API/threat-designer/all?limit=1"
curl -sf "$API/threat-designer/all?limit=1" >/dev/null

echo "OK — API reachable and catalog responds"
