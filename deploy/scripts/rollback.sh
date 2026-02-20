#!/usr/bin/env bash
set -euo pipefail

# Rollback Fase 8
# Uso:
#   ./deploy/scripts/rollback.sh <tag-ou-commit>
#
# Exemplo:
#   ./deploy/scripts/rollback.sh v0.8.0

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

TARGET="${1:-}"
if [[ -z "${TARGET}" ]]; then
  echo "Uso: $0 <tag-ou-commit>"
  exit 1
fi

echo "[rollback] Buscando refs..."
git fetch --all --tags

echo "[rollback] Checkout ${TARGET}..."
git checkout "${TARGET}"

echo "[rollback] Subindo containers no commit/tag alvo..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --build

echo "[rollback] Aplicando migrations (se necessário)..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T api alembic upgrade head || true

echo "[rollback] Status:"
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps

echo "[rollback] Healthcheck:"
curl -fsS "http://127.0.0.1/api/v1/health" >/dev/null && echo "OK: /api/v1/health via Nginx (HTTP)"

echo "[rollback] Done."
