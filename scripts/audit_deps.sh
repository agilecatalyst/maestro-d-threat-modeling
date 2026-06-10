#!/usr/bin/env bash
# Maestro review gate — pip-audit on Python 3.12 (matches Docker images)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
docker run --rm -v "$ROOT:/app" -w /app python:3.12-slim sh -c '
  pip install -q pip-audit &&
  pip-audit -r backend/api/requirements.txt -r backend/agent/requirements.txt
'
