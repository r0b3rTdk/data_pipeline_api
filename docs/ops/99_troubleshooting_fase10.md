# 99 — Troubleshooting (Fase 10: CI/CD)

Este documento registra os principais erros encontrados ao configurar o CI no GitHub Actions e como resolvemos cada um deles.

---

## 1) Pipeline não roda / não aparece no GitHub

**Sintoma**
- Nada aparece na aba **Actions** após `git push`.

**Causa**
- O GitHub Actions só executa pipelines se existir um workflow em:
  - `.github/workflows/*.yml`

**Correção**
- Criar o arquivo:
  - `.github/workflows/ci.yml`
- Comitar e dar push.

---

## 2) Falha no lint (flake8) com muitos erros de estilo

**Sintoma**
- Step **Run lint (flake8)** falha.
- Erros comuns: `E302`, `E305`, `W291`, `W292`, `W293`, `E501` (linha >79).

**Causa**
- O projeto não estava formatado para as regras padrões do flake8 (muito estritas por padrão).
- No CI o flake8 roda “do zero” e barra o pipeline antes de migrations/testes.

**Correção recomendada**
- Criar um arquivo **.flake8** na raiz do projeto para ajustar as regras ao padrão do projeto e destravar o CI.

Exemplo usado (resumo):
- aumentar `max-line-length`
- ignorar regras puramente “estéticas”
- excluir migrations geradas (versions)

> Observação: A ideia é manter lint útil (imports quebrados, sintaxe, erros reais) sem travar o CI por whitespace.

---

## 3) Erro `E402 module level import not at top of file`

**Sintoma**
- Step **Run lint (flake8)** falha com:
  - `E402 module level import not at top of file`
- Ex.: `app/core/security.py`

**Causa**
- Existiam imports no meio do arquivo (depois de constantes, funções ou execução de código).

**Correções possíveis**
1. **Mover imports para o topo do arquivo** (preferível quando não há dependência circular).
2. Se o import precisar ser local (para evitar circular import), manter dentro da função e usar:
   - `# noqa: E402`

---

## 4) Driver do Postgres no CI (psycopg v3 vs psycopg2)

**Sintoma**
- Migrations/testes falham por driver/URL incompatível (ou erro de conexão/engine).

**Causa**
- O projeto usa `psycopg[binary]` (psycopg v3), mas o CI estava configurado com:
  - `postgresql+psycopg2://...`

**Correção**
- Atualizar `DATABASE_URL` no `ci.yml` para o driver correto do projeto:
  - `postgresql+psycopg://appuser:apppass@localhost:5432/appdb`

---

## 5) Testes falhando no CI por depender de dados pré-existentes

### 5.1) `No trusted_event found...` (banco vazio no CI)

**Sintoma**
- Pytest falha em `tests/test_audit.py` com:
  - `AssertionError: No trusted_event found...`

**Causa**
- No GitHub Actions, o banco começa vazio a cada run.
- O teste assumia que já existia um `TrustedEvent` no DB.

**Correção**
- Criar fixtures que inserem os dados necessários no DB antes do teste rodar.
- Recomendação: usar fixture `trusted_event` no `tests/conftest.py` e injetar no teste:
  - `def test_...(client, db_session, trusted_event): ...`

### 5.2) Erros ao criar `SourceSystem`/`RawIngestion` por campos obrigatórios

**Sintomas**
- `TypeError: 'is_active' is an invalid keyword argument for SourceSystem`
- `IntegrityError` por colunas NOT NULL ao criar `RawIngestion` e/ou `TrustedEvent`

**Causas**
- `SourceSystem` não possuía o atributo `is_active` (model diferente).
- `RawIngestion` e `TrustedEvent` possuem campos e FKs obrigatórias (`NOT NULL`), por exemplo:
  - `source_id`, `raw_ingestion_id`
  - `external_id`, `event_timestamp`, `payload_raw`, `payload_hash`, `request_id`, etc.

**Correção**
- Ajustar a fixture para criar a “cadeia” mínima correta:
  1) `SourceSystem`
  2) `RawIngestion` com todos campos NOT NULL
  3) `TrustedEvent` referenciando `source_id` e `raw_ingestion_id`

> Dica: quando der `IntegrityError`, o log sempre aponta a coluna que faltou. Ajuste a fixture e reexecute.

---

## 6) Como depurar rapidamente no GitHub Actions

1) Abra o repositório no GitHub
2) Aba **Actions**
3) Clique no run que falhou (vermelho)
4) Abra o step com erro (ex.: **Run lint**, **Run database migrations**, **Run tests**)
5) Copie o trecho do log do erro — ele costuma ser suficiente para corrigir em 1 iteração.

---

## Checklist de “CI OK” (Fase 10)

- Workflow em `.github/workflows/ci.yml`
- Flake8 passa no CI
- Postgres service sobe com healthcheck
- `alembic upgrade head` roda no CI
- `pytest -q` passa no CI
- Run aparece verde na aba **Actions**
