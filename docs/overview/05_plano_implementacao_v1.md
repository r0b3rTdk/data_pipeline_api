# Plano de Implementação V1 (Fase 2)
## Arquitetura + API + Migrações/Constraints (enxuto e executável)

> **Objetivo**  
> Este documento consolida o plano técnico da V1 para você sair dos requisitos/modelagem (Fase 1 + doc 04) e começar a implementar com clareza:
> - estrutura do projeto (camadas e pastas)
> - endpoints V1 + RBAC
> - plano de migrações/constraints/índices/seed
>
> **Obs.:** Diagramas e modelagem detalhada ficam no `docs/04_modelagem_dados.md`.

---

# 1) Arquitetura e Estrutura do Projeto

## 1.1 Camadas (responsabilidades)
### API (apresentação)
- recebe request
- autentica/autoriza (RBAC)
- valida entrada (contrato)
- chama services
- retorna resposta padronizada

### Services (casos de uso)
- implementa o fluxo do sistema (pipeline)
- coordena domínio + repositórios + transações
- decide status final: `ACCEPTED` / `REJECTED` / `DUPLICATE`

### Domain (regras)
- catálogos e transições
- validação semântica (negócio)
- decisões puras (sem FastAPI e sem banco)

### Infra (persistência)
- sessão/conexão do banco
- repositórios e queries
- migrações

### Core (cross-cutting)
- configuração por env
- logging estruturado (request_id)
- constantes/enums
- RBAC helpers

---

## 1.2 Estrutura de pastas recomendada (V1)

```
project-root/
  app/
    main.py

    api/
      routes/
        ingest.py
        events.py
        rejections.py
        raw.py
        audit.py
        security.py
        health.py
      schemas/
        ingest.py
        common.py
        events.py

    services/
      ingest_service.py
      query_service.py
      audit_service.py
      security_service.py

    domain/
      rules/
        catalogs.py
        transitions.py
        validation_contract.py
        validation_business.py
        dedup.py

    infra/
      db/
        session.py
        migrations/
      repositories/
        source_repo.py
        raw_repo.py
        trusted_repo.py
        rejection_repo.py
        audit_repo.py
        security_repo.py

    core/
      config.py
      logging.py
      rbac.py
      constants.py

  tests/
    unit/
    integration/

  docs/
    01_requisitos.md
    02_contrato_evento.md
    03_catalogos_e_regras.md
    04_modelagem_dados.md
    05_plano_implementacao_v1.md
    diagrams/

  docker-compose.yml
  README.md
```

---

## 1.3 Regras de responsabilidade (pra não virar bagunça)
- `api/routes/*` não contém regra de negócio.
- `services/*` contém o pipeline e orquestra transações.
- `domain/rules/*` contém validações semânticas, catálogos e transições.
- `infra/repositories/*` faz persistência e queries (sem lógica de negócio).
- `core/*` é configuração/logging/RBAC/constantes.

---

## 1.4 Observabilidade (V1)
- `request_id` por request (aceitar header se vier, senão gerar)
- logs estruturados com: `request_id`, endpoint, status_code, duration_ms, actor/source
- criar `security_event` em:
  - auth falha
  - acesso negado (403)
  - payload anômalo/limites (400 repetidos, tamanho, attributes explosivo)

---

# 2) Plano de API — Endpoints V1 + RBAC

## 2.1 Padrões gerais
- Base: `/api/v1`
- Listagens sempre paginadas: `page`, `page_size` (com limites)
- Resposta padrão inclui `request_id` e `status`
- Erros retornam `errors[]` quando aplicável

## 2.2 Endpoints (V1)

### Ingestão
**POST** `/api/v1/ingest`  
**Objetivo:** receber evento, salvar RAW, validar contrato/negócio, deduplicar, gerar TRUSTED ou REJEIÇÕES.  
**RBAC:** origem autenticada (client).

Retornos de negócio:
- `ACCEPTED` (trusted criado)
- `REJECTED` (rejeições criadas)
- `DUPLICATE` (sem novo trusted)

---

### TRUSTED
**GET** `/api/v1/events`  
Filtros: `source`, `entity_id`, `status`, `type`, `date_from`, `date_to`  
Paginação obrigatória.  
**RBAC:** `admin`, `analyst`, `operator`, `auditor`.

**GET** `/api/v1/events/{id}`  
Detalhe do trusted_event.  
**RBAC:** `admin`, `analyst`, `operator`, `auditor`.

*(opcional V1)* **PATCH** `/api/v1/events/{id}`  
Alteração de TRUSTED com `reason` obrigatório + criação de `audit_log`.  
**RBAC:** `admin` e (opcional) `analyst`.

---

### REJEIÇÕES
**GET** `/api/v1/rejections`  
Filtros: `source`, `category`, `severity`, `date_from`, `date_to`  
Paginação obrigatória.  
**RBAC:** `admin`, `analyst`, `auditor`.

**GET** `/api/v1/rejections/{id}`  
Detalhe de uma rejeição.  
**RBAC:** `admin`, `analyst`, `auditor`.

---

### RAW (evidência)
**GET** `/api/v1/raw`  
Filtros: `source`, `external_id`, `processing_status`, `date_from`, `date_to`  
Paginação obrigatória.  
**RBAC:** `admin`, `auditor`.

**GET** `/api/v1/raw/{id}`  
Detalhe do RAW (inclui payload original).  
**RBAC:** `admin`, `auditor`.

---

### AUDITORIA
**GET** `/api/v1/audit`  
Filtros: `entity_table`, `entity_id`, `actor_user`, `date_from`, `date_to`  
Paginação obrigatória.  
**RBAC:** `admin`, `auditor` (e `analyst` opcional, leitura limitada).

---

### EVENTOS DE SEGURANÇA
**GET** `/api/v1/security-events`  
Filtros: `event_type`, `severity`, `source`, `date_from`, `date_to`  
Paginação obrigatória.  
**RBAC:** `admin`, `auditor`.

---

### HEALTH
**GET** `/api/v1/health`  
Retorna status simples (e opcionalmente status do banco).  
**RBAC:** público (ou protegido, decisão sua).

---

## 2.3 Matriz RBAC (resumo)
- `admin`: tudo
- `analyst`: TRUSTED + REJEIÇÕES + (opcional) PATCH trusted com audit
- `operator`: TRUSTED + KPIs (se existir endpoint de métricas)
- `auditor`: RAW + AUDIT + SECURITY_EVENTS + leitura geral

---

# 3) Plano do Banco — Migrações, Constraints, Índices e Seed

## 3.1 Ordem recomendada das migrações (V1)
1. `source_system`
2. `raw_ingestion` (FK → source_system)
3. `trusted_event` (FK → raw_ingestion, FK → source_system)
4. `rejection` (FK → raw_ingestion)
5. `user_account`
6. `role`
7. `user_role` (FK → user_account, FK → role)
8. `audit_log` (FK → user_account)
9. `security_event` (FK opcional → source_system, FK opcional → user_account)

---

## 3.2 Constraints obrigatórias

### Integridade (FK)
- `raw_ingestion.source_id` → `source_system.id` (NOT NULL)
- `trusted_event.raw_ingestion_id` → `raw_ingestion.id` (NOT NULL)
- `trusted_event.source_id` → `source_system.id` (NOT NULL)
- `rejection.raw_ingestion_id` → `raw_ingestion.id` (NOT NULL)
- `user_role.user_id` → `user_account.id` (NOT NULL)
- `user_role.role_id` → `role.id` (NOT NULL)
- `audit_log.actor_user_id` → `user_account.id` (NOT NULL)
- `security_event.source_id` → `source_system.id` (NULL permitido)
- `security_event.actor_user_id` → `user_account.id` (NULL permitido)

### Unicidade (idempotência e consistência)
- `source_system.name` UNIQUE
- `role.name` UNIQUE
- `user_account.username` UNIQUE
- `user_role` PK composta: `(user_id, role_id)`
- `trusted_event.raw_ingestion_id` UNIQUE (**1 RAW → no máx 1 TRUSTED**)
- `trusted_event (source_id, external_id)` UNIQUE (**idempotência**)

### Checks / enums (mínimo)
- `raw_ingestion.processing_status` ∈ {ACCEPTED, REJECTED, DUPLICATE}
- `rejection.severity` ∈ {LOW, MEDIUM, HIGH, CRITICAL}
- `source_system.status` ∈ {active, inactive}
- `user_account.status` ∈ {active, inactive}

---

## 3.3 Índices mínimos (V1)
### `trusted_event`
- `(source_id, event_timestamp)`
- `(entity_id, event_timestamp)`
- `(event_status)`
- `UNIQUE(source_id, external_id)`

### `raw_ingestion`
- `(source_id, received_at)`
- `(source_id, external_id)`
- `(payload_hash)` (opcional)

### `rejection`
- `(raw_ingestion_id)`
- `(category, created_at)`
- `(severity, created_at)`

### Governança
- `audit_log`: `(entity_table, entity_id)` e `(actor_user_id, created_at)`
- `security_event`: `(event_type, created_at)`, `(severity, created_at)`, `(source_id, created_at)`

---

## 3.4 Seed mínimo (V1)
- Inserir roles: `admin`, `analyst`, `operator`, `auditor`
- Criar 1 origem local (ex.: `partner_local`) para testes

---

## 3.5 Política de deleção (V1)
- `raw_ingestion` e `audit_log`: não deletar fisicamente (evidência).
- `source_system` e `user_account`: usar `status = inactive` (soft delete).

---

# 4) Checklist “pronto para codar” (DoD)

Você pode iniciar a implementação quando:
- o `docs/04_modelagem_dados.md` está linkando os diagramas corretamente
- as constraints de idempotência (UNIQUE composto) estão claras
- a estrutura de pastas está criada no repo
- endpoints V1 e RBAC foram definidos aqui
- a ordem de migrações e índices mínimos foi definida aqui
