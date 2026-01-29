# Contrato do Evento (V1)
## Formato padrão de entrada para ingestão (API)

> **Objetivo**  
> Definir um contrato único (campos, tipos, regras e limites) para eventos enviados por sistemas parceiros para a API.  
> Esse contrato é a base para: **validação**, **normalização**, **deduplicação/idempotência**, **persistência RAW/TRUSTED** e **rastreamento**.

---

## 1. Visão geral do evento

Um **evento** representa uma ocorrência operacional (ex.: atualização de status, registro de movimentação, confirmação de entrega, etc.).  
O evento chega pela API e passa por:
1) **validação de contrato** (campos/tipos/formato)  
2) **registro RAW obrigatório** (evidência)  
3) **normalização + regras de negócio**  
4) **TRUSTED** (se válido) ou **REJEIÇÃO** (se inválido)

---

## 2. Estrutura do payload (JSON)

O payload de ingestão é composto por 3 blocos:

- **metadata**: informações de rastreio e origem (obrigatórias)
- **event**: informações do evento em si (obrigatórias)
- **attributes**: campos adicionais opcionais (controlados)

### 2.1 Campos obrigatórios (mínimo V1)

| Campo | Caminho | Tipo | Obrigatório | Regras |
|------|--------|------|-------------|--------|
| Origem do sistema | `metadata.source` | string | Sim | Deve existir no cadastro de origens (`source_system`) |
| ID externo do evento | `metadata.external_id` | string | Sim | Unicidade por origem (base para idempotência) |
| Timestamp do evento | `metadata.event_timestamp` | string (ISO 8601) | Sim | Ex.: `2026-01-26T10:20:30Z` |
| Tipo do evento | `event.type` | string | Sim | Deve estar no catálogo `event_type` |
| Status do evento | `event.status` | string | Sim | Deve estar no catálogo `event_status` |
| ID do objeto de negócio | `event.entity_id` | string | Sim | Identifica o “alvo” do evento (ex.: entrega/pedido/registro) |

### 2.2 Campos recomendados (importantes na prática)

| Campo | Caminho | Tipo | Obrigatório | Regras |
|------|--------|------|-------------|--------|
| Versão do contrato | `metadata.schema_version` | string | Sim (recomendado) | Ex.: `v1` |
| ID de correlação | `metadata.correlation_id` | string | Não | Útil para rastrear uma sequência de eventos |
| Prioridade | `event.priority` | string | Não | Catálogo fechado: `low`, `normal`, `high` |
| Descrição | `event.description` | string | Não | Limite de tamanho (ver seção 4) |

### 2.3 Campos opcionais (attributes)
`attributes` pode existir para informações extras, desde que:
- seja um objeto simples (chave/valor)
- não ultrapasse limites de tamanho
- não contenha dados sensíveis desnecessários (ver seção 5)

Exemplos de chaves comuns:
- `attributes.location`
- `attributes.operator`
- `attributes.channel`
- `attributes.notes`

---

## 3. Catálogos (V1)

> **Importante:** Os valores exatos dos catálogos ficam no arquivo `docs/03_catalogos_e_regras.md`.  
> Aqui apenas definimos que são **fechados** e validados.

### 3.1 event.type (catálogo fechado)
Exemplos comuns (você pode usar como base):
- `status_update`
- `created`
- `progress`
- `completed`
- `canceled`

### 3.2 event.status (catálogo fechado)
Exemplos comuns (você pode usar como base):
- `CREATED`
- `IN_PROGRESS`
- `ON_HOLD`
- `COMPLETED`
- `CANCELED`

---

## 4. Regras de validação de contrato (V1)

### 4.1 Regras de formato
- `metadata.event_timestamp` deve estar em **ISO 8601**.
- Strings devem ser **trimadas** (sem espaços desnecessários nas pontas).
- Campos obrigatórios não podem ser vazios.

### 4.2 Regras de tamanho (limites)
- `metadata.source`: máx **50**
- `metadata.external_id`: máx **120**
- `metadata.correlation_id`: máx **120**
- `event.type`: máx **40**
- `event.status`: máx **40**
- `event.entity_id`: máx **120**
- `event.description`: máx **500**
- `attributes`: máx **30 chaves** e cada valor máx **200**

> Se algum limite for excedido, deve gerar **REJEIÇÃO** (categoria `CONTRACT_INVALID` ou `PAYLOAD_LIMIT`).

### 4.3 Regras de campos inesperados
Na V1:
- campos extras fora de `metadata`, `event`, `attributes` devem ser **rejeitados** (para manter contrato controlado)  
ou, alternativamente (se você preferir), podem ser **ignorados** e registrados no RAW.  
> **Escolha uma política e mantenha consistente** (recomendação: rejeitar campos no nível raiz para evitar abuso).

---

## 5. Regras de segurança no contrato

### 5.1 Dados sensíveis
Evitar no payload (ou mascarar) informações como:
- documentos pessoais
- dados financeiros
- credenciais, tokens, segredos

Se aparecerem:
- registrar no RAW com cuidado (ideal: mascarar em logs)
- gerar evento de segurança (`security_event`) se houver tentativa suspeita

### 5.2 Proteção contra abuso
- Limitar tamanho total do payload (ex.: **até 32KB** na V1)
- Rate limit por origem (mínimo viável) — pode ser V2
- Rejeitar payloads com “explosão” de `attributes`

---

## 6. Deduplicação / Idempotência (base do contrato)

A deduplicação na V1 deve considerar pelo menos:
- `metadata.source` + `metadata.external_id`

Opcionalmente (mais forte):
- hash do payload + `metadata.source`

Regras:
- Se o mesmo evento for enviado novamente, a API deve retornar status **DUPLICATE**.
- Não criar novo registro TRUSTED.
- Ainda deve existir rastreabilidade (RAW pode registrar a tentativa ou vincular ao original, conforme regra que você definir na implementação).

---

## 7. Respostas esperadas (conceito)

### 7.1 Resposta de sucesso (aceito)
Deve retornar:
- `ingestion_id` (id interno do RAW)
- `trusted_id` (id interno do TRUSTED, se criado)
- `status`: `ACCEPTED`
- `processed_at`

### 7.2 Resposta de rejeição
Deve retornar:
- `ingestion_id`
- `status`: `REJECTED`
- lista de erros com:
  - `category`
  - `field`
  - `message`
  - `rule`

### 7.3 Resposta de duplicado
Deve retornar:
- `status`: `DUPLICATE`
- referência do evento original (se aplicável)

---

## 8. Exemplos rápidos (válido / inválido)

> **Obs.:** são exemplos conceituais para guiar entendimento do contrato.

### Exemplo válido (conceitual)
- `metadata.source` preenchido e existente
- `metadata.external_id` preenchido
- `metadata.event_timestamp` ISO 8601
- `event.type` no catálogo
- `event.status` no catálogo
- `event.entity_id` preenchido

### Exemplo inválido (conceitual)
- `event.status` fora do catálogo
- `metadata.event_timestamp` em formato errado
- `event.description` acima do limite
- payload acima de 32KB

---

## 9. Critérios de aceite do contrato (DoD)
O contrato está “pronto” quando:
- Todos os campos obrigatórios estão definidos (nome, tipo, regras).
- Limites e formato estão definidos.
- Catálogos referenciados estão definidos (arquivo de catálogos).
- Está claro como funciona idempotência/deduplicação.
