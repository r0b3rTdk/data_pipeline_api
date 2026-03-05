# Troubleshooting — Fase 9 (Observabilidade)

Este guia cobre os problemas mais comuns ao validar a Fase 9 localmente (Docker)
e em ambiente de deploy.

---

## 1) No navegador aparece `ERR_EMPTY_RESPONSE` / “Nenhum dado foi enviado”

### Sintoma
- Browser mostra: **ERR_EMPTY_RESPONSE**
- Ou a página “não está funcionando”
- Mas `docker compose ps` mostra containers rodando

### Causa mais comum
Você acessou `http://localhost/...` (porta 80), mas sua API está em **porta 8000**.

### Como confirmar
No terminal:

```powershell
docker compose ps
```

Procure algo como:

- `0.0.0.0:8000->8000/tcp` (API exposta na 8000)

### Como corrigir
Acesse com porta explícita:

- `http://localhost:8000/docs`
- `http://localhost:8000/api/v1/ready`
- `http://127.0.0.1:8000/api/v1/ready`

---

## 2) PowerShell: `curl` pede `Uri` / erro “Não é possível localizar a unidade http”

### Sintoma
Ao rodar:

```powershell
curl -i http://localhost:8000/api/v1/ready
```

o PowerShell trata `curl` como `Invoke-WebRequest` e pode dar erro.

### Como corrigir
Use o curl real do Windows:

```powershell
curl.exe -i "http://localhost:8000/api/v1/ready"
```

Ou PowerShell puro:

```powershell
iwr -Uri "http://localhost:8000/api/v1/ready" -Method GET
```

---

## 3) `/api/v1/ready` retorna **503** (db fail)

### Sintoma
- `GET /api/v1/ready` retorna **503**
- Body: `"checks": {"db": "fail"}`

### Causas comuns
- Postgres não subiu (container db down)
- `DATABASE_URL` está errado
- Migrações não foram aplicadas (menos comum para `SELECT 1`, mas pode ocorrer em setups específicos)
- Problema de rede entre containers

### Como investigar
1) Verificar containers:

```powershell
docker compose ps
```

2) Ver logs do banco:

```powershell
docker compose logs -f db
```

3) Ver logs da API:

```powershell
docker compose logs -f api
```

4) Confirmar variáveis/config (se aplicável no seu projeto):
- `DATABASE_URL`

### Como corrigir
- Subir ambiente novamente:

```powershell
docker compose up -d --build
```

- Se o DB não subir, verificar credenciais e porta no compose/env.

---

## 4) `/api/v1/metrics` retorna **401 Unauthorized**

### Sintoma
- `GET /api/v1/metrics` retorna **401**
- Body com `"detail": "not_authenticated"` ou semelhante

### Causa
O endpoint é protegido por RBAC. Você chamou sem JWT.

### Como corrigir (fluxo correto)
1) Fazer login:

```powershell
curl.exe -s -X POST "http://localhost:8000/api/v1/auth/login" `
  -H "Content-Type: application/json" `
  -d '{ "username": "admin", "password": "Admin@123" }'
```

2) Guardar o `access_token` em uma variável:

```powershell
$token = "<COLE_O_ACCESS_TOKEN>"
```

3) Chamar `/metrics` com Bearer:

```powershell
curl.exe -i "http://localhost:8000/api/v1/metrics" -H "Authorization: Bearer $token"
```

---

## 5) `/api/v1/metrics` retorna **401 invalid_token**

### Sintoma
- Body: `"detail":"invalid_token"`

### Causas comuns
- Token expirou
- Você não atualizou a variável `$token` com o **token novo**
- Você colou `token_type` junto, ou colocou `Bearer` duplicado

### Como corrigir
- Copie **somente** o `access_token` e refaça:

```powershell
$token = "<ACCESS_TOKEN>"
curl.exe -i "http://localhost:8000/api/v1/metrics" -H "Authorization: Bearer $token"
```

### Dica
Para conferir se a variável está preenchida:

```powershell
$token.Length
```

---

## 6) `/api/v1/metrics` retorna **403 forbidden**

### Sintoma
- HTTP 403
- Body: `"detail": "forbidden"`

### Causa
O usuário autenticado existe, mas **o role não está permitido** pelo `require_roles([...])` desse endpoint.

### Como investigar
- Veja o role do usuário (no banco ou no token)
- Confira quais roles o endpoint aceita (no arquivo da rota)

### Como corrigir
- Logar com um usuário de role permitido
- Ajustar a lista de roles permitidos (se fizer sentido no projeto)

---

## 7) Contadores `http` “zeram” após restart

### Sintoma
- `requests_total` volta para 0 após reiniciar container

### Explicação
As métricas operacionais são **in-memory** (em memória do processo).
Isso é intencional na Fase 9 (simples e eficaz).

### Opções (se quiser evoluir)
- Exportar métricas para Prometheus
- Persistir em DB (não recomendado para métrica de request)
- Mandar para serviço externo (Datadog, Grafana Cloud etc.)

---

## 8) `http_routes` só mostra algumas rotas

### Sintoma
- Você esperava ver várias rotas, mas aparece só 1 ou 2

### Causas comuns
- Você só chamou poucas rotas desde que o processo subiu
- O contador por rota é **in-memory**, então depende do tráfego gerado

### Como corrigir
Chame mais endpoints e verifique novamente:

```powershell
curl.exe -i "http://localhost:8000/api/v1/ready"
curl.exe -i "http://localhost:8000/api/v1/health"
curl.exe -i "http://localhost:8000/api/v1/metrics" -H "Authorization: Bearer $token"
```

---

## 9) Onde ver logs estruturados

### Local (Docker)
```powershell
docker compose logs -f api
```

Você deve ver uma linha JSON por request contendo `request_id`, `status_code`,
`process_time_ms` e, quando autenticado, `user_id` e `role`.

---

## 10) Swagger /docs não abre

### Causas comuns
- Porta errada (ver tópico 1)
- API não está rodando

### Como corrigir
- Confirme `docker compose ps`
- Acesse:

- `http://localhost:8000/docs`

---

## 11) Deploy: health check correto

Ao subir em Render/Fly/VPS, use:

- **Readiness**: `GET /api/v1/ready`

Porque ele valida DB e evita mandar tráfego para instâncias “meio quebradas”.

---

## 12) Checklist final de validação

- `GET /api/v1/health` retorna 200
- `GET /api/v1/ready` retorna 200 (DB ok)
- `GET /api/v1/metrics` retorna 200 com token válido
- `/metrics` inclui:
  - `"http"`
  - `"http_routes"`
- Logs JSON aparecem em `docker compose logs -f api`
- `pytest` passa:

```powershell
docker compose exec -e PYTHONPATH=/app api pytest -q
```
