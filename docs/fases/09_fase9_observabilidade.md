# Fase 9 — Observabilidade 

Este documento descreve **o que foi implementado na Fase 9 (Observabilidade)**, como **validar** e como **testar** localmente via Docker.

---

## Objetivo

Melhorar a capacidade de **operar, monitorar e diagnosticar** o sistema através de:

- **Readiness** real (API + DB)
- **Logs estruturados** com campos suficientes para investigação
- **Métricas operacionais** agregadas (uptime/requests/erros)
- **Latência por rota** (média e contagem)

---

## 1) Endpoint de Readiness

### Rota

`GET /api/v1/ready`

### Comportamento

- Valida se a **API está viva**
- Valida conectividade com o **PostgreSQL**
  - Executa: `SELECT 1`
- Se o banco falhar, retorna **HTTP 503**

### Resposta esperada (DB OK)

```json
{
  "status": "ok",
  "checks": {
    "api": "ok",
    "db": "ok"
  },
  "request_id": "..."
}
```

### Resposta esperada (DB FAIL)

- HTTP `503`

```json
{
  "status": "fail",
  "checks": {
    "api": "ok",
    "db": "fail"
  },
  "request_id": "..."
}
```

### Teste rápido (Windows / PowerShell)

> **Atenção:** no ambiente local com Docker, a API está exposta em `:8000`.

```powershell
curl.exe -i "http://localhost:8000/api/v1/ready"
```

---

## 2) Logs estruturados (JSON)

### Onde

- Logs do container da API:
  - `docker compose logs -f api`

### O que foi melhorado

Cada request gera um log JSON com informações suficientes para diagnóstico, incluindo:

- `ts`, `level`, `message`, `logger`
- `request_id`
- `method`, `path`, `status_code`, `process_time_ms`
- `client_ip`, `user_agent`
- `user_id`, `role` (**quando autenticado**)

Exemplo real de log:

```json
{
  "ts": "2026-03-05T05:31:52.840648+00:00",
  "level": "INFO",
  "message": "request",
  "logger": "app.request",
  "request_id": "4f71b41a250a44de851b32e22bf5c01e",
  "path": "/api/v1/metrics",
  "method": "GET",
  "status_code": 200,
  "process_time_ms": 37,
  "client_ip": "172.18.0.1",
  "user_agent": "curl/8.13.0",
  "user_id": 1,
  "role": "admin"
}
```

### Regras de segurança

**Nunca** logar:

- senha
- JWT
- API key
- secrets

---

## 3) Métricas operacionais em `/metrics`

### Rota

`GET /api/v1/metrics` (protegida por RBAC)

### Blocos retornados

#### (a) Métricas de negócio (já existiam)

- `total_raw`
- `total_trusted`
- `total_rejected`
- `duplicates`
- `rejection_rate`
- `top_rejection_categories` (ranking)

#### (b) Métricas operacionais (Fase 9)

Campo novo: `http`

```json
"http": {
  "uptime_seconds": 110,
  "requests_total": 4,
  "errors_4xx_total": 1,
  "errors_5xx_total": 0
}
```

- `uptime_seconds`: tempo que o processo está no ar
- `requests_total`: total de requests atendidas
- `errors_4xx_total`: total de respostas 4xx
- `errors_5xx_total`: total de respostas 5xx

> Observação: os contadores são **in-memory** (reiniciam junto com o container).

---

## 4) Latência por endpoint (opcional implementado)

Campo novo: `http_routes`

Exemplo:

```json
"http_routes": {
  "POST /api/v1/auth/login": { "count": 2, "avg_ms": 41.5 },
  "GET /api/v1/ready": { "count": 3, "avg_ms": 18.3 }
}
```

- `count`: quantas vezes a rota foi chamada
- `avg_ms`: média de latência em milissegundos

A rota usada é o **template** do framework sempre que possível (ex: `/trusted/{trusted_id}`), evitando explodir cardinalidade por IDs.

---

## 5) Como validar o fluxo completo (curto e prático)

### 1) Readiness

```powershell
curl.exe -i "http://localhost:8000/api/v1/ready"
```

### 2) Login (gerar JWT)

```powershell
curl.exe -s -X POST "http://localhost:8000/api/v1/auth/login" `
  -H "Content-Type: application/json" `
  -d '{ "username": "admin", "password": "Admin@123" }'
```

Guarde o `access_token`.

### 3) Chamar `/metrics` com Bearer

```powershell
$token = "<COLE_O_ACCESS_TOKEN>"
curl.exe -i "http://localhost:8000/api/v1/metrics" -H "Authorization: Bearer $token"
```

---

## 6) Testes automatizados (Pytest)

### Rodar dentro do container

```powershell
docker compose exec -e PYTHONPATH=/app api pytest -q
```

Cobertura da Fase 9:

- `/ready` retorna 200 quando DB está OK
- `/ready` retorna 503 quando DB falha (mock)
- `/metrics` inclui `http` e `http_routes`
- Headers `X-Request-Id` e `X-Process-Time-Ms` presentes
- RBAC / Auth continuam funcionando

---

## 7) Comandos úteis

### Subir ambiente

```powershell
docker compose up -d --build
```

### Ver logs

```powershell
docker compose logs -f api
```

### Abrir docs (Swagger)

- `http://localhost:8000/docs`

---

## Status da Fase 9

✅ `/api/v1/ready` implementado  
✅ logs estruturados enriquecidos  
✅ métricas operacionais (`http`) em `/metrics`  
✅ latência por rota (`http_routes`) em `/metrics`  
✅ testes automatizados passando
