# Troubleshooting — Fase 7 (Front Dashboard)

## 1) Front abre, mas Login dá “Failed to fetch”
**Causa provável:** API fora do ar, base URL errada ou CORS.

### Checagens
- API está acessível?
  - http://localhost:8000/docs
- Base URL do front:
  - `frontend/config.js` → `API_BASE_URL`

### CORS (se aparecer no Console do navegador)
Se o Console (F12) mostrar erro de CORS, permita o origin do front no backend:
- `http://localhost:3000`

Reinicie o serviço `api` após ajustar CORS.

---

## 2) Login funciona via curl/PowerShell, mas falha no navegador
**Causa:** CORS bloqueando o browser.

### Solução
- Adicionar `http://localhost:3000` em `CORS_ORIGINS` (ou `allow_origins`) no backend
- Reiniciar API (`docker compose restart api`)

---

## 3) Após login, algumas telas voltam para Login
**Causa:** token inválido/expirado ou falta de permissão (RBAC).

### Como identificar
- Se a API retornar `401`, o front limpa token e redireciona para `#/login`.
- Se retornar `403`, normalmente é permissão insuficiente.

### Solução
- Relogar (token novo)
- Verificar role/claims do usuário e permissões das rotas

---

## 4) “Rota não encontrada” ao aplicar filtros/paginação
**Causa:** parser de rota lendo `?query` como parte do nome da rota.

### Solução
No `routeFromHash()` do `frontend/app.js`, garantir que o route ignore querystring:
```js
const m = h.match(/^#\/([^?]+)(\?.*)?$/);
```

---

## 5) Endpoint 404 (ex.: /api/v1/audit)
**Causa:** sua API pode ter path diferente.

### Solução
- Verificar no Swagger (`/docs`) o path exato
- Ajustar o path no arquivo da página correspondente:
  - `pages_audit.js`
  - `pages_security_events.js`
  - etc.

---

## 6) Tabela mostra itens, mas “Total” aparece errado
**Causa:** o backend pode retornar `total` inconsistente.

### Solução no front (resiliente)
Usar fallback:
```js
const totalFromApi = Number(data.total ?? data.total_items ?? data.total_count ?? data.count ?? NaN);
const total = Number.isFinite(totalFromApi) && totalFromApi >= items.length ? totalFromApi : items.length;
```

---

## 7) Token salvo, mas não está sendo enviado
**Checar:**
- `localStorage` contém `p01_access_token`
- `frontend/api.js` adiciona header:
  - `Authorization: Bearer <token>`

---

## 8) Como debugar rápido
- Console do navegador (F12) para:
  - CORS
  - Network (requests/response)
- Swagger (`/docs`) para conferir:
  - paths
  - query params
  - modelos de resposta
