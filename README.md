# Projeto01 — Data Pipeline (RAW → TRUSTED → REJEIÇÕES) | Fase 3 (V1)

Plataforma mínima e funcional para **ingestão**, **validação**, **idempotência/deduplicação**, **persistência relacional**, **registro de rejeições** e **consulta** via API.

## Visão rápida

**Fluxo:** `POST /ingest` → grava **RAW** sempre → se válido grava **TRUSTED** → se inválido grava **REJECTION** → se repetido retorna **DUPLICATE** (sem novo TRUSTED)

**Stack:** Python (FastAPI) + Postgres + SQLAlchemy + Alembic + Docker Compose

---

## Como rodar (Docker)

### 1) Subir serviços
```bash
docker compose up -d --build
```

### 2) Verificar saúde
```powershell
Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/health"
```

### 3) (Opcional) Ver logs
```bash
docker compose logs -n 200 api
docker compose logs -n 200 db
```

---

## Endpoints (Fase 3)

### Health
- `GET /api/v1/health` → `{"status":"ok"}`

### Ingestão
- `POST /api/v1/ingest`

**Exemplo (PowerShell):**
```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/ingest" `
  -ContentType "application/json" `
  -Body '{"source":"partner_a","external_id":"ext-1","schema_version":"v1","entity_id":"ent-1","event_type":"ORDER","event_status":"NEW","event_timestamp":"2026-01-29T12:00:00Z","attributes":{"x":1}}'
```

**Respostas esperadas:**
- `ACCEPTED` → cria RAW e TRUSTED
- `DUPLICATE` → cria RAW (e retorna duplicado) sem novo TRUSTED
- `REJECTED` → cria RAW e REJECTION(s)

### Consulta TRUSTED (paginado + filtros)
- `GET /api/v1/trusted?page=1&page_size=50`
- Filtros (quando implementados no seu router): `source`, `external_id`, `event_status`, `date_from`, `date_to`

Exemplo:
```powershell
Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/trusted?page=1&page_size=50"
```

### Consulta REJEIÇÕES (paginado + filtros)
- `GET /api/v1/rejections?page=1&page_size=50`
- Filtros: `category`, `severity`

Exemplo:
```powershell
Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/rejections?page=1&page_size=50"
```

---

## Migrations (Alembic)

Este projeto usa **Alembic** para versionar o schema do Postgres.

- As migrations ficam em:
  - `app/infra/db/migrations/versions/`

Para aplicar migrations (dentro do container da API):
```bash
docker compose exec api sh -c "alembic upgrade head"
```

> Importante: **sempre mantenha as migrations no código do Windows (repo)**. Não confie em migrations criadas apenas “dentro do container”.

---

## Estrutura (Fase 3 - essencial)

- `app/main.py` — cria `app = FastAPI()` e registra routers
- `app/api/routes/*` — rotas (ingest, trusted, rejections, health)
- `app/api/schemas/*` — schemas de request/response
- `app/services/*` — regra de negócio (ingest pipeline)
- `app/infra/db/*` — models, session, repositories
- `app/infra/db/migrations/*` — Alembic

---

## Troubleshooting

Veja: **docs/99_troubleshooting_fase3.md** (erros reais + correções).

---

## Definition of Done (Fase 3)

- `POST /api/v1/ingest` retorna `ACCEPTED`, `DUPLICATE`, `REJECTED`
- Tabelas existem no Postgres: `source_system`, `raw_ingestion`, `trusted_event`, `rejection`, `alembic_version`
- `GET /api/v1/trusted` e `GET /api/v1/rejections` paginados
- `GET /api/v1/health` retorna `ok`
- Docker sobe com `docker compose up -d --build`

---

## Autor

**Robert Emanuel**  
Back-end Developer (Python/FastAPI • SQL • Docker • Segurança)

---
