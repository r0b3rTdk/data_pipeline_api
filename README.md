# Projeto01 — Data Pipeline API (RAW → TRUSTED → REJEIÇÕES)

API e front-end mínimos (e funcionais) para **ingestão**, **validação**, **idempotência/deduplicação**, **persistência relacional**, **registro de rejeições** e **consulta** — com camadas de **segurança** e **observabilidade** pensadas para uso real.

---

## Visão geral

### Fluxo (RAW → TRUSTED / REJECTION)

1. **Ingestão** recebe eventos via endpoint protegido por **API Key por fonte**.
2. Cada item é validado e normalizado.
3. Itens válidos seguem para **TRUSTED** (banco relacional).
4. Itens inválidos ou inconsistentes geram um registro em **REJEIÇÕES** com motivo e payload original.
5. Endpoints de consulta permitem inspecionar TRUSTED/REJEIÇÕES.

### O que este projeto entrega

- **Ingestão** com validação e **idempotência/deduplicação**
- **Persistência** (PostgreSQL) + **migrations** (Alembic)
- **Rejeições** com rastreabilidade (motivo + payload)
- **Segurança**
  - API Key por fonte (hash no banco)
  - Login **JWT**
  - **RBAC** (perfis/permissões por rota)
  - **Auditoria** + **security events**
- **Observabilidade**
  - `X-Request-Id` (propagado)
  - `X-Process-Time-Ms`
  - endpoint `/metrics` simples
  - health e readiness (inclui check de DB)
- **Front (Fase 7)** com login e telas de consulta

### Stack

- **FastAPI** + Uvicorn
- **PostgreSQL**
- **SQLAlchemy**
- **Alembic**
- Docker + Docker Compose
- Nginx (modo produção-lite)

---

## Como rodar (Docker)

> **URLs locais (Docker):** por padrão, a API sobe em `http://localhost:8000`.
> Se você estiver usando um container **nginx** na frente (opcional), o acesso pode ser via `http://localhost` (porta 80).



> Pré-requisitos: Docker e Docker Compose.

### 1) Subir os serviços

```bash
docker compose up -d --build
```

### 2) Health

```bash
curl -i http://localhost:8000/api/v1/health
```

### 3) Readiness (com checks)

```bash
curl -i http://localhost:8000/api/v1/ready
```

### 4) OpenAPI (Swagger)

- `http://localhost:8000/docs`

### 5) Logs (opcional)

```bash
docker compose logs -f api
```

---

## Front-end

### Opção 1 — Dev simples (recomendado)

> Ajuste os comandos abaixo para a pasta do front (se necessário).

```bash
cd front
npm install
npm run dev
```

### Login (JWT) no front

- Faça login pela UI.
- O front armazena o token e o envia no `Authorization: Bearer <token>`.

### Telas principais

- **Login**
- **TRUSTED** (consulta/listagem)
- **REJEIÇÕES** (consulta/listagem)

---

## Configuração

### Variáveis de ambiente

Crie um `.env` baseado no `.env.example`.

Exemplo (referência):

```env
DATABASE_URL=postgresql+psycopg://appuser:apppass@db:5432/appdb
APP_ENV=local

JWT_SECRET=change-me
JWT_ALG=HS256
JWT_EXPIRES_MIN=60
```

> No Docker, o host do Postgres é `db` (nome do serviço).

---

## Banco e migrations (Alembic)

Aplicar migrations (dentro do container da API):

```bash
docker compose exec api sh -c "alembic upgrade head"
```

Criar revision:

```bash
docker compose exec api alembic revision -m "mensagem"
```

---

## Segurança

### 1) API Key por fonte

**Conceito:** cada *source* possui uma API Key. A API recebe a chave e compara com o **hash** persistido no banco.

#### Gerar API Key + Hash (dentro do container)

```bash
docker compose exec api python -m app.scripts.generate_api_key
```

> Guarde a API Key com segurança. O banco deve armazenar apenas o **hash**.

#### Salvar o hash no banco (para uma source existente)

Use o script/rota prevista no projeto (ou rode a atualização no DB conforme o guia do projeto).  
A ideia é: **DB guarda hash** → cliente envia **API Key** → API valida.

### 2) Login — JWT

#### Login

- Endpoint de login retorna um JWT.
- Demais rotas protegidas exigem `Authorization: Bearer <token>`.

### 3) RBAC

- Perfis e permissões restringem o acesso por rota (ex.: operador, admin etc.).
- Retornos **403** quando o papel não tem permissão.

### 4) Auditoria e security events

- Ações sensíveis (ex.: patch em TRUSTED, rejeições e operações administrativas) geram auditoria.
- Eventos de segurança (ex.: tentativas inválidas, violações) são registrados para investigação.

---

## Endpoints (referência)

> A lista completa está no Swagger: `http://localhost:8000/docs`.

- **Health:** `GET /api/v1/health`
- **Readiness:** `GET /api/v1/ready`
- **Métricas:** `GET /api/v1/metrics`
- **Ingestão (API Key):** `POST /api/v1/ingest`
- **Login (JWT):** `POST /api/v1/auth/login`
- **Consultas:** rotas de TRUSTED e REJEIÇÕES (ver Swagger)

---

## Observabilidade

- `X-Request-Id`
  - Se o cliente enviar `X-Request-Id`, a API propaga.
  - Se não enviar, a API gera um novo.
- `X-Process-Time-Ms` em respostas (latência do processamento)
- `/metrics` com contadores básicos
- `/ready` valida “API ok” + “DB ok”

---

## Deploy (produção-lite)

Este projeto inclui um cenário de deploy com **Docker Compose** e **Nginx** como reverse proxy:

- Nginx → API (Uvicorn/FastAPI)
- PostgreSQL com volume
- Healthchecks para estabilização do stack

### HTTPS (futuro)

O bloco HTTPS do Nginx pode ser habilitado quando houver domínio público:

1. Apontar DNS (registro A) para o IP do servidor
2. Ajustar `server_name` no Nginx
3. Gerar certificado (ex.: Certbot)
4. Ativar `listen 443 ssl`
5. Validar `https://SEU_DOMINIO/api/v1/health`

---

## Testes

```bash
docker compose exec -e PYTHONPATH=/app api pytest -q
```

---

## Autor

**Robert Emanuel**  
Back-end Developer (Python/FastAPI • SQL • Docker • Segurança)
