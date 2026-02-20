# docs/99_troubleshooting_fase4.md — Erros reais da Fase 4 (Security + API Key + RBAC básico) + Como corrigir

Este arquivo registra **enroscos reais** que aconteceram durante a **Fase 4** e como foram resolvidos.
A ideia é colar isso no repo (igual você fez na Fase 3) para mostrar maturidade em debug e troubleshooting.

---

## 01) `NoReferencedTableError`: FK para `user_account` não encontra a tabela

**Sintoma (logs)**
- `sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 'security_event.user_id' could not find table 'user_account' ...`

**Causa**
- O model `SecurityEvent` tinha FK `user_account.id`, mas:
  - o model `UserAccount` não estava importado/registrado no `Base.metadata`, **ou**
  - a migration não foi aplicada/estava fora de ordem, **ou**
  - havia discrepância entre nomes (`user_account` vs outro nome).

**Correção**
- Garantir que existe o model `UserAccount` e ele é importado em algum ponto que “carrega” todos os models (ex.: `app/infra/db/base.py`).
- Garantir que a migration `0647cc47ea66_fase4_security_models.py` foi aplicada:
  ```powershell
  docker compose exec db psql -U appuser -d appdb -c "select * from alembic_version;"
  docker compose exec db psql -U appuser -d appdb -c "\dt"
  ```

---

## 02) `TypeError: 'source' is an invalid keyword argument for SecurityEvent`

**Sintoma**
- No caminho do `deny()` (quando API key é inválida/ausente), a API retornava **500**.
- Logs mostravam que a criação do `SecurityEvent` explodia com keyword inválida.

**Causa**
- O repositório ou o `create_security_event(...)` passava argumentos que **não existem** no model (ex.: `source="partner_a"` em vez de `source_id`).

**Correção**
- Ajustar o repositório para usar **somente campos válidos** do model:
  - `event_type, severity, source_id, user_id, ip, user_agent, request_id, details, created_at`
- Resultado esperado:
  - Fluxo negativo retorna **401/403** (não 500)
  - E grava um registro em `security_event`.

---

## 03) `AttributeError: 'Header' object has no attribute 'encode'` ao validar API key

**Sintoma (logs)**
- `AttributeError: 'Header' object has no attribute 'encode'`
- Explodia em `hash_api_key(api_key)`.

**Causa**
- O parâmetro `x_api_key` foi tipado/definido como dependência de `Header(...)`, mas acabou sendo passado o **objeto Header** ao invés da **string** real.

**Correção (robusta e simples)**
- Ler do `request.headers` diretamente (case-insensitive):
  ```py
  x_api_key = request.headers.get("X-API-Key")
  ```
- Só então chamar `verify_api_key(x_api_key, src.api_key_hash)`.

---

## 04) Teste negativo OK, mas `security_event.details` não tinha `request_id`

**Sintoma**
- Você consultou:
  ```sql
  where details->>'request_id' = '...'
  ```
  e não encontrou nada.

**Causa**
- Você não enviou `X-Request-Id` nos requests; então `request.headers.get("x-request-id")` era `null`.
- Além disso, `request_id` estava sendo salvo **dentro de `details`**, não na coluna `security_event.request_id` (dependendo da implementação).

**Correção (opcional / melhoria)**
- Se você quiser o `request_id` como coluna também, passe `request_id=...` no insert do SecurityEvent.
- E/ou envie `X-Request-Id` no PowerShell:
  ```powershell
  $headers_ok = @{ "X-API-Key" = "<API_KEY>"; "X-Request-Id" = [guid]::NewGuid().ToString("N") }
  ```

---

## 05) `psql` travando em `(END)` quando a query retorna muitos registros

**Sintoma**
- O terminal mostra `(END)` e “parece travado”.

**Causa**
- Pager do `psql` ligado.

**Correção**
- Sair com `q`
- Ou desativar pager em uma query:
  ```powershell
  docker compose exec db psql -U appuser -d appdb -P pager=off -c "select 1;"
  ```

---

## 06) PowerShell: tentar rodar SQL/\d direto no PowerShell dá erro

**Sintoma**
- `-- comentário` dá erro de parser no PowerShell.
- `\d raw_ingestion` dá “cmdlet não reconhecido”.

**Causa**
- Você estava digitando comandos do `psql` **fora do `psql`** (no PowerShell).
- `\d` e comentários SQL precisam estar dentro do `psql` ou enviados via `psql -c`.

**Correção**
- Para ver colunas/tipos usando `psql -c`:
  ```powershell
  docker compose exec db psql -U appuser -d appdb -P pager=off -c "
  SELECT table_name, column_name, data_type
  FROM information_schema.columns
  WHERE table_name IN ('raw_ingestion','trusted_event','rejection','security_event')
  ORDER BY table_name, ordinal_position;"
  ```

---

## 07) `Invoke-RestMethod` retorna “Field required” (body nulo)

**Sintoma**
- FastAPI respondia:
  ```json
  {"detail":[{"type":"missing","loc":["body"],"msg":"Field required","input":null}]}
  ```

**Causa (quase sempre)**
- `$body_ok` estava **nulo** (variável sobrescrita / sessão reiniciada / comando em bloco que falhou antes).
- Ou você mandou `-Body $body_ok` sem ter gerado o JSON antes.
- Em outro ponto, você tentou alterar propriedade em hashtable usando sintaxe de objeto:
  - `$body_ok_obj.external_id = ...` → falha (hashtable não tem “property”, tem chave)

**Correção**
- Sempre reconstruir o body antes do POST (e checar tipo):
  ```powershell
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
  $body_ok.GetType().FullName   # tem que ser System.String
  ```

- Para alterar **chave** de hashtable:
  ```powershell
  $body_ok_obj["external_id"] = "ext-OK-" + (Get-Random)
  ```

---

## 08) `Invoke-RestMethod` dizia “missing X-API-Key” mesmo com header

**Sintoma**
- Você jurava que mandou header, mas a API respondia `"missing X-API-Key"`.

**Causa**
- `$headers_ok` estava **nulo** (variável perdida/sobrescrita), ou foi criado com tipo estranho e não chegou certo.

**Correção**
- Recriar como hashtable simples:
  ```powershell
  $headers_ok = @{ "X-API-Key" = "<API_KEY_VALIDA>" }
  ```
- Sanity:
  ```powershell
  $headers_ok["X-API-Key"]
  ```

---

## 09) `invalid source` / `invalid api key` no ingest

**Sintoma**
- `{"detail":"invalid source"}` ou `{"detail":"invalid api key"}` (401).

**Causa**
- A `source` do payload não existia em `source_system` ou estava `inactive`.
- Ou `source_system.api_key_hash` estava vazio (NULL) — então a validação falha sempre.
- Ou você usou uma API key diferente daquela cujo hash foi salvo no banco.

**Correção (fluxo “certo”)**
1) Confirmar o source:
   ```powershell
   docker compose exec db psql -U appuser -d appdb -c "SELECT id, name, status, api_key_hash FROM source_system ORDER BY id;"
   ```

2) Gerar key + hash **usando a própria função do projeto** (evita divergência):
   ```powershell
   docker compose exec api python -c "from app.core.security import generate_api_key, hash_api_key; k=generate_api_key('src'); print('API_KEY='+k); print('HASH='+hash_api_key(k))"
   ```

3) Salvar o HASH no banco:
   ```powershell
   docker compose exec db psql -U appuser -d appdb -c "UPDATE source_system SET api_key_hash = '<HASH>' WHERE name = 'partner_a';"
   ```

4) Usar a API_KEY no header:
   ```powershell
   $headers_ok = @{ "X-API-Key" = "<API_KEY>" }
   ```

---

## 10) `curl` no PowerShell (quebra com -H / -d)

**Sintoma**
- `-H` / `-d` não reconhecidos, e o comando quebra.

**Causa**
- No Windows PowerShell, `curl` é alias de `Invoke-WebRequest`.

**Correção**
- Usar `Invoke-RestMethod` (recomendado), ou `curl.exe` (o binário real).

---

## Checklist final de validação (Fase 4)

### 1) Health
```powershell
Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/health"
```

### 2) NEGATIVO — sem API key
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/ingest" -ContentType "application/json" -Body $body_ok
# Esperado: 401 + detail "missing X-API-Key"
```

### 3) NEGATIVO — API key inválida
```powershell
$headers_bad = @{ "X-API-Key" = "INVALIDA" }
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/ingest" -Headers $headers_bad -ContentType "application/json" -Body $body_ok
# Esperado: 401 + detail "invalid api key"
```

### 4) POSITIVO — API key correta
```powershell
$headers_ok = @{ "X-API-Key" = "<API_KEY_VALIDA>" }
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/ingest" -Headers $headers_ok -ContentType "application/json" -Body $body_ok
# Esperado: ACCEPTED / DUPLICATE / REJECTED (fluxo normal)
```

### 5) Confirmar que o `security_event` grava no negativo
```powershell
docker compose exec db psql -U appuser -d appdb -P pager=off -c "
SELECT id, event_type, severity, source_id, user_id, ip, user_agent, request_id, details, created_at
FROM security_event
ORDER BY id DESC
LIMIT 10;"
```

---

## Nota de entrega

Esse arquivo deve ficar no repo em `docs/99_troubleshooting_fase4.md`.
Ele mostra que você:
- implementou API key corretamente (hash + verify)
- registrou eventos de segurança sem quebrar o fluxo (não dá 500)
- dominou diferenças de PowerShell vs Linux/psql
- sabe diagnosticar erros de ORM/migrations (FK/tabelas/models)
