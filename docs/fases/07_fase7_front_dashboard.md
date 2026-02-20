# Fase 7 — Front (Dashboard Admin)

## Objetivo
Entregar um front-end simples (HTML/CSS/JS puro) para consumir a API e visualizar o pipeline:
- Metrics/KPIs
- Trusted Events (lista + detalhe)
- Rejections (lista + detalhe)
- Security Events (lista + filtros)
- Audit Logs (lista + filtros)
- Login/Logout (JWT)

---

## Como rodar (DEV)

### 1) Subir API + DB
Na raiz do projeto:
```bash
docker compose up -d
```

A API deve estar em:
- http://localhost:8000/docs

### 2) Subir o front (arquivos estáticos)
Na raiz do projeto:
```bash
cd frontend
python -m http.server 3000
```

Abrir no navegador:
- http://localhost:3000

---

## Configuração do Front
Arquivo:
- `frontend/config.js`

Base URL padrão:
- `http://localhost:8000`

Se sua API estiver em outra porta/host, altere:
```js
window.__APP_CONFIG__ = { API_BASE_URL: "http://localhost:8000" }
```

---

## Login / Autorização
- Tela de login chama: `POST /api/v1/auth/login`
- O `access_token` é salvo em `localStorage` (key: `p01_access_token`)
- As rotas internas usam `Authorization: Bearer <token>`
- Se der `401`, o token é apagado e a UI volta para o login

---

## Rotas/Telas (Front)
- `#/dashboard` → Cards com `GET /api/v1/metrics`
- `#/trusted` → Tabela paginada + detalhes
- `#/rejections` → Tabela paginada + detalhes
- `#/security-events` → Tabela paginada + filtros (severity/event_type)
- `#/audit` → Tabela paginada + filtros (action/entity_type/user_id)
- `Logout` → apaga token e volta ao login

---

## Paginação e Filtros
O front usa querystring no hash, por exemplo:
- `#/trusted?page=1&page_size=10`
- `#/security-events?page=1&page_size=10&severity=HIGH&event_type=AUTH_FAILED`
- `#/audit?page=1&page_size=10&action=UPDATE`

---

## Observações
- UI propositalmente mínima (admin simples), focada em “consumível por UI”.
- Sem framework, sem build: roda local com `http.server`.
