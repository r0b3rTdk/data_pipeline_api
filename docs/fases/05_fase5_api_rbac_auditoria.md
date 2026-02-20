# Fase 5 — API “pronta para uso real” (Auth + RBAC + Auditoria + Métricas)

## Objetivos entregues
- Login (JWT) e dependency `get_current_user`
- RBAC por endpoint (`require_roles`)
- Auditoria de alteração em `trusted_event` via `audit_log`
- Endpoint de `security-events`
- Endpoint de `metrics`
- Padronização de `request_id` (middleware + headers)
- Testes mínimos com `pytest`

---

## 1) Auth (JWT)

### Endpoint
- **POST** `/api/v1/auth/login`

### Entrada
```json
{ "username": "admin", "password": "Admin@123" }
```

### Saída
```json
{ "access_token": "<JWT>" }
```

### O que o token carrega
- `sub` (username)
- `uid` (id do usuário)
- `role` (papel)

### Como enviar o token
- Header:
  - `Authorization: Bearer <token>`

---

## 2) RBAC

### Implementação
- `get_current_user()` valida token e busca o usuário no DB
- `require_roles([...])` permite/nega acesso (**403**)

### Matriz (ajuste se você mudar regras)
- `GET /trusted` → `operator` / `analyst` / `admin`
- `GET /rejections` → `analyst` / `admin`
- `PATCH /trusted/{id}` → `admin`
- `GET /audit` → `auditor` / `admin`
- `GET /security-events` → `auditor` / `admin`
- `GET /metrics` → `admin`

---

## 3) Auditoria (`audit_log`)

### Tabela (campos principais)
- `trusted_event_id`
- `user_id`
- `action`
- `reason`
- `before_data`
- `after_data`
- `request_id`
- `created_at`

### Endpoint
- **PATCH** `/api/v1/trusted/{trusted_id}`

### Regras
- `reason` é **obrigatório**
- Atualiza apenas os campos enviados (ex.: `event_status`, `event_type`)
- Escreve `audit_log` com **before/after**
- Salva `request_id` (`request.state.request_id`)

### Exemplo de payload
```json
{ "reason": "corrigir status", "event_status": "APPROVED" }
```

---

## 4) Security events

### Endpoint
- **GET** `/api/v1/security-events`

### Permissões
- `auditor` / `admin`

### Filtros (se implementados no backend)
- `severity`
- `event_type`
- paginação

### Exemplos de eventos típicos
- `AUTH_FAILED` (ex.: `X-API-Key` ausente/inválida, `source` inválida etc.)

---

## 5) Metrics / KPIs

### Endpoint
- **GET** `/api/v1/metrics`

### Retorna (exemplo)
- `total_raw`
- `total_trusted`
- `total_rejected`
- `rejection_rate`
- `duplicates`
- `top_rejection_categories`

> Pode aceitar filtros de período se isso tiver sido implementado.

---

## 6) Request ID + Headers

- `x-request-id` sempre presente (gerado se não vier)
- `x-process-time-ms` com tempo de processamento
- O `request_id` é propagado para:
  - erros padronizados
  - `security_event` (quando aplicável)
  - `audit_log` (no PATCH de trusted)

---

## 7) Testes mínimos (pytest)

### Rodar
```bash
docker compose exec -e PYTHONPATH=/app api pytest -q
```
