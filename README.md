# Projeto01 — Data Pipeline API (RAW → TRUSTED → REJEIÇÕES) | Fase 4 (Security + RBAC básico)

Plataforma mínima e funcional para **ingestão**, **validação**, **idempotência/deduplicação**, **persistência relacional**, **registro de rejeições** e **consulta** via API — agora com **autenticação por API Key** e **trilha de auditoria (security_event)**.

## Visão rápida

**Fluxo:** `POST /ingest`  
1) **Auth (Fase 4):** exige `X-API-Key` e valida contra `source_system.api_key_hash`  
2) **Pipeline (Fase 3):** grava **RAW** sempre → se válido grava **TRUSTED** → se inválido grava **REJECTION(s)** → se repetido retorna **DUPLICATE**

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

## Migrations (Alembic)

Este projeto usa **Alembic** para versionar o schema do Postgres.

- Migrations:
  - `app/infra/db/migrations/versions/`

Aplicar migrations (dentro do container da API):
```bash
docker compose exec api sh -c "alembic upgrade head"
```

**Fase 4 adiciona/cria:**
- `source_system.api_key_hash` + índice `ix_source_system_api_key_hash`
- `user_account` (RBAC básico)
- `security_event` (auditoria e eventos de segurança)

> Importante: mantenha as migrations no código do Windows (repo). Não confie em migrations criadas só “dentro do container”.

---

## Autenticação por API Key (Fase 4)

### Conceito
- Cada integração/fonte fica em `source_system` com `name`, `status` e `api_key_hash`.
- O cliente **envia a API Key em texto puro** no header `X-API-Key`.
- A API **nunca salva a key** — só salva o **hash** (`sha256` hex) em `source_system.api_key_hash`.

### Gerar API Key + Hash (dentro do container da API)
```bash
docker compose exec api python -c "from app.core.security import generate_api_key, hash_api_key; k=generate_api_key('src'); print('API_KEY='+k); print('HASH='+hash_api_key(k))"
```

### Salvar o HASH no banco (para uma source existente)
Exemplo: `partner_a`
```bash
docker compose exec db psql -U appuser -d appdb -c "UPDATE source_system SET api_key_hash = '<COLE_O_HASH_AQUI>' WHERE name = 'partner_a';"
```

Confirmar:
```bash
docker compose exec db psql -U appuser -d appdb -c "SELECT id, name, status, api_key_hash FROM source_system WHERE name='partner_a';"
```

---

## Endpoints

### Health
- `GET /api/v1/health` → `{"status":"ok"}`

### Ingestão (protegida por API Key)
- `POST /api/v1/ingest`

**Regras de negócio do event_type (Fase 3):**
- Tipos permitidos (ALLOWED_TYPES): `ORDER`, `PAYMENT`, `SHIPMENT`

#### Exemplo (PowerShell) — **SUCESSO**
```powershell
$headers_ok = @{ "X-API-Key" = "SUA_API_KEY_AQUI" }

$body_ok_obj = @{
  source = "partner_a"
  external_id = "ext-OK-" + (Get-Random)
  entity_id = "ent-OK-010"
  event_status = "NEW"
  event_timestamp = "2026-02-04T00:10:00Z"
  event_type = "ORDER"
  severity = "low"
  payload = @{ x = 999 }
}

$body_ok = $body_ok_obj | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/ingest" `
  -Headers $headers_ok `
  -ContentType "application/json" `
  -Body $body_ok
```

**Respostas esperadas:**
- `ACCEPTED` → cria RAW e TRUSTED
- `DUPLICATE` → cria RAW e retorna duplicado (sem novo TRUSTED)
- `REJECTED` → cria RAW e REJECTION(s)

#### Exemplo (PowerShell) — **NEGATIVO (sem header)**
```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/ingest" `
  -ContentType "application/json" `
  -Body $body_ok
```
Esperado: `401` com `{"detail":"missing X-API-Key"}` + grava em `security_event`.

#### Exemplo (PowerShell) — **NEGATIVO (API Key inválida)**
```powershell
$headers_bad = @{ "X-API-Key" = "INVALIDA" }

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/ingest" `
  -Headers $headers_bad `
  -ContentType "application/json" `
  -Body $body_ok
```
Esperado: `401` com `{"detail":"invalid api key"}` + grava em `security_event`.

---

## Consultas (Fase 3)

### Consulta TRUSTED (paginado)
- `GET /api/v1/trusted?page=1&page_size=50`

```powershell
Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/trusted?page=1&page_size=50"
```

### Consulta REJEIÇÕES (paginado)
- `GET /api/v1/rejections?page=1&page_size=50`

```powershell
Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/rejections?page=1&page_size=50"
```

---

## Auditoria / Security Events (Fase 4)

Quando a autenticação falha, a API registra um evento em `security_event` (ex.: `AUTH_FAILED`, severidade `HIGH`).

Ver últimos eventos:
```bash
docker compose exec db psql -U appuser -d appdb -c "SELECT id, event_type, severity, source_id, user_id, ip, user_agent, request_id, details, created_at FROM security_event ORDER BY id DESC LIMIT 10;"
```

---

## Estrutura (essencial)

- `app/main.py` — cria `app = FastAPI()` e registra routers
- `app/api/routes/*` — rotas (ingest, trusted, rejections, health)
- `app/api/schemas/*` — schemas de request/response
- `app/services/*` — regra de negócio (ingest pipeline)
- `app/api/deps.py` — deps de autenticação/segurança (API key)
- `app/infra/db/*` — models, session, repositories
- `app/infra/db/migrations/*` — Alembic

---

## Troubleshooting (PowerShell)

- **`curl` no PowerShell** é alias de `Invoke-WebRequest` → prefira `Invoke-RestMethod` ou `curl.exe`.
- Se aparecer **`{"detail":[{"loc":["body"],"msg":"Field required"}]}`**, geralmente é porque a variável `$body_*` está `null` ou você está passando um objeto em vez de JSON string.
  - Refaça sempre: `$body = $obj | ConvertTo-Json -Depth 10`
- Para comandos SQL / `\d` do Postgres: use sempre `psql -c "..."` (não rode SQL direto no PowerShell).

---

## Definition of Done (Fase 4)

- `POST /api/v1/ingest`:
  - sem `X-API-Key` → `401` **sem 500** + grava `security_event`
  - com key inválida → `401` **sem 500** + grava `security_event`
  - com key válida → fluxo normal `ACCEPTED/DUPLICATE/REJECTED`
- Tabelas existem no Postgres:
  - `source_system`, `raw_ingestion`, `trusted_event`, `rejection`, `user_account`, `security_event`, `alembic_version`
- `GET /api/v1/trusted`, `GET /api/v1/rejections`, `GET /api/v1/health` funcionando
- Docker sobe com `docker compose up -d --build`

---

## Autor

**Robert Emanuel**  
Back-end Developer (Python/FastAPI • SQL • Docker • Segurança)
