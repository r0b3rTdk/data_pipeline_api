# Fase 6 — Produção leve / Hardening

## Objetivo
Aplicar hardening leve e melhorias de qualidade **sem inventar feature grande**:
- Configuração por ambiente (DEV/PROD) via `.env`
- Logging estruturado (JSON) com `request_id`
- Tratamento global de erros (HTTP/422/500) com resposta padronizada
- Segurança leve: **Security Headers** + (opcional) **CORS por env**
- Seed/bootstrap para “rodar fácil”
- Testes extras focados na Fase 6

---

## Como rodar (Docker)

### 1) Subir serviços
```bash
docker compose up -d --build
```

### 2) Migrations
```bash
docker compose exec api sh -c "alembic upgrade head"
```

### 3) Health
```powershell
Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/health"
```

---

## Configuração por ambiente (DEV/PROD)

### Variáveis de ambiente
Crie um `.env` baseado no `.env.example`.

Sugestão (Fase 6):
- `APP_ENV=dev|prod`
- `LOG_LEVEL=INFO`
- `DATABASE_URL=...`
- `JWT_SECRET=...`
- `CORS_ORIGINS=http://localhost:3000` (opcional, CSV)
- Seed:
  - `SEED_ADMIN_USERNAME=admin`
  - `SEED_ADMIN_PASSWORD=admin123`
  - `SEED_SOURCE_NAME=partner_a`
  - `SEED_SOURCE_API_KEY=partner_a_key_change_me`

> No Docker, o host do Postgres é `db` (nome do serviço).

---

## Logging estruturado (JSON)

### O que sai no log
Para cada request, a API loga uma linha JSON com:
- `request_id`
- `path`
- `method`
- `status_code`
- `process_time_ms`

Isso permite rastrear um request específico pelo `X-Request-Id`.

---

## Tratamento global de erros (handlers)

### Padrão de resposta
- `HTTPException` e erros gerados pelo framework (ex: 404) retornam:
```json
{ "detail": "...", "code": "HTTP_ERROR", "request_id": "..." }
```

- Erro 422 (validação) retorna:
```json
{ "detail": "Validation error", "code": "VALIDATION_ERROR", "errors": [...], "request_id": "..." }
```

- Erro 500 (inesperado) retorna:
```json
{ "detail": "Internal server error", "code": "INTERNAL_ERROR", "request_id": "..." }
```

---

## Segurança extra leve (Fase 6)

### Security Headers
As respostas incluem:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

### (Opcional) CORS por env
Se `CORS_ORIGINS` estiver configurado, o app habilita CORS para as origens definidas (CSV).

---

## Seed / Bootstrap

### Rodar seed (recomendado)
Cria automaticamente (se não existir):
- usuário `admin` (role admin)
- source `partner_a` ativa com `api_key_hash`

```bash
docker compose exec api python -m app.scripts.seed
```

---

## Testes (Fase 6)

Rodar no container:
```bash
docker compose exec -e PYTHONPATH=/app api pytest -q
```

Testes adicionados na Fase 6:
- valida 422 padronizado com `code` + `request_id`
- valida 404 padronizado com `code` + `request_id`
- valida headers `X-Request-Id` e `X-Process-Time-Ms`

---

## Checklist de validação final (Fase 6 pronta)

- [ ] `docker compose up -d --build` OK
- [ ] `alembic upgrade head` OK
- [ ] `/api/v1/health` OK
- [ ] 422 retorna `{code, request_id, errors}` OK
- [ ] 404 retorna `{code, request_id}` OK
- [ ] Logs mostram `request_id` e `status_code`
- [ ] Security headers presentes
- [ ] Seed executa sem erro e é idempotente
- [ ] `pytest` passa no container
