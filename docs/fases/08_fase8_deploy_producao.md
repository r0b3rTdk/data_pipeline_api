# Fase 8 — Deploy / Produção (Docker + Nginx) — Produção-Lite

## Objetivo

Disponibilizar o **Projeto01 - Data Pipeline API** em um ambiente Linux com estrutura de produção-lite, utilizando:

- Docker Compose (produção)
- PostgreSQL em container com volume persistente
- API FastAPI em container
- Nginx como reverse proxy
- Healthchecks e restart policy
- Configuração por variáveis de ambiente (`.env.prod`)

> **Observação:** nesta fase, o deploy foi validado em **HTTP** (sem HTTPS), pois o projeto é de portfólio e ainda não há domínio público configurado.  
> A estrutura para HTTPS com Certbot/Let's Encrypt foi preparada para ativação futura.

---

## Escopo entregue nesta fase

### Entregue e validado (produção-lite)
- `docker-compose.prod.yml`
- Nginx como reverse proxy (`/api/ -> api:8000`)
- Banco PostgreSQL com volume persistente (`db_data`)
- Healthchecks de `db` e `api`
- `restart: unless-stopped`
- `.env.prod` (fora do Git)
- Seed inicial (admin + source system)
- Teste de login via Nginx
- Teste de ingest via Nginx com `X-API-Key`

### Preparado para etapa futura
- HTTPS com Certbot/Let's Encrypt (requer domínio apontando para IP público)

---

## Estrutura de arquivos usada no deploy

- `docker-compose.prod.yml`
- `deploy/nginx/default.conf`
- `.env.prod.example` (modelo)
- `.env.prod` (real, **não versionado**)

---

## Pré-requisitos (servidor Linux / Ubuntu)

- Docker instalado
- Docker Compose plugin instalado (`docker compose`)
- Porta 80 liberada (firewall/UFW), se for acessar externamente
- (Futuro HTTPS) domínio apontando para IP público + portas 80/443 liberadas

---

## Configuração de ambiente de produção

### 1) Criar pasta e clonar repositório

```bash
sudo mkdir -p /opt/projeto01
sudo chown $USER:$USER /opt/projeto01
git clone https://github.com/r0b3rTdk/data_pipeline_api /opt/projeto01
cd /opt/projeto01
```

### 2) Criar `.env.prod`

Criar arquivo real de produção a partir do modelo:

```bash
cp .env.prod.example .env.prod
nano .env.prod
```

### 3) Variáveis importantes (produção-lite)

Exemplo de configuração (ajustar valores reais):

```env
APP_ENV=prod
LOG_LEVEL=INFO

POSTGRES_DB=appdb
POSTGRES_USER=appuser
POSTGRES_PASSWORD=SENHA_FORTE_AQUI

DATABASE_URL=postgresql+psycopg://appuser:SENHA_FORTE_AQUI@db:5432/appdb

JWT_SECRET=CHAVE_JWT_FORTE_32_CHARS_OU_MAIS
JWT_ALG=HS256
JWT_EXPIRES_MIN=60

# Temporário enquanto não houver domínio real
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

MAX_BODY_BYTES=1000000

SEED_ON_STARTUP=false
SEED_ADMIN_USERNAME=admin
SEED_ADMIN_EMAIL=admin@local.test
SEED_ADMIN_PASSWORD=SENHA_FORTE_ADMIN
SEED_SOURCE_NAME=partner_a
SEED_SOURCE_API_KEY=CHAVE_FORTE_SOURCE
```

> **Importante:** `POSTGRES_PASSWORD` e a senha dentro de `DATABASE_URL` devem ser idênticas.

---

## Subindo os containers (produção-lite)

### 1) Subir ambiente

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

### 2) Verificar status

```bash
docker compose -f docker-compose.prod.yml ps
```

Esperado:
- `db` → healthy
- `api` → healthy
- `nginx` → running

---

## Migrations e seed

### 1) Aplicar migrations

```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### 2) Executar seed (primeira vez)

```bash
docker compose -f docker-compose.prod.yml exec api python -m app.scripts.seed
```

Saída esperada (exemplo):
- `Seed OK`
- `Admin username: admin`
- `Source name: partner_a`

---

## Validações realizadas (HTTP via Nginx)

### 1) Healthcheck da API via proxy

```bash
curl -i http://localhost/api/v1/health
```

Resultado esperado:
- `HTTP/1.1 200 OK`
- body com `{"status":"ok"}`

---

### 2) Login JWT via Nginx

```bash
curl -i -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SENHA_DO_SEED_ADMIN"}'
```

Resultado esperado:
- `HTTP/1.1 200 OK`
- retorno com `access_token`

---

### 3) Ingest via Nginx com `X-API-Key`

```bash
curl -i -X POST http://localhost/api/v1/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: CHAVE_DO_SEED_SOURCE" \
  -d '{
    "source": "partner_a",
    "external_id": "ext-prod-test-001",
    "entity_id": "ent-001",
    "event_status": "NEW",
    "event_timestamp": "2026-02-24T00:00:00Z",
    "event_type": "ORDER",
    "severity": "low",
    "payload": {"test": true}
  }'
```

Resultado esperado (exemplo):
```json
{"status":"ACCEPTED","raw_id":1,"trusted_id":1,"request_id":"..."}
```

---

## Persistência de dados (volume do Postgres)

O volume `db_data` foi criado e validado durante a fase.

### Validação prática realizada
1. Ingest inicial (`raw_id=1`, `trusted_id=1`)
2. Reinício dos containers
3. Novo ingest com novo `external_id`
4. IDs incrementando (`raw_id=2`, `trusted_id=2`)

Isso confirma que os dados persistiram após reinício.

---

## Reinício dos serviços (restart / recovery)

### Reiniciar serviços

```bash
docker compose -f docker-compose.prod.yml restart
```

### Observação
Logo após o `restart`, pode haver falha temporária em requests (`connection reset`) enquanto:
- `db` está iniciando (`health: starting`)
- `api` aguarda disponibilidade
- `nginx` reinicia

Após alguns segundos, o endpoint `/api/v1/health` volta a responder normalmente.

---

## Nginx e HTTPS (situação nesta fase)

O Nginx foi configurado com reverse proxy funcional em **HTTP (porta 80)**.

### Situação do bloco HTTPS
O bloco HTTPS (`listen 443 ssl`) foi deixado **desativado temporariamente**, porque:
- ainda não existe domínio apontando para o servidor
- os certificados em `/etc/letsencrypt/...` ainda não foram gerados

### Próximo passo futuro (quando houver domínio)
1. Configurar `server_name` com domínio real
2. Gerar certificado com Certbot
3. Reativar bloco HTTPS no `default.conf`
4. Validar `https://SEU_DOMINIO/api/v1/health`

---

## Observações de configuração (Compose e `.env`)

Durante a fase foi observado warning do Docker Compose:

- `The "POSTGRES_PASSWORD" variable is not set. Defaulting to a blank string.`

### Causa
Esse warning ocorre na etapa de **interpolação do arquivo compose**, antes do `env_file` do serviço ser considerado.

### Ajuste aplicado no servidor
Foi criado um `.env` local (não versionado) com base no `.env.prod` para eliminar o warning:

```bash
cp .env.prod .env
```

> Isso é apenas para leitura de variáveis pelo Compose no servidor.  
> O arquivo real de produção continua sendo o `.env.prod`.

---

## Comandos úteis (produção-lite)

### Status
```bash
docker compose -f docker-compose.prod.yml ps
```

### Logs da API
```bash
docker compose -f docker-compose.prod.yml logs -n 200 api
```

### Logs do Nginx
```bash
docker compose -f docker-compose.prod.yml logs -n 200 nginx
```

### Logs do DB
```bash
docker compose -f docker-compose.prod.yml logs -n 200 db
```

### Restart
```bash
docker compose -f docker-compose.prod.yml restart
```

---

## Resultado da Fase 8 (estado atual)

A fase foi concluída em modo **produção-lite**, com validação funcional completa em HTTP no servidor:

- API operacional via Nginx
- autenticação JWT funcional
- ingestão com API key funcional
- banco persistente e saudável
- ambiente resiliente a restart

HTTPS ficou **preparado** para ativação futura quando houver domínio.
