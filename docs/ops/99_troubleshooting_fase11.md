# 99 — Troubleshooting (Fase 11 : Security Hardening)

Este arquivo registra os principais erros que apareceram durante a Fase 11
e como resolvemos cada um, com causa raiz e solução.

---

## 1) `docker compose up -d --build` → 502 Bad Gateway (DockerDesktopLinuxEngine)

**Sintoma (resumo):**
- `request returned 502 Bad Gateway ... dockerDesktopLinuxEngine ... check if the server supports the requested API version`

**Causa raiz:**
- Problema de comunicação entre o Docker CLI/Compose e o Docker Engine (Docker Desktop/WSL).
- Normalmente engine travado, backend WSL reiniciando, ou contexto bugado.

**Solução aplicada:**
1. Reiniciar Docker Desktop (garantir “Engine running”)
2. (Se necessário) `docker context use default`
3. (Se necessário) `wsl --shutdown` e reabrir Docker Desktop

---

## 2) `docker compose exec ... api pytest -q` → `service "api" is not running`

**Sintoma:**
- Compose subiu apenas `db` (Postgres), mas `api` não estava rodando.

**Causa raiz:**
- O serviço `api` não tinha subido (ou estava crashando), então não existia container ativo para `exec`.

**Como investigar:**
- `docker compose ps`
- `docker compose logs -n 200 api`

**Solução:**
- Subir explicitamente:
  - `docker compose up -d --build api`
- Ver logs e corrigir o erro se estivesse “Exited”.

---

## 3) Teste `test_bruteforce_blocks_after_5_failures` falhando com `KeyError: 'detail'`

**Sintoma:**
- O teste esperava:
  - `429` + JSON com `{"detail": "too_many_login_attempts"}`
- Mas recebeu `429` de rate limit do SlowAPI e o payload não tinha `detail`.

**Causa raiz:**
- O brute force fazia 6 requisições no login com o mesmo IP.
- Com `LOGIN_RATE_LIMIT=5/minute`, a 6ª request cai primeiro no SlowAPI (rate limit) e não no bloqueio de brute force.
- SlowAPI usa handler próprio e a resposta não é o `HTTPException` da API.

**Solução aplicada:**
- Para testes, elevamos `LOGIN_RATE_LIMIT` (ex.: `1000/minute`) para não interferir no brute force.
- Alternativamente, dá para:
  - isolar IPs nos testes
  - ou forçar `LOGIN_RATE_LIMIT` apenas no teste de rate limit.

---

## 4) `tests/test_audit.py` erro: `UniqueViolation` em `uq_source_system_name` (ci-source)

**Sintoma:**
- `duplicate key value violates unique constraint "uq_source_system_name"`
- `Key (name)=(ci-source) already exists`

**Causa raiz:**
- O Postgres no Docker usa volume persistente (`pgdata`).
- Isso mantém dados entre execuções.
- O fixture criava sempre `SourceSystem(name="ci-source")`.

**Solução aplicada (mais robusta):**
- Tornar o `name` único por teste usando UUID:
  - `name=f"ci-source-{uuid4().hex}"`
- Também tornamos `external_id` únicos quando necessário.

**Alternativa (mais “agressiva”):**
- Derrubar stack e apagar volume:
  - `docker compose down -v`
- (Mas isso apaga os dados do banco.)

---

## 5) `test_rate_limit_login_429` falhando depois de aumentar `LOGIN_RATE_LIMIT`

**Sintoma:**
- O teste esperava `429` na 6ª request (limite 5/min).
- Mas recebia `200` porque `LOGIN_RATE_LIMIT=1000/minute` no ambiente de teste.

**Causa raiz:**
- Para não conflitar com brute force, elevamos o rate limit nos testes.
- Isso deixa o teste de rate limit sem “gatilho”.

**Solução recomendada:**
- Forçar o limite apenas dentro do teste de rate limit:
  - setar `settings.LOGIN_RATE_LIMIT = "5/minute"` no teste
  - e garantir que o decorator use leitura dinâmica do settings.

---

## 6) docker-compose.yml com `environment` misturado (lista + mapa)

**Sintoma:**
- Compose pode interpretar errado quando mistura:
  - `- VAR=...` (lista)
  - `VAR: ...` (mapa)

**Causa raiz:**
- YAML inválido/ambíguo: `environment:` deve ser **ou** lista **ou** mapa.

**Solução:**
- Padronizar para mapa:
  - `ENV: "valor"`
- ou padronizar para lista:
  - `- ENV=valor`

---

## Comandos úteis

### Ver serviços e logs
```bash
docker compose ps
docker compose logs -n 200 api
```

### Rodar testes
```bash
docker compose exec -e PYTHONPATH=/app api pytest -q
```

### Limpar imagens não usadas
```bash
docker image prune -f
docker system prune -a -f
```

### Apagar dados do DB (cuidado)
```bash
docker compose down -v
```
