# Catálogos e Regras de Negócio (V1)
## Plataforma de Monitoramento, Processamento e Segurança de Dados

> **Objetivo**  
> Definir os **valores permitidos** (catálogos) e as **regras de negócio** que serão aplicadas após a validação do contrato do evento (`docs/02_contrato_evento.md`).  
> Este documento guia: **validação semântica**, **normalização**, **consistência**, **auditoria** e **classificação** (ACEITO / REJEITADO / SUSPEITO).

---

## 1. Conceitos importantes

### 1.1 Validação semântica (o que é)
É a validação que garante que o dado **faz sentido para o negócio**, mesmo que o formato esteja correto.  
Exemplos:
- Status existe no catálogo, mas a transição é inválida.
- Timestamp é ISO válido, mas está fora do intervalo aceitável.
- Evento é bem formado, mas contradiz o estado atual conhecido.

### 1.2 Classificação de resultado (V1)
Na V1, todo evento deve terminar com um status de processamento:

- **ACCEPTED**: entrou no TRUSTED.
- **REJECTED**: não entrou no TRUSTED; gerou rejeições com motivo.
- **DUPLICATE**: reenviado; não cria novo TRUSTED.
- **SUSPECT** *(opcional V1, recomendado como melhoria V2)*: não entra no TRUSTED automaticamente; fica separado para revisão.

> Se você quiser manter simples na V1, use apenas ACCEPTED/REJECTED/DUPLICATE e deixe SUSPECT para V2.

---

## 2. Catálogo: `event_type` (tipos de evento)

### 2.1 Lista de valores permitidos (V1)
- `status_update` — mudança de status do objeto.
- `created` — criação do objeto (primeiro evento).
- `progress` — avanço/etapa intermediária.
- `completed` — conclusão.
- `canceled` — cancelamento.

### 2.2 Regras associadas
- `created` deve ser o primeiro evento lógico do `entity_id` (quando o sistema tiver estado).
- `completed` e `canceled` são estados finais (ver transições).

---

## 3. Catálogo: `event_status` (status do objeto)

### 3.1 Lista de valores permitidos (V1)
- `CREATED`
- `IN_PROGRESS`
- `ON_HOLD`
- `COMPLETED`
- `CANCELED`

### 3.2 Significado (para clareza)
- **CREATED**: objeto registrado no sistema.
- **IN_PROGRESS**: objeto em execução/andamento.
- **ON_HOLD**: pausado por algum motivo.
- **COMPLETED**: finalizado com sucesso.
- **CANCELED**: finalizado por cancelamento.

---

## 4. Catálogo: `event_priority` (opcional na V1)

### 4.1 Valores permitidos
- `low`
- `normal`
- `high`

### 4.2 Regra
Se o campo estiver ausente, considerar `normal`.

---

## 5. Tabela de transições permitidas (regra crítica)

### 5.1 Transições válidas
Use esta tabela como regra base:

| Status atual | Pode ir para |
|------------|--------------|
| `CREATED` | `IN_PROGRESS`, `ON_HOLD`, `CANCELED` |
| `IN_PROGRESS` | `ON_HOLD`, `COMPLETED`, `CANCELED` |
| `ON_HOLD` | `IN_PROGRESS`, `CANCELED` |
| `COMPLETED` | *(nenhum — final)* |
| `CANCELED` | *(nenhum — final)* |

### 5.2 Regra de rejeição (semântica)
- Se um evento tentar fazer uma transição fora da tabela, deve gerar **REJEIÇÃO** com categoria `BUSINESS_INVALID_TRANSITION`.

> Observação: para aplicar essa regra você precisa conhecer o “status atual” do `entity_id` no TRUSTED.  
> Na V1, isso funciona bem porque o `trusted_event` será consultável por `entity_id` e o último status pode ser obtido.

---

## 6. Regras temporais (consistência de timestamp)

### 6.1 Janela aceitável de tempo (V1)
Defina uma política simples e objetiva:

- `event_timestamp` não pode estar mais de **+10 minutos no futuro** em relação ao servidor.
- `event_timestamp` não pode estar mais de **365 dias no passado**.

### 6.2 Tratamento
- Violação grave (muito fora da janela): **REJECTED** com categoria `BUSINESS_INVALID_TIME`.
- Leve desvio (ex.: até +10 min): pode ser aceito, mas logado como aviso *(opcional)*.

---

## 7. Regras de duplicidade / idempotência

### 7.1 Chave de idempotência (V1)
- `source + external_id` define unicidade por origem.

### 7.2 Comportamento esperado
- Se a chave já existir e o payload for igual: retornar **DUPLICATE**.
- Se a chave já existir e o payload for diferente: tratar como **SUSPECT** *(recomendado)* ou **REJECTED** com categoria `BUSINESS_CONFLICTING_DUPLICATE`.

> Se você quiser simplificar a V1: trate “mesma chave com payload diferente” como REJECTED.

---

## 8. Regras de normalização (V1)

### 8.1 Normalização de strings
- Remover espaços extras nas pontas (trim).
- Padronizar `status` em UPPERCASE.
- Padronizar `type` em lowercase.

### 8.2 Normalização de timestamp
- Converter e armazenar em formato único no banco (padrão do sistema).
- Sempre manter também o valor original no RAW.

---

## 9. Categorias de rejeição (padrão)

> **Objetivo:** padronizar os motivos e facilitar métricas.

### 9.1 Lista de categorias (V1)
- `CONTRACT_INVALID` — erro de contrato (campo faltando, tipo errado).
- `PAYLOAD_LIMIT` — excedeu limites (tamanho, attributes).
- `BUSINESS_INVALID_STATUS` — status fora do catálogo.
- `BUSINESS_INVALID_TYPE` — type fora do catálogo.
- `BUSINESS_INVALID_TRANSITION` — transição de status inválida.
- `BUSINESS_INVALID_TIME` — timestamp fora da janela.
- `BUSINESS_CONFLICTING_DUPLICATE` — mesma chave com payload diferente.
- `INTERNAL_ERROR` — erro interno do sistema (não expor detalhes ao cliente).

### 9.2 Severidade (V1)
- `LOW` — não impede funcionamento, mas registra (opcional).
- `MEDIUM` — evento inválido comum.
- `HIGH` — potencial abuso, conflito ou risco.
- `CRITICAL` — tentativa maliciosa óbvia ou falha séria.

---

## 10. Regras de auditoria (V1)

### 10.1 Quando auditar
- Toda alteração em dado TRUSTED gera um registro em `audit_log`.

### 10.2 Campos mínimos da auditoria
- entidade afetada (tabela e id)
- `before` (antes)
- `after` (depois)
- usuário responsável
- timestamp
- **motivo obrigatório** (texto curto)

### 10.3 Regra de segurança
- Apenas `admin` e `auditor` podem consultar auditoria completa.
- Logs não devem conter payload sensível completo.

---

## 11. Critérios de aceite (DoD) — Catálogos e Regras
Este documento está “pronto” quando:
- catálogos de `event_type` e `event_status` estão fechados e definidos.
- tabela de transições está definida.
- regras temporais estão definidas.
- política para duplicidade conflitante está definida.
- categorias de rejeição estão padronizadas.
- regra de auditoria está definida.
