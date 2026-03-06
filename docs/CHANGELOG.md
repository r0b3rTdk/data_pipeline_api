# Changelog — Projeto01 (Data Pipeline API)

Este changelog registra as entregas por fase do projeto.

---
## [Fase 11] — Security Hardening Avançado

### Adicionado
- Rate limiting real com **SlowAPI**:
  - integração via middleware (`SlowAPIMiddleware`) + handler de `RateLimitExceeded`
  - limite configurável via `LOGIN_RATE_LIMIT` (ex.: `5/minute` no `/auth/login`)
- Proteção contra brute force (in-memory) por IP no login:
  - bloqueio após N tentativas (`MAX_ATTEMPTS`) com janela de bloqueio (`BLOCK_MINUTES`)
  - reset automático do contador em login bem-sucedido
- Refresh token JWT:
  - login retorna `access_token` + `refresh_token`
  - endpoint `POST /api/v1/auth/refresh` para emitir novo access token
  - claim `typ` diferencia `access` vs `refresh`
- Logs estruturados de autenticação:
  - eventos: `login_success`, `login_failed`, `login_blocked`, `token_refresh`
  - campos: `client_ip`, `user_agent`, `user_id`, `role`, `path`, `method`
- Security headers avançados:
  - `Strict-Transport-Security` (apenas em HTTPS)
  - `Content-Security-Policy` (CSP)
  - `X-XSS-Protection`

### Alterado
- `security.py` estendido para gerar e validar access/refresh tokens (com `typ`).
- `auth` atualizado para aplicar rate limit + brute force + refresh token.
- Testes ajustados para isolar estado de segurança:
  - reset do brute force entre testes
  - fixtures com IDs/names únicos para evitar conflito em DB persistente (Docker volume)

### Testes
- Cobertura de:
  - rate limit no login (429)
  - brute force (bloqueio após falhas)
  - refresh token flow (login → refresh → novo access)
  - regressão de login sucesso/falha

### Documentação
- `docs/11_fase11_security_hardening.md`
- `docs/99_troubleshooting_fase11.md`

---
---

## [Fase 10] — CI/CD (GitHub Actions)
### Adicionado
- Pipeline de Integração Contínua com GitHub Actions em:
  - `.github/workflows/ci.yml`
- Execução automática do pipeline em:
  - `push` e `pull_request` para `main` e `develop`
- Etapas do CI:
  - instalação de dependências
  - lint com `flake8` (diretório `app/`)
  - provisionamento de PostgreSQL via service container
  - migrations com Alembic (`alembic upgrade head`)
  - testes com Pytest (`pytest -q`)

### Alterado
- Configuração do lint adicionada via `.flake8` para adequar regras do flake8 ao padrão do projeto e evitar falhas por regras puramente estéticas no CI.
- Testes ajustados para rodarem em ambiente limpo (CI), criando dados necessários via fixtures (sem depender de registros pré-existentes no banco).

### Documentação
- `docs/10_fase10_ci_cd.md`
- `docs/99_troubleshooting_fase10.md`

---

## [Fase 9] — Observabilidade
### Adicionado
- Endpoint de readiness:
  - `GET /api/v1/ready` com verificação de banco (`SELECT 1`) e retorno `503` quando DB falha.
- Métricas operacionais em `GET /api/v1/metrics` (bloco `http`):
  - `uptime_seconds`, `requests_total`, `errors_4xx_total`, `errors_5xx_total`.
- Latência por rota em `GET /api/v1/metrics` (bloco `http_routes`):
  - contagem e média de latência por rota no formato `"METHOD /path": {count, avg_ms}`.
- Logs estruturados (JSON) enriquecidos por request:
  - `client_ip`, `user_agent`, `user_id`, `role` (quando autenticado), além de `request_id` e `process_time_ms`.
- Testes da fase (Pytest):
  - validação de `/ready` (200/503), propagação de headers `X-Request-Id` e `X-Process-Time-Ms`,
  - validação de `/metrics` incluindo `http` e `http_routes`.

### Alterado
- Middleware de request_id ajustado para registrar métricas HTTP e por rota a cada request (contadores in-memory).

### Observações
- Métricas operacionais (`http` e `http_routes`) são **in-memory** e reiniciam junto com o processo/container.
- Documentação da fase:
  - `docs/09_fase9_observabilidade.md`
  - `docs/99_troubleshooting_fase9.md`

## [Fase 8] Deploy / Produção (Docker + Nginx) — Produção-Lite

### Adicionado
- `docker-compose.prod.yml` para execução em ambiente de produção-lite.
- Serviço `nginx` como reverse proxy para a API (`/api/ -> api:8000`).
- Configuração de Nginx em `deploy/nginx/default.conf`.
- Healthchecks para serviços `db` e `api`.
- `restart: unless-stopped` nos serviços principais.
- `.env.prod.example` como modelo de variáveis para produção.
- Scripts e estrutura de deploy preparados para evolução da fase (incluindo base para HTTPS).
- Documentação de deploy da fase:
  - `docs/08_fase8_deploy_producao.md`
  - `docs/99_troubleshooting_fase8.md`

### Alterado
- Fluxo de execução separado entre ambiente local (`docker-compose.yml`) e produção-lite (`docker-compose.prod.yml`).
- Nginx configurado para operar inicialmente em HTTP (porta 80), com bloco HTTPS preparado para ativação futura.
- Ajustes de processo no servidor para leitura de variáveis pelo Compose via `.env` local (copiado de `.env.prod`) para evitar warning de interpolação.

### Validado em servidor Linux (produção-lite)
- Subida de ambiente com `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build`.
- API e banco PostgreSQL saudáveis (`healthy`) via healthcheck.
- Nginx operacional como reverse proxy.
- `GET /api/v1/health` via Nginx retornando `200 OK`.
- Execução de migrations (`alembic upgrade head`) em ambiente de produção-lite.
- Execução de seed (`python -m app.scripts.seed`) com criação de:
  - usuário admin
  - source system `partner_a`
- `POST /api/v1/auth/login` funcionando via Nginx (JWT).
- `POST /api/v1/ingest` funcionando via Nginx com `X-API-Key`.
- Persistência do banco validada após restart (IDs incrementando em novo ingest).
- Reinício dos serviços validado (`docker compose restart`) com recuperação normal após janela de inicialização.

### Observações
- HTTPS com Certbot/Let's Encrypt **não foi ativado nesta fase** por ausência de domínio público apontado para o servidor.
- Estrutura de Nginx/TLS ficou preparada para ativação futura quando houver domínio.

---

## [Fase 7] — Front Admin (Visualização) — 2026-02-19
### Adicionado
- Front-end simples em `frontend/` (HTML/CSS/JS puro) para consumo da API e visualização do pipeline.
- Login via JWT consumindo `POST /api/v1/auth/login` com armazenamento do token no `localStorage` (`p01_access_token`).
- Guard de autorização no front:
  - envio automático de `Authorization: Bearer <token>` nas requisições
  - ao receber `401`, limpar token e redirecionar para `#/login`
- Dashboard com KPIs (cards) consumindo `GET /api/v1/metrics`.
- Telas com tabelas paginadas + detalhe (modal JSON):
  - Trusted Events (`#/trusted`)
  - Rejections (`#/rejections`)
- Tela Security Events (`#/security-events`) com:
  - paginação
  - filtros mínimos (`severity`, `event_type`)
  - persistência de filtros na URL (hash querystring)
- Tela Audit Logs (`#/audit`) com:
  - paginação
  - filtros simples (`action`, `entity_type`, `user_id`)
  - persistência de filtros na URL (hash querystring)
- Documentação da fase:
  - `docs/07_fase7_front_dashboard.md`
  - `docs/99_troubleshooting_fase7.md`

### Ajustado
- Parser de rotas do front para ignorar querystring em `#/route?query=...`.
- Cálculo resiliente de `total/total_pages` nas telas (fallback quando o backend não retorna total consistente).

---

## [Fase 6] — Produção/Hardening leve — 2026-02-12
### Adicionado
- Logs estruturados em JSON.
- Headers de segurança básicos.
- Seed/Bootstrap idempotente (admin + source_system default).
- Ajustes de robustez e testes em container.

---

## [Fase 5] — Autenticação JWT + RBAC — 2026-02-05
### Adicionado
- Login JWT para usuários internos.
- RBAC (roles) e proteção de rotas internas.
- Melhorias de observabilidade (request_id, tempo de processamento) e testes.

---

## [Fases 1–4] — Pipeline (RAW → TRUSTED → REJEIÇÕES) — 2026-01-29
### Adicionado
- Ingestão RAW com idempotência/deduplicação.
- Validação e roteamento para TRUSTED ou REJEIÇÕES.
- Endpoints de listagem/paginação para trusted e rejections.
- Persistência com PostgreSQL + migrations Alembic.
