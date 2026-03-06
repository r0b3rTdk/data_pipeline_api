# FASE 11 — Security Hardening Avançado

## Objetivo
Fortalecer a segurança da API com proteções reais usadas em produção:

- Rate limiting (SlowAPI)
- Proteção contra brute force (bloqueio por IP após falhas)
- Refresh token JWT (+ endpoint de refresh)
- Security headers avançados
- Logs de autenticação (eventos estruturados)
- Testes cobrindo os fluxos

> Resultado: a API fica muito mais próxima de um cenário “produção real”.

---

## Visão geral do que mudou

### Arquivos novos (Fase 11)
- `app/core/rate_limit.py`  
  Cria o `limiter` do SlowAPI e define a chave do cliente (IP).
- `app/core/login_attempts.py`  
  Controle simples (em memória) de tentativas de login falhas por IP.

### Arquivos alterados
- `app/main.py`  
  Integra SlowAPI middleware + handler de RateLimitExceeded.
- `app/api/routes/auth.py`  
  Aplica rate limit, adiciona brute force, refresh token, logs.
- `app/middleware/security_headers.py`  
  Security headers avançados (HSTS/CSP/XSS).
- `app/core/security.py`  
  Geração de access/refresh token com claim `typ`.
- `app/core/settings.py`  
  Novas configs: `LOGIN_RATE_LIMIT`, `JWT_REFRESH_DAYS`, etc.
- `tests/conftest.py`  
  Ajustes para evitar conflitos com DB persistente + reset do brute force.
- `tests/test_auth.py`  
  Testes para refresh, brute force e rate limit.

---

## PARTE 1 — Rate limiting (SlowAPI)

### Por que isso existe?
Evita abuso e reduz risco de:
- brute force rápido
- flood no login
- DOS leve por endpoint

### Dependência
Adicionar ao `requirements.txt`:
- `slowapi==0.1.9`

### Implementação
**Arquivo:** `app/core/rate_limit.py`

- Define `client_key` com prioridade para header `X-Client-IP` (ótimo em testes e atrás de proxy)
- Define `limiter = Limiter(key_func=client_key)`

### Integração no FastAPI
**Arquivo:** `app/main.py`

- `app.state.limiter = limiter`
- `app.add_middleware(SlowAPIMiddleware)`
- `app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)`

### Aplicação no endpoint
**Arquivo:** `app/api/routes/auth.py`

- Decorator no login:
  - `@limiter.limit(...)`

> Observação importante: o rate limit é *por IP (key_func)*.

---

## PARTE 2 — Proteção contra brute force (in-memory)

### Por que isso existe?
Mesmo com rate limit, ataques “lentos” ou distribuídos podem tentar senha repetidamente.
Aqui a API mantém estado por IP e bloqueia após N falhas.

### Implementação
**Arquivo:** `app/core/login_attempts.py`

- `register_failure(ip)` incrementa contagem e aplica bloqueio após `MAX_ATTEMPTS`
- `is_blocked(ip)` retorna True se o IP está bloqueado (até `blocked_until`)
- `reset(ip)` limpa estado em caso de sucesso
- `reset_all()` útil para testes

### Integração no login
**Arquivo:** `app/api/routes/auth.py`

Fluxo:
1. `if is_blocked(ip):` → `HTTP 429` (`too_many_login_attempts`)
2. valida user/senha
3. falhou → `register_failure(ip)` e `401 invalid_credentials`
4. sucesso → `reset(ip)`

> Em produção com múltiplas instâncias, o ideal é Redis. Aqui in-memory é perfeito para fase de projeto/CI.

---

## PARTE 3 — Refresh Token JWT

### Por que isso existe?
- Access token curto reduz impacto caso vaze.
- Refresh token longo mantém sessão sem pedir senha toda hora.

### O que mudou no contrato?
Login agora retorna:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

### Implementação
**Arquivo:** `app/core/security.py`

- `create_access_token(..., typ="access")`
- `create_refresh_token(..., typ="refresh")`
- `decode_token(token)` para validar/ler claims

### Endpoint novo
**Arquivo:** `app/api/routes/auth.py`

`POST /api/v1/auth/refresh`

- recebe `{ "refresh_token": "..." }`
- valida token + `typ == "refresh"`
- retorna um novo `access_token`

---

## PARTE 4 — Security Headers avançados

### Por que isso existe?
Ajuda a reduzir vetores comuns:
- clickjacking
- mime sniffing
- políticas de navegação permissivas
- CSP para reduzir superfície XSS (com cuidado em `/docs`)

### Implementação
**Arquivo:** `app/middleware/security_headers.py`

- mantém headers básicos já existentes
- adiciona:
  - `X-XSS-Protection`
  - `Strict-Transport-Security` (somente quando scheme == https)
  - `Content-Security-Policy`
    - mais permissivo para `/docs`, `/redoc`, `/openapi.json`
    - mais restritivo para o resto

---

## PARTE 5 — Logs de autenticação (estruturados)

### Por que isso existe?
- auditoria
- investigação de incidentes
- entender tentativa de ataques (IP/User-Agent/rota)

### Eventos logados
**Arquivo:** `app/api/routes/auth.py`

- `login_success`
- `login_failed`
- `login_blocked`
- `token_refresh`
- (opcional) `token_refresh_failed`

Campos úteis no `extra`:
- `client_ip`
- `user_agent`
- `user_id` (quando disponível)
- `role`
- `path`
- `method`

---

## PARTE 6 — Testes

### Cobertura adicionada
**Arquivo:** `tests/test_auth.py`

- Login retorna access + refresh
- Brute force bloqueia após 5 falhas
- Refresh gera novo access token
- Rate limit no login retorna 429

### Observações importantes de testes
- Se o `LOGIN_RATE_LIMIT` estiver alto (ex.: `1000/minute`), o teste de rate limit precisa forçar `5/minute` (ex.: alterando settings no teste).
- Como o DB usa volume persistente no Docker, dados podem permanecer entre execuções — fixtures precisam de nomes únicos.

### Comando para rodar testes no Docker
```bash
docker compose exec -e PYTHONPATH=/app api pytest -q
```

---

## Resultado da Fase 11
Agora sua API tem:

- ✔ Rate limit real (SlowAPI)
- ✔ Proteção brute force (bloqueio por IP)
- ✔ Refresh token + endpoint `/auth/refresh`
- ✔ Security headers reforçados
- ✔ Logs estruturados de autenticação
- ✔ Testes cobrindo os fluxos

---

## Próxima fase (FINAL)
**FASE 12 — Deploy + Finalização**
- Deploy real (Fly.io / Render / Railway / VPS)
- HTTPS + domínio
- Variáveis seguras (secrets)
- README final (arquitetura, diagramas, exemplos de endpoints)
