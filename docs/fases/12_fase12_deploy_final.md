# Fase 12 — Deploy Final (Render) e Validação em Produção

## Objetivo da fase

Publicar o projeto em ambiente real com acesso público via HTTPS, banco de dados online,
frontend integrado ao backend e validação completa do fluxo de ingestão e consulta.

---

## Escopo da fase

Nesta fase o projeto passou do ambiente local para produção:

- Backend publicado como Web Service no Render
- PostgreSQL provisionado no Render
- Frontend publicado como Static Site
- Configuração de variáveis de ambiente
- Execução de migrations
- Execução do seed inicial
- Validação completa do fluxo frontend → backend → banco

---

## Arquitetura final

```
Frontend (Render Static Site)
        ↓
Backend API (FastAPI - Render Web Service)
        ↓
PostgreSQL (Render Managed Database)
```

---

## URLs públicas

API  
https://data-pipeline-api-p01y.onrender.com

Frontend  
https://data-pipeline-frontend.onrender.com

Healthcheck  
https://data-pipeline-api-p01y.onrender.com/api/v1/health

---

## Deploy do Backend

O backend foi publicado como Web Service no Render.

Stack utilizada:

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Uvicorn

Comando de inicialização:

```
alembic upgrade head && python -m app.scripts.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

---

## Banco de dados

Banco PostgreSQL provisionado no Render.

Características:

- Banco gerenciado
- Conexão segura
- DATABASE_URL fornecida automaticamente
- Migrations executadas via Alembic

---

## Variáveis de ambiente

Principais variáveis configuradas:

```
APP_ENV=production

JWT_SECRET=<secret>
JWT_ALG=HS256
JWT_EXPIRES_MIN=60
JWT_REFRESH_DAYS=7

LOGIN_MAX_ATTEMPTS=5
LOGIN_BLOCK_MINUTES=15
LOGIN_RATE_LIMIT=5/minute

CORS_ORIGINS=https://data-pipeline-frontend.onrender.com
```

---

## Deploy do Frontend

O frontend foi publicado como Static Site no Render.

Configuração utilizada:

Root Directory

```
frontend
```

Build Command

```
(vazio)
```

Publish Directory

```
.
```

---

## Integração Frontend ↔ Backend

O frontend consome diretamente a API pública.

config.js:

```
API_BASE_URL = "https://data-pipeline-api-p01y.onrender.com"
```

As requisições utilizam:

```
Authorization: Bearer <token>
```

---

## Funcionalidades validadas

- Login JWT
- RBAC
- Ingest de eventos
- Validação de regras de negócio
- Persistência em trusted e rejections
- Consulta administrativa
- Logs de segurança
- Auditoria

---

## Segurança validada

Foram testados:

- JWT Authentication
- RBAC
- Rate limit
- Proteção contra brute force
- API Key no endpoint de ingest
- Security headers
- Auditoria

---


## Resultado final

Após a Fase 12 o sistema passou a operar completamente em produção com:

- Backend FastAPI
- PostgreSQL gerenciado
- Frontend administrativo
- Segurança com JWT e RBAC
- Pipeline completo de ingestão e validação
- Interface administrativa funcional

---
