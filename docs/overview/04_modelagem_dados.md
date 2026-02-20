# Modelagem de Dados (Fase 2) — V1
## RAW → TRUSTED → REJEIÇÕES + Auditoria + Segurança

## Diagramas
Coloque os arquivos em `docs/diagramas/` e mantenha os nomes abaixo.

- ER: `docs/diagramas/ER.jpg`  
![ER](diagramas/ER.jpg)

- MER/Tabelas: `docs/diagramas/MER.jpg`
![MER](diagramas/MER.jpg)
  
- Pipeline: `docs/diagramas/PIPELINE.jpg`  
![PIPELINE](diagramas/PIPELINE.jpg)

- RBAC: `docs/diagramas/RBAC.jpg`  
![RBAC](diagramas/RBAC.jpg)

## Tabelas (V1) e finalidade
- `source_system`: origens/parceiros autorizados
- `raw_ingestion`: evidência de toda ingestão (sempre grava)
- `trusted_event`: dados normalizados e aprovados
- `rejection`: erros estruturados de uma ingestão
- `user_account`, `role`, `user_role`: RBAC
- `audit_log`: histórico de alterações em TRUSTED (before/after + motivo)
- `security_event`: eventos de segurança (auth falha, acesso negado, abuso)

## Decisões-chave (V1)
1) **RAW sempre grava**: toda requisição cria `raw_ingestion`.
2) **1 RAW → no máximo 1 TRUSTED**: `trusted_event.raw_ingestion_id` é **UNIQUE**.
3) **Idempotência no TRUSTED**: `trusted_event` tem **UNIQUE(source_id, external_id)**.
4) **Rejeições sempre apontam para RAW**: `rejection.raw_ingestion_id` é FK obrigatório.
5) **Auditoria obrigatória** para mudanças em TRUSTED: `audit_log` com before/after + motivo + usuário.
6) **Security events** podem ter `source_id` e/ou `actor_user_id` (opcionais).

## Índices mínimos recomendados
- `trusted_event`: `(source_id, event_timestamp)`, `(entity_id, event_timestamp)`, `(event_status)`, `UNIQUE(source_id, external_id)`
- `raw_ingestion`: `(source_id, received_at)`, `(source_id, external_id)`, `(payload_hash)`
- `rejection`: `(raw_ingestion_id)`, `(category, created_at)`, `(severity, created_at)`

