# Troubleshooting — Fase 6

## 1) API não responde / connection refused
**Sintoma**
- `curl: (7) Failed to connect...`
- `Empty reply from server`

**Causas comuns**
- container `api` caiu por erro de import/startup

**Como investigar**
```bash
docker compose ps
docker compose logs api --tail=200
```

---

## 2) ImportError em middleware/handlers
**Sintoma**
- `ImportError: cannot import name ...`

**Correção**
- Confirme que o nome da classe/função no arquivo bate com o import no `main.py`.
Ex:
- `SecurityHeadersMiddleware` deve existir no `security_headers.py`.

---

## 3) 404 não vem padronizado (sem `code`)
**Causa**
- 404 é gerado pelo Starlette, não pelo `fastapi.HTTPException`.

**Correção**
- Registre handler também para:
  - `starlette.exceptions.HTTPException as StarletteHTTPException`

---

## 4) PowerShell + curl
No PowerShell, `curl` é alias de `Invoke-WebRequest`. Prefira:
- `Invoke-RestMethod`
- ou `curl.exe`

Se quiser mandar JSON com `curl.exe` sem dor:
```powershell
'{"username":"x"}' | Out-File -Encoding ascii .\body.json
curl.exe -i -X POST "http://localhost:8000/api/v1/auth/login" -H "Content-Type: application/json" --data-binary "@body.json"
```

---

## 5) Erro 422 com `json_invalid`
**Causa**
- JSON chegou quebrado (escape/aspas do PowerShell)

**Correção**
- Use `Invoke-RestMethod` com `ConvertTo-Json`
- ou a técnica do arquivo acima

---

## 6) DATABASE_URL vazio / engine falha
**Sintoma**
- erro na criação do engine do SQLAlchemy

**Correção**
- confira `.env` (ou envs do compose)
```bash
docker compose exec api sh -c "env | sort | grep DATABASE_URL"
```

---

## 7) Logs não mostram JSON / request_id
**Causa**
- `setup_logging()` não foi chamado
- log por request não foi adicionado no middleware

**Correção**
- confira `setup_logging(settings.LOG_LEVEL)` no `main.py`
- confira `logger.info(... extra={request_id,...})` no `RequestIdMiddleware`

---

## 8) Seed não cria admin/source
**Correção**
- rode manualmente:
```bash
docker compose exec api python -m app.scripts.seed
```
- confira envs:
  - `SEED_ADMIN_USERNAME`, `SEED_ADMIN_PASSWORD`
  - `SEED_SOURCE_NAME`, `SEED_SOURCE_API_KEY`
