# Fase 12 — Troubleshooting do Deploy Final

Este arquivo registra **enroscos reais** que aconteceram durante a **Fase 12** e como foram resolvidos.

---

## 1) Erro no PowerShell com variável de porta

### Problema
Ao executar o comando:

uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

o PowerShell retornava erro.

### Causa
A sintaxe `${PORT:-8000}` é própria de shell Unix e não funciona no PowerShell.

### Solução

Executar localmente com:

uvicorn app.main:app --host 0.0.0.0 --port 8000

---

## 2) DATABASE_URL ausente em testes locais

### Problema
Erro do SQLAlchemy indicando URL de banco inválida.

### Causa
A variável de ambiente `DATABASE_URL` não estava definida no ambiente local.

### Solução
Configurar a variável no `.env` ou no ambiente antes de rodar a aplicação.

---

## 3) Falhas no CI com flake8

### Problema
O pipeline do GitHub Actions falhou com erros de estilo como:

- indentação incorreta
- linhas muito longas

### Solução
Ajustar indentação e quebrar linhas longas conforme padrão configurado no flake8.

---

## 4) Conflito entre brute force e rate limit

### Problema
Teste de brute force falhava porque o rate limit bloqueava a rota antes.

### Solução
No workflow do CI foi configurado:

LOGIN_RATE_LIMIT=1000/minute

para permitir que o teste de brute force execute corretamente.

---

## 5) Erro no deploy do Render (status 127)

### Problema
O container iniciava mas encerrava com:

Exited with status 127

### Causa
Configuração incorreta do comando de inicialização.

### Solução
Mover o start da aplicação para o Dockerfile:

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

---

## 6) Driver de banco incorreto

### Problema
Erro:

ModuleNotFoundError: No module named 'psycopg2'

### Causa
A string de conexão estava usando:

postgresql://

o que faz o SQLAlchemy procurar `psycopg2`.

### Solução
Alterar para:

postgresql+psycopg://

---

## 7) Usuário seed não existia no banco

### Problema
Login com admin falhava após o deploy.

### Causa
O seed não estava sendo executado no banco novo.

### Solução
Adicionar o seed no comando de inicialização:

alembic upgrade head && python -m app.scripts.seed && uvicorn ...

---

## 8) Swagger carregando em branco

### Problema
Página `/docs` aparecia vazia.

### Causa
Content Security Policy muito restritiva.

### Solução
Ajustar a CSP para permitir assets necessários do Swagger.

---

## 9) Ingest falhando por JSON inválido

### Problema
Swagger retornava erro de JSON decode.

### Causa
Body estava vazio ou mal formatado.

### Solução
Enviar JSON válido ou testar via PowerShell/curl.

---

## 10) Ingest retornando missing_x_api_key

### Problema
Endpoint exigia header `X-API-Key`.

### Solução
Enviar header correto:

X-API-Key: partner_a_key_change_me

---

## 11) Rotas protegidas retornando missing_bearer_token

### Problema
Trusted e Rejections retornavam erro 401.

### Causa
Header Authorization não estava sendo enviado.

### Solução
Enviar:

Authorization: Bearer <access_token>

---

## 12) Frontend falhando com Failed to fetch

### Problema
Frontend não conseguia chamar a API.

### Causa
CORS não permitia o domínio do frontend.

### Solução
Configurar:

CORS_ORIGINS=https://data-pipeline-frontend.onrender.com

---

## 13) Frontend retornando Not Found

### Problema
Static site do Render não encontrava arquivos.

### Solução
Configuração correta:

Root Directory: frontend  
Build Command: vazio  
Publish Directory: .

---

## 14) Trusted com total incorreto

### Problema
API retornava total 1 mas items vazio.

### Causa
Uso incorreto de count com query paginada.

### Solução
Substituir por:

total = q.order_by(None).count()

---

## 15) Import não utilizado no CI

### Problema
flake8 acusou:

F401 sqlalchemy.func imported but unused

### Solução
Remover import após alteração da query.

---

## 16) Zoom automático no celular

### Problema
Inputs causavam zoom automático no iOS.

### Solução
Garantir:

input,
select,
textarea,
button {
  font-size: 16px;
}

---

## 17) Responsividade quebrada em Trusted e Rejections

### Problema
A página inteira ganhava scroll horizontal no mobile.

### Causa
Tabela larga dentro de item de CSS Grid sem permitir shrink.

### Solução
Aplicar:

.app { min-width: 0; }  
.card { min-width: 0; }  
.grid { grid-template-columns: minmax(0, 1fr); }  
.grid > * { min-width: 0; }

e ajustar `.table-wrap` para limitar o overflow da tabela.

---

# Conclusão

Todos os problemas encontrados durante o deploy foram identificados e corrigidos.

O sistema passou a funcionar corretamente em produção com:

- Backend (FastAPI)
- PostgreSQL
- Frontend (Render Static Site)
- JWT + RBAC
- Pipeline completo de ingestão e validação.