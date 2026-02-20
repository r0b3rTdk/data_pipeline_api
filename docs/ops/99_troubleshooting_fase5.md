# Troubleshooting — Fase 5

## 1) PowerShell: “curl” não é curl
No PowerShell, `curl` é alias do `Invoke-WebRequest`.

Use:
- `Invoke-RestMethod` (recomendado), **ou**
- `curl.exe`

---

## 2) API não sobe / “Impossível conectar”

### Ver logs
```bash
docker compose ps
docker compose logs api --tail 200
```

### Causas comuns
- erro de import (`NameError` / `ImportError`)
- código executando no import (side effects)
- router com prefix duplicado (ex.: `/api/v1/api/v1/...`)

---

## 3) pytest: `ModuleNotFoundError: No module named 'app'`

### Rodar com `PYTHONPATH`
```bash
docker compose exec -e PYTHONPATH=/app api pytest -q
```

### Alternativa
- definir `PYTHONPATH=/app` no `docker-compose.yml` do serviço `api`

---

## 4) Alembic: “Can't locate revision”

### Checar versão atual
```bash
docker compose exec db psql -U appuser -d appdb -c "select version_num from alembic_version;"
```

### Causas comuns
- migration criada no container e **não persistida** (sem bind/volume)
- arquivo removido/renomeado após aplicado

---

## 5) `psql: not found`
O cliente `psql` geralmente não vem no container `api`.

Use o container `db`:
```bash
docker compose exec db psql -U appuser -d appdb
```

---

## 6) `request_id` não aparece no `audit_log` / `security_event`

### Checklist
- confirme middleware de `request_id` ativo
- no endpoint:
  - `rid = getattr(request.state, 'request_id', None)`
- passe `request_id=rid` para `create_audit_log` / `create_security_event`

### Testar headers no health
```bash
curl.exe -i "http://localhost:8000/api/v1/health"
```

---

## 7) “forbidden” (403) inesperado

### Confirmar role do usuário
```bash
docker compose exec db psql -U appuser -d appdb -c "select id, username, role, is_active from user_account;"
```

E confirme quais roles o endpoint aceita.

---

## 8) Login dá `invalid_credentials`

### Causas comuns
- usuário não existe
- `password_hash` incorreto

### Exemplo de update via container
```bash
docker compose exec -e PYTHONPATH=/app api python -c "from app.infra.db.session import get_db; from app.infra.db.repositories.user_repo import get_user_by_username; from app.core.security import hash_password; db=next(get_db()); u=get_user_by_username(db,'admin'); u.password_hash=hash_password('Admin@123'); u.role='admin'; u.is_active=True; db.commit(); print('OK')"
```
