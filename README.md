# Projeto01 — Data Pipeline API (RAW → TRUSTED → REJEIÇÕES) + Segurança + Front (Fase 6 + Fase 7)

Plataforma mínima e funcional para **ingestão**, **validação**, **idempotência/deduplicação**, **persistência relacional**, **registro de rejeições** e **consulta** via API — com **segurança** (API Key por fonte), **login JWT**, **RBAC**, **auditoria**, **security events**, **request-id**, **métricas simples** e **testes mínimos**.

---

## Visão rápida

### Fluxo de ingestão (RAW → TRUSTED / REJECTION)
**Endpoint:** `POST /api/v1/ingest`

1) **Auth por fonte (Fase 4/5):** exige `X-API-Key` e valida contra `source_system.api_key_hash`  
2) **Pipeline:** grava **RAW** sempre → se válido grava **TRUSTED** → se inválido grava **REJECTION(s)** → se repetido retorna **DUPLICATE**  

### Stack
- **FastAPI**
- **Postgres (Docker)**
- **SQLAlchemy + Alembic**
- **Auth:** API Key (por source) + **JWT** (login de usuário)
- **RBAC** (roles)
- **Auditoria:** `audit_log`
- **Security events:** `security_event`
- **Observabilidade:** `x-request-id` + `x-process-time-ms` + `/metrics`
- **Testes mínimos:** `pytest`

---

## Como rodar (Docker)

### 1) Subir serviços
```bash
docker compose up -d --build
```

### 2) Health
```powershell
Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/health"
```

### 3) OpenAPI
- `http://localhost:8000/docs`
- `http://localhost:8000/openapi.json`

### 4) (Opcional) Logs
```bash
docker compose logs -n 200 api
docker compose logs -n 200 db
```


---

## Como rodar o Front (Fase 7)

### Opção 1 — Dev simples (recomendado)
1) Suba a API normalmente (Docker):
```bash
docker compose up -d
```

2) Suba o front (estático) em outro terminal:
```bash
cd frontend
python -m http.server 3000
```

Acesse:
- Front: http://localhost:3000
- API: http://localhost:8000/docs

> **Config**: `frontend/config.js` → `API_BASE_URL` (padrão: `http://localhost:8000`)

### Login (JWT) no Front
- Tela chama: `POST /api/v1/auth/login`
- Token é salvo no `localStorage` em `p01_access_token`
- Se a API retornar `401`, o front limpa o token e volta para `#/login`

### Telas do Front
- Dashboard: `#/dashboard` (KPIs via `GET /api/v1/metrics`)
- Trusted: `#/trusted` (lista + detalhes)
- Rejections: `#/rejections` (lista + detalhes)
- Security Events: `#/security-events` (lista + filtros: `severity`, `event_type`)
- Audit Logs: `#/audit` (lista + filtros: `action`, `entity_type`, `user_id`)

---

---

## Variáveis de ambiente

Crie um `.env` baseado no `.env.example`.

Exemplo de `.env.example`:
```env
DATABASE_URL=postgresql+psycopg://appuser:apppass@db:5432/appdb
APP_ENV=local

# JWT
JWT_SECRET=change-me
JWT_ALG=HS256
JWT_EXPIRES_MIN=60
```

> No Docker, o host do Postgres é `db` (nome do serviço).

---

## Migrations (Alembic)

Aplicar migrations (dentro do container da API):
```bash
docker compose exec api sh -c "alembic upgrade head"
```

Criar revision:
```bash
docker compose exec api alembic revision -m "mensagem"
```

Ver tabelas:
```bash
docker compose exec db psql -U appuser -d appdb -c "\dt"
```

### Estrutura de migrations
- `app/infra/db/migrations/versions/`

> Importante: mantenha as migrations no código do Windows (repo). Não confie em migrations criadas só “dentro do container”.

---

## Autenticação por API Key (por fonte)

### Conceito
- Cada integração/fonte fica em `source_system` com `name`, `status` e `api_key_hash`.
- O cliente envia a API Key em texto puro no header `X-API-Key`.
- A API **não salva a key**, apenas o **hash** (`sha256` hex) em `source_system.api_key_hash`.

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

## Auth (login) — JWT

### Login
```powershell
$loginBody = @{ username="admin"; password="Admin@123" } | ConvertTo-Json

$resp = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/auth/login" `
  -ContentType "application/json" `
  -Body $loginBody

$token = $resp.access_token
$headers = @{ Authorization = "Bearer $token" }
```

---

## RBAC (permissões por endpoint)

Sugestão de matriz (ajuste conforme sua config):
- `GET /api/v1/trusted` → `operator`, `analyst`, `admin`
- `GET /api/v1/rejections` → `analyst`, `admin`
- `PATCH /api/v1/trusted/{trusted_id}` → `admin`
- `GET /api/v1/audit` → `auditor`, `admin`
- `GET /api/v1/security-events` → `auditor`, `admin`
- `GET /api/v1/metrics` → `admin` (ou conforme sua config)

---

## Endpoints

### Health
- `GET /api/v1/health` → `{"status":"ok"}`

### Ingestão (protegida por API Key)
- `POST /api/v1/ingest`

**Regras de negócio do event_type:**
- Tipos permitidos (ALLOWED_TYPES): `ORDER`, `PAYMENT`, `SHIPMENT`

#### Exemplo (PowerShell) — SUCESSO (Ingest)
```powershell
$headersIngest = @{ "X-API-Key" = "SUA_API_KEY_AQUI" }

$body_ok_obj = @{
  source = "partner_a"
  external_id = "ext-OK-" + (Get-Random)
  entity_id = "ent-OK-010"
  event_status = "NEW"
  event_timestamp = "2026-02-10T00:00:00Z"
  event_type = "ORDER"
  severity = "low"
  payload = @{ a = 1 }
}

$body_ok = $body_ok_obj | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/ingest" `
  -Headers $headersIngest `
  -ContentType "application/json" `
  -Body $body_ok
```

**Respostas esperadas:**
- `ACCEPTED` → cria RAW e TRUSTED
- `DUPLICATE` → cria RAW e retorna duplicado (sem novo TRUSTED)
- `REJECTED` → cria RAW e REJECTION(s)

#### Exemplo — NEGATIVO (sem header)
```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/ingest" `
  -ContentType "application/json" `
  -Body $body_ok
```
Esperado: `401` com `{"detail":"missing X-API-Key"}` + grava em `security_event`.

#### Exemplo — NEGATIVO (API Key inválida)
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

## Consultas (TRUSTED / REJEIÇÕES)

### GET TRUSTED (paginado)
- `GET /api/v1/trusted?page=1&page_size=50`
```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://localhost:8000/api/v1/trusted?page=1&page_size=50" `
  -Headers $headers
```

### GET REJEIÇÕES (paginado)
- `GET /api/v1/rejections?page=1&page_size=50`
```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://localhost:8000/api/v1/rejections?page=1&page_size=50" `
  -Headers $headers
```

---

## PATCH TRUSTED (auditoria)

- `PATCH /api/v1/trusted/{trusted_id}`
```powershell
$patchBody = @{ reason="corrigir status"; event_status="APPROVED" } | ConvertTo-Json

Invoke-RestMethod -Method Patch `
  -Uri "http://localhost:8000/api/v1/trusted/5" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $patchBody
```

---

## Auditoria (audit_log)

- `GET /api/v1/audit?page=1&page_size=50`
```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://localhost:8000/api/v1/audit?page=1&page_size=50" `
  -Headers $headers
```

---

## Security Events (security_event)

Quando autenticação falha (API Key/JWT/RBAC), a API registra eventos (ex.: `AUTH_FAILED`, severidade `HIGH`).

### API
- `GET /api/v1/security-events?severity=HIGH&event_type=AUTH_FAILED&page=1&page_size=50`
```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://localhost:8000/api/v1/security-events?severity=HIGH&event_type=AUTH_FAILED&page=1&page_size=50" `
  -Headers $headers
```

### SQL (últimos eventos)
```bash
docker compose exec db psql -U appuser -d appdb -c "SELECT id, event_type, severity, source_id, user_id, ip, user_agent, request_id, details, created_at FROM security_event ORDER BY id DESC LIMIT 10;"
```

---

## Métricas (observabilidade básica)

- `GET /api/v1/metrics`
```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://localhost:8000/api/v1/metrics" `
  -Headers $headers
```

---

## Headers de rastreio (Request ID)

Toda resposta inclui:
- `x-request-id`
- `x-process-time-ms`

Use `x-request-id` para rastrear logs/auditoria/security_event.

---

## Testes

Rodar dentro do container:
```bash
docker compose exec -e PYTHONPATH=/app api pytest -q
```

---

## Estrutura do projeto (essencial)

- `app/main.py` — cria `app = FastAPI()` e registra routers
- `app/api/routes/*` — rotas (ingest, trusted, rejections, auth, audit, security-events, metrics, health)
- `app/api/schemas/*` — schemas de request/response
- `app/services/*` — regra de negócio (pipeline ingest)
- `app/api/deps.py` — deps de autenticação/segurança (API key, JWT, roles)
- `app/infra/db/*` — models, session, repositories
- `app/infra/db/migrations/*` — Alembic

---

## Documentação

- `docs/07_fase7_front_dashboard.md` — como rodar e usar o Front (Fase 7)
- `docs/99_troubleshooting_fase7.md` — erros comuns do Front (CORS, 401, base url, etc)

## Troubleshooting (PowerShell)

- **`curl` no PowerShell** é alias de `Invoke-WebRequest` → prefira `Invoke-RestMethod` ou `curl.exe`.
- Se aparecer **`{"detail":[{"loc":["body"],"msg":"Field required"}]}`**, geralmente `$body_*` está `null` ou você passou objeto em vez de JSON string.
  - Sempre: `$body = $obj | ConvertTo-Json -Depth 10`
- Para SQL / `\d` do Postgres: use `psql -c "..."` (não rode SQL direto no PowerShell).
- Veja também: `docs/99_troubleshooting_fase5.md`

---

## Definition of Done

### Fase 4 (Security + base)
- `POST /api/v1/ingest`:
  - sem `X-API-Key` → `401` (sem 500) + grava `security_event`
  - key inválida → `401` (sem 500) + grava `security_event`
  - key válida → fluxo `ACCEPTED/DUPLICATE/REJECTED`
- Tabelas no Postgres:
  - `source_system`, `raw_ingestion`, `trusted_event`, `rejection`, `user_account`, `security_event`, `alembic_version`
- `GET /api/v1/trusted`, `GET /api/v1/rejections`, `GET /api/v1/health` funcionando
- Docker sobe com `docker compose up -d --build`

### Fase 6 (Hardening leve)
- Logs em JSON
- Seed idempotente (admin + source default)
- Headers de segurança básicos
- Testes passando no container

### Fase 7 (Front Admin)
- Front roda em `http://localhost:3000` e consome API em `http://localhost:8000`
- Login JWT no front + armazenamento de token
- Dashboard (metrics) + Trusted + Rejections + Security Events (filtros) + Audit Logs (filtros)

### Fase 5 (Auth JWT + RBAC + observabilidade + testes)
- `POST /api/v1/auth/login` retorna `access_token` JWT
- RBAC aplicado conforme matriz (ou equivalente)
- `PATCH /api/v1/trusted/{id}` registra `audit_log`
- `GET /api/v1/audit` e `GET /api/v1/security-events` funcionam com autorização
- Respostas incluem `x-request-id` e `x-process-time-ms`
- `/metrics` disponível e protegido
- `pytest -q` roda (mínimo) sem falhas no container

---

## Autor

**Robert Emanuel**  
Back-end Developer (Python/FastAPI • SQL • Docker • Segurança)
