#!/usr/bin/env bash
set -euo pipefail

# Deploy Fase 8 (produção-lite)
# Uso:
#   ./deploy/scripts/deploy.sh
#
# Requisitos:
# - estar na raiz do repo no servidor (/opt/projeto01)
# - existir .env.prod (FORA do git)
# - docker + compose plugin instalados

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

echo "[deploy] Atualizando repo..."
git fetch --all --tags
git pull --ff-only

echo "[deploy] Subindo containers..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --build

echo "[deploy] Aplicando migrations..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T api alembic upgrade head

if [[ "${SEED_ON_DEPLOY:-false}" == "true" ]]; then
  echo "[deploy] Rodando seed (SEED_ON_DEPLOY=true)..."
  docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T api python -m app.scripts.seed
else
  echo "[deploy] Seed ignorado (SEED_ON_DEPLOY=false)."
fi

echo "[deploy] Status:"
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps

echo "[deploy] Healthcheck:"
curl -fsS "http://127.0.0.1/api/v1/health" >/dev/null && echo "OK: /api/v1/health via Nginx (HTTP)"

echo "[deploy] Done."
