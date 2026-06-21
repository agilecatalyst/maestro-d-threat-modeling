#!/usr/bin/env bash
# Verify pass for slices 010–017 — run with Docker stack up (postgres + api + tm-agent).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.dev.yml"

echo "→ Ensure stack is up"
$COMPOSE --profile full up -d postgres api tm-agent >/dev/null

echo "→ Repair migrations if tables missing (alembic stamp without schema)"
TABLE_COUNT=$($COMPOSE exec -T postgres psql -U maestro -d maestro_d -tAc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='threat_models';")
if [[ "${TABLE_COUNT// /}" != "1" ]]; then
  $COMPOSE exec -T postgres psql -U maestro -d maestro_d -c "TRUNCATE alembic_version;" >/dev/null
  $COMPOSE exec -T api alembic upgrade head
fi

python3 -m pip install -q pytest requests 2>/dev/null || true

echo "→ HOST: health, inference, upload"
python3 -m pytest test/test_health.py test/test_inference.py test/test_upload.py -q --tb=line

echo "→ API container tests"
$COMPOSE run --rm \
  -e DATABASE_URL=postgresql://maestro:maestro@postgres:5432/maestro_d \
  -e API_RATE_LIMIT_ENABLED=false \
  -v "$ROOT/test:/test:ro" \
  api bash -c 'pip install -q pytest requests && PYTHONPATH=/app pytest \
    /test/test_job_api.py /test/test_threat_mutations.py /test/test_audit_log.py \
    /test/test_rate_limit.py /test/test_description_cap.py /test/test_polish_016.py \
    /test/test_export.py /test/test_db.py /test/test_upload_validation.py \
    /test/test_threat_mutations_unit.py /test/test_backup_restore.py -q --tb=line'

echo "→ AGENT container tests"
$COMPOSE run --rm --no-deps \
  -v "$ROOT/test:/test:ro" \
  -v "$ROOT/backend/agent:/agent:ro" \
  -e PYTHONPATH=/agent \
  tm-agent bash -c 'pip install -q pytest && pytest \
    /test/test_assets_parser.py /test/test_flows_parser.py /test/test_threats_parser.py \
    /test/test_workflow_graph.py -q --tb=line'

echo "→ Repair schema after API tests (pytest drop_all teardown)"
TABLE_COUNT=$($COMPOSE exec -T postgres psql -U maestro -d maestro_d -tAc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='threat_models';")
if [[ "${TABLE_COUNT// /}" != "1" ]]; then
  $COMPOSE exec -T postgres psql -U maestro -d maestro_d -c "TRUNCATE alembic_version;" >/dev/null
  $COMPOSE exec -T api alembic upgrade head
fi

echo "→ Smoke"
bash "$ROOT/scripts/smoke.sh"

echo "VERIFY PASS OK"
