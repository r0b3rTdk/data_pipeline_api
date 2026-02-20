# docs/99_troubleshooting_fase3.md — Erros reais da Fase 3 + Como corrigir

Este arquivo registra **enroscos reais** que aconteceram durante a Fase 3 e como foram resolvidos.
A ideia é você colar isso no repo para mostrar maturidade (debug, troubleshooting e domínio de ambiente).

---

## 01) `docker` não reconhecido no PowerShell / VS Code

**Sintoma**
- `docker : O termo 'docker' não é reconhecido ...`

**Causa**
- Docker Desktop instalado, mas `docker.exe` não estava no `PATH` daquele terminal (ou o VS Code estava usando um shell/ambiente diferente).

**Correção**
- Conferir se existe:
  - `C:\Program Files\Docker\Docker\resources\bin\docker.exe`
- Adicionar ao PATH na sessão:
  ```powershell
  $env:Path += ";C:\Program Files\Docker\Docker\resources\bin"
  docker --version
  docker compose version
  ```
- Dica: às vezes funciona no PowerShell “normal” e não no terminal integrado do VS Code por diferença de ambiente.

---

## 02) `no configuration file provided: not found`

**Sintoma**
- `docker compose up --build` → `no configuration file provided: not found`

**Causa**
- Rodou o comando fora da pasta onde está o `docker-compose.yml`.

**Correção**
- `cd` para a raiz do projeto antes:
  ```powershell
  cd "E:\PROGRAMACAO\PROJETOS\PROJETO 01"
  docker compose up -d --build
  ```

---

## 03) Erro de engine no Windows (pipe do Docker Desktop)

**Sintoma**
- `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`

**Causa**
- Docker Desktop não estava rodando, engine não iniciou, ou alternância de engine (Linux/WSL2) gerou inconsistência.

**Correção**
- Abrir Docker Desktop e aguardar ficar “Running”.
- Reiniciar Docker Desktop quando necessário.
- Depois:
  ```powershell
  docker compose up -d --build
  ```

---

## 04) `FROM python:3.12-slim` rodado no PowerShell (erro “from não tem suporte”)

**Sintoma**
- Você colou conteúdo do Dockerfile no PowerShell e recebeu:
  - `A palavra-chave 'from' não tem suporte ...`

**Causa**
- `FROM` é instrução de **Dockerfile**, não comando de terminal.

**Correção**
- Criar/editar um arquivo chamado `Dockerfile` e colocar o conteúdo lá.
- No terminal, rodar:
  ```powershell
  docker compose up -d --build
  ```

---

## 05) Alembic: `Can't load plugin: sqlalchemy.dialects:driver`

**Sintoma**
- `alembic upgrade head` falha com:
  - `sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:driver`

**Causa**
- `sqlalchemy.url` (no `alembic.ini`) ficou no placeholder `driver://...` (URL do banco não configurada).

**Correção (recomendado)**
- Configurar URL real via env var (ex.: `DATABASE_URL`) e no `env.py` ler essa variável.
- Exemplo de URL:
  - `postgresql+psycopg://appuser:apppass@db:5432/appdb`

---

## 06) `psql: not found` dentro do container `api`

**Sintoma**
- Dentro do container `api`: `psql: not found`

**Causa**
- O client `psql` não vem instalado na imagem da API.

**Correções**
- Rodar `psql` no container do banco:
  ```powershell
  docker compose exec db psql -U appuser -d appdb
  ```
- (Opcional) instalar `postgresql-client` na imagem da API (não obrigatório na V1).

---

## 07) Alembic: `FileNotFoundError ... script.py.mako`

**Sintoma**
- `alembic revision -m "..."`
  - `FileNotFoundError: ... app/infra/db/migrations/script.py.mako`

**Causa**
- `script_location` apontando para pasta errada ou estrutura duplicada `migrations/migrations`.
- Template `script.py.mako` não estava onde o Alembic esperava.

**Correção**
- Padronizar:
  - `script_location = app/infra/db/migrations`
  - garantir `script.py.mako` nessa pasta.
- Se houver `migrations/migrations`, corrigir para **um único nível**.

---

## 08) Migration “sumiu” do repo / Alembic não acha revision

**Sintoma**
- `Can't locate revision identified by '4e1d113c69c0'`
- No Postgres, `alembic_version` estava nessa revision, mas o arquivo `.py` não existia no seu Windows/repo.

**Causa**
- Migration criada dentro do container sem bind/volume do diretório, ou rebuild apagou o arquivo que não estava no host.
- Resultado: DB aponta para uma revision que o código não possui.

**Correção**
- Garantir que os arquivos de migration existam no repo (host).
- Se necessário, copiar/criar manualmente a migration faltante no host.
- Quando o DB e o código ficaram “desalinhados”, foi necessário **reaplicar** corretamente as migrations (após restaurar os arquivos), e então rodar `alembic upgrade head`.

**Boa prática**
- Sempre criar migrations com o projeto montado no container (bind) ou gerar no host.

---

## 09) PowerShell: `curl` é alias do `Invoke-WebRequest`

**Sintoma**
- `curl -X ... -H ... -d ...` falha com:
  - `Não é possível localizar um parâmetro ... 'X'`
  - `-H` e `-d` não reconhecidos

**Causa**
- No Windows PowerShell, `curl` **não é** o curl tradicional; é alias para `Invoke-WebRequest`.

**Correções**
- Usar `Invoke-RestMethod`:
  ```powershell
  Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/ingest" -ContentType "application/json" -Body '{...}'
  ```
- Ou usar `curl.exe`:
  ```powershell
  curl.exe -X POST ...
  ```

---

## 10) `TypeError: Object of type datetime is not JSON serializable`

**Sintoma**
- `POST /ingest` retornava 500 e log mostrava:
  - `TypeError: Object of type datetime is not JSON serializable`

**Causa**
- `json.dumps(payload_dict)` recebia `datetime` (Pydantic converte `event_timestamp` para `datetime`).
- `json.dumps` puro não serializa datetime.

**Correção (melhor)**
- Antes de calcular hash / salvar payload_raw:
  - `payload_dict = req.model_dump(mode="json")`
- Assim `event_timestamp` vira string ISO e `json.dumps` funciona.

**Alternativa**
- `json.dumps(..., default=str)` (resolve, mas é “menos elegante” que `mode="json"`).

---

## 11) API não subia: `NameError: name 'app' is not defined`

**Sintoma**
- Uvicorn falhava ao iniciar:
  - `NameError: name 'app' is not defined`

**Causa**
- Chamou `app.include_router(...)` sem definir `app = FastAPI()`.

**Correção**
- Em `app/main.py`:
  ```python
  app = FastAPI(...)
  app.include_router(...)
  ```

---

## 12) API não subia: `ModuleNotFoundError: No module named 'app.infra.db.repositories'`

**Sintoma**
- Import falhava para `app.infra.db.repositories.*`

**Causa**
- Pasta/arquivos não existiam no container (ou nome diferente).
- Falta de `__init__.py` em pastas de pacote.

**Correção**
- Garantir no host e no container:
  - `app/infra/db/repositories/` com `__init__.py` + arquivos `.py`
- Criar `__init__.py` vazios em pastas relevantes (app/, infra/, db/, repositories/).

---

## 13) `psql` travando em `(END)` ao mostrar resultados

**Sintoma**
- Query mostra `(END)` e não volta.

**Causa**
- Pager do `psql` (tipo `less`) está ativo.

**Correção**
- Sair com `q`
- Ou desligar pager:
  ```powershell
  docker compose exec db psql -U appuser -d appdb -P pager=off -c "select 1;"
  ```

---

## 14) Aspas/escape em comandos `docker compose exec ... python -c ...`

**Sintoma**
- Erros de aspas no PowerShell ao tentar `python -c "...os.getenv(...)"`

**Correção**
- Preferir `env | findstr`:
  ```powershell
  docker compose exec api env | findstr DATABASE_URL
  ```
- Ou:
  ```powershell
  docker compose exec api printenv DATABASE_URL
  ```

---

## Checklist final de validação (Fase 3)

- Subir:
  ```powershell
  docker compose up -d --build
  ```
- Health:
  ```powershell
  Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/health"
  ```
- Ingest:
  - 1x payload válido → `ACCEPTED`
  - reenviar mesmo payload → `DUPLICATE`
  - status inválido → `REJECTED`
- Consultas:
  ```powershell
  Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/trusted?page=1&page_size=50"
  Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/rejections?page=1&page_size=50"
  ```
- Confirmar tabelas:
  ```powershell
  docker compose exec db psql -U appuser -d appdb -P pager=off -c "\dt"
  ```

---

## Nota de entrega

Esse arquivo deve ficar no repo em `docs/99_troubleshooting_fase3.md`.
Ele mostra que você:
- sabe montar ambiente
- sabe debugar Docker/Alembic/SQL/Python
- sabe registrar incidentes e correções (maturidade de engenharia)
