# Changelog — Projeto01 (Data Pipeline API)

Este changelog registra as entregas por fase do projeto.

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
