> **Nota do autor (contexto e foco)**  
> Eu criei este projeto para aprender como dados viram “dado confiável” em sistemas reais — saindo do cenário de planilhas e entrando em um pipeline controlado.  
> A **V1 (MVP)** foca em: **ingestão autenticada**, pipeline **RAW → TRUSTED → REJEIÇÕES**, **validação em camadas**, **deduplicação**, **consultas paginadas**, **logs estruturados** e **base para auditoria**.  
> Itens mais avançados ficam para **V2** (ex.: quarentena de eventos suspeitos, métricas mais completas, rate limit avançado e detecção de anomalias).

# Documento de Requisitos
## Plataforma de Monitoramento, Processamento e Segurança de Dados (RAW → TRUSTED → REJEIÇÕES) com API e Interface Visual

---

## 1. Visão do Produto

### Objetivo do sistema
Construir uma plataforma para **ingestão, validação, normalização, deduplicação, armazenamento relacional, auditoria e visualização** de dados operacionais vindos de múltiplas origens, garantindo **confiabilidade**, **segurança** e **rastreabilidade**.

### Problema central
Dados chegam de parceiros e sistemas com **inconsistências**, **duplicidade**, **formatos diferentes** e **risco de manipulação**, gerando falhas operacionais, relatórios incorretos e risco de segurança por ausência de trilha de evidências.

### Proposta de valor
- Transformar entradas brutas em dados confiáveis com governança.
- Registrar rejeições com motivos e evidências.
- Manter auditoria completa e eventos de segurança.
- Disponibilizar API padronizada e interface simples de acompanhamento.

---

## 2. Escopo

### 2.1 Escopo incluído (in-scope)
- Ingestão de eventos/dados via **API autenticada**.
- Pipeline com camadas:
  - **RAW** (evidência/payload original)
  - **TRUSTED** (dados normalizados e confiáveis)
  - **REJEIÇÕES** (erros categorizados e rastreáveis)
- Deduplicação / idempotência de ingestão.
- Consulta de dados confiáveis (**filtros + paginação**).
- Consulta de rejeições e indicadores de qualidade.
- Controle de acesso (**RBAC**) por perfil.
- Auditoria de alterações em dados confiáveis (antes/depois + motivo).
- Logs estruturados e eventos de segurança.
- Front-end simples para KPIs e consultas.

### 2.2 Fora do escopo (out-of-scope) nesta versão
- Processamento distribuído/streaming em tempo real com alta escala (Kafka etc.).
- Machine learning/IA em produção (pode entrar como evolução).
- Integração com múltiplos bancos/warehouses (foco em **1 banco relacional**).
- Gestão avançada de identidade corporativa (SSO/OAuth corporativo) — pode ser evolução.

---

## 3. Stakeholders e Perfis de Usuário

### Stakeholders
- **Operações:** precisa de status e acompanhamento diário.
- **Dados/BI:** precisa de qualidade e consistência.
- **Segurança/Auditoria:** precisa de rastreio, evidência e conformidade.
- **TI/Engenharia:** precisa de manutenção e escalabilidade.

### Perfis (RBAC)
- **Admin:** configura origens, gerencia usuários e permissões, vê tudo.
- **Analista:** consulta trusted/rejeições/indicadores, exporta relatórios (se permitido).
- **Operador:** consulta e acompanha indicadores básicos.
- **Auditor:** consulta auditoria e evidências (raw) para investigação.
- **Sistema Parceiro (Client API):** envia eventos/dados (ingestão).

---

## 4. Glossário e Conceitos
- **RAW:** registro bruto com payload original + metadados de ingestão; serve como evidência.
- **TRUSTED:** dado normalizado e validado, pronto para consumo e relatórios.
- **REJEIÇÃO:** falha de validação ou regra de negócio com motivo estruturado.
- **Idempotência:** reenvio do mesmo evento não gera duplicidade.
- **Deduplicação:** identificação de entradas repetidas por chave natural/hashes.
- **Auditoria:** histórico de alterações em dados confiáveis com antes/depois e responsável.

---

## 5. Requisitos Funcionais (RF)

### 5.1 Ingestão e processamento

**RF01 — Ingestão autenticada**  
O sistema deve receber dados via API apenas de origens autenticadas.

**RF02 — Validação de contrato (sintática)**  
O sistema deve validar: campos obrigatórios, tipos, tamanho máximo, formatos (data/hora etc.).

**RF03 — Registro RAW obrigatório**  
Toda ingestão deve gerar um registro RAW, mesmo quando rejeitada, contendo: payload original, origem, timestamp de recebimento, IP/metadados e hash do evento.

**RF04 — Normalização**  
O sistema deve normalizar formatos (datas, números, catálogos de status) para padrão interno.

**RF05 — Validação de negócio (semântica)**  
O sistema deve aplicar regras de domínio (ex.: status permitido, transição válida, consistência temporal).

**RF06 — Rejeições estruturadas**  
Quando houver erro, o sistema deve registrar rejeição(ões) com: categoria, campo, severidade, regra violada e mensagem técnica.

**RF07 — Deduplicação / idempotência**  
O sistema deve detectar eventos duplicados por chave definida (ex.: origem + id_externo + timestamp_evento ou hash). Reenvios devem retornar “duplicado” sem criar novo trusted.

**RF08 — Persistência TRUSTED**  
Eventos aprovados devem ser persistidos no conjunto TRUSTED com esquema relacional e indexável.

### 5.2 Consulta e visualização

**RF09 — Consulta TRUSTED com filtros e paginação**  
O sistema deve permitir filtrar por origem, intervalo de datas, status, id externo e paginar resultados.

**RF10 — Consulta de rejeições**  
O sistema deve listar rejeições por origem, período, categoria e severidade, com paginação.

**RF11 — Indicadores de qualidade e operação**  
O sistema deve expor KPIs: volume ingerido, taxa de rejeição, taxa de duplicidade e latência (média e percentis definidos).

**RF12 — Front-end simples**  
A interface deve exibir: KPIs, lista de últimos trusted, lista de últimas rejeições e tela de detalhe por registro.

### 5.3 Segurança, auditoria e governança

**RF13 — RBAC**  
O sistema deve restringir endpoints e dados por papel (admin/analista/operador/auditor).

**RF14 — Auditoria de alterações em TRUSTED**  
Alterações em dados confiáveis devem exigir motivo e gerar trilha de auditoria com antes/depois, usuário, timestamp e origem da ação.

**RF15 — Eventos de segurança**  
O sistema deve registrar eventos como: autenticação falha, acesso negado, payload anômalo, excesso de tentativas.

**RF16 — Logs estruturados com correlação**  
O sistema deve registrar logs com request_id, usuário/origem, endpoint, status, duração e erro (se houver).

---

## 6. Requisitos Não Funcionais (RNF)

**RNF01 — Segurança**
- Autenticação e autorização robustas.
- Segredos fora do código (variáveis de ambiente).
- Não vazar dados sensíveis em mensagens de erro.

**RNF02 — Performance**
- Consultas paginadas obrigatórias.
- Índices em campos críticos (origem, data, status, id externo, hash).
- Resposta de ingestão e consulta dentro de limites definidos pela aplicação (com meta de latência).

**RNF03 — Confiabilidade**
- Operações transacionais: evitar gravação parcial (ex.: trusted sem raw).
- Consistência referencial no banco.

**RNF04 — Disponibilidade**
- Entrada inválida não derruba o serviço.
- Timeouts e limites de payload.
- Rate limiting por origem (mínimo viável).

**RNF05 — Observabilidade**
- Logs estruturados.
- Métricas básicas para monitoramento.
- Healthcheck para serviços.

**RNF06 — Manutenibilidade**
- Arquitetura em camadas e módulos.
- Padrões consistentes.
- Testes cobrindo regras críticas.

**RNF07 — Portabilidade**
- Execução padronizada via Docker.
- Documentação completa de setup.

---

## 7. Regras de Negócio (RN)

**RN01 — Origem obrigatória e identificável**  
Todo evento deve conter identificação de origem (source) válida.

**RN02 — Identificador externo obrigatório (id_externo)**  
Todo evento deve possuir id externo único dentro de uma origem (para rastreio e idempotência).

**RN03 — Catálogo fechado para status/tipo**  
Campos críticos (ex.: status) só podem assumir valores do catálogo interno.

**RN04 — Consistência temporal**  
timestamp_evento não pode ser “muito no futuro” nem “muito no passado” (faixas definidas no projeto) sem ser marcado como suspeito ou rejeitado.

**RN05 — Transição de status válida**  
Mudanças de status devem respeitar uma tabela de transições permitidas.

**RN06 — Alterações em TRUSTED exigem justificativa**  
Qualquer update em dado confiável exige “motivo” e gera auditoria.

**RN07 — RAW é evidência (não apagar)**  
Registros RAW e auditoria não devem ser removidos na versão padrão (somente retenção/arquivamento controlado em evolução).

---

## 8. User Stories + Critérios de Aceitação

**US01 — Ingestão segura (Parceiro)**  
Como sistema parceiro, quero enviar eventos autenticados para processamento automático.  
**Aceitação:**
- Sem credencial válida → acesso negado e security_event registrado.
- Payload inválido → RAW gravado + REJEIÇÃO gravada + resposta com erros.
- Payload válido → RAW + TRUSTED gravados + resposta com identificadores.

**US02 — Idempotência (Parceiro)**  
Como parceiro, quero reenviar o mesmo evento sem gerar duplicidade.  
**Aceitação:**
- Reenvio do mesmo evento retorna status “duplicado”.
- Não cria novo TRUSTED; mantém rastreabilidade.

**US03 — Qualidade por origem (Analista)**  
Como analista, quero ver taxa de rejeição por origem e tipo de erro.  
**Aceitação:**
- Endpoint/Front mostra rejeição por origem e por categoria.
- Filtros por período.
- Valores batem com dados persistidos em REJEIÇÕES.

**US04 — Investigação (Auditor)**  
Como auditor, quero acessar a evidência RAW e histórico de mudanças do TRUSTED.  
**Aceitação:**
- Somente auditor/admin acessa RAW/auditoria.
- Tela/endpoint mostra antes/depois e usuário responsável.
- Toda alteração tem motivo.

**US05 — Operação (Operador)**  
Como operador, quero ver KPIs e últimos eventos para acompanhamento diário.  
**Aceitação:**
- KPIs atualizados.
- Listas paginadas.
- Sem travar com volume alto (paginação e limites).

---

## 9. Casos de Uso (descritos)

**UC01 — Receber e processar evento**
- **Ator:** Sistema parceiro  
- **Fluxo principal:** autentica → valida contrato → grava RAW → normaliza → valida negócio → deduplica → grava TRUSTED → retorna status “aceito”  
- **Fluxo alternativo A (erro contrato):** valida falha → grava RAW → grava REJEIÇÃO → retorna “rejeitado” + lista de erros  
- **Fluxo alternativo B (duplicado):** detecta duplicidade → grava RAW (ou vincula ao existente, conforme regra) → retorna “duplicado”

**UC02 — Consultar TRUSTED**
- **Ator:** Operador/Analista  
- **Fluxo:** autentica → aplica filtros → pagina → retorna lista + metadados de paginação

**UC03 — Consultar rejeições**
- **Ator:** Analista  
- **Fluxo:** autentica → filtra por origem/período/categoria → pagina → retorna lista

**UC04 — Alterar dado confiável (com auditoria)**
- **Ator:** Admin/Analista (se permitido)  
- **Fluxo:** autentica → valida permissão → exige motivo → atualiza TRUSTED → cria audit_log antes/depois → retorna sucesso

**UC05 — Auditoria e evidências**
- **Ator:** Auditor  
- **Fluxo:** autentica → consulta registro → vê histórico de alterações → acessa RAW relacionado

---

## 10. Critérios de Aceitação Globais (Definition of Done)
Um incremento é considerado “pronto” quando:
- Endpoint(s) documentados no Swagger.
- Persistência consistente (RAW sempre; TRUSTED apenas quando válido).
- Rejeições registradas com categoria/campo/regra.
- RBAC funcionando nos endpoints críticos.
- Logs estruturados com request_id.
- Testes cobrindo regras críticas (validação, deduplicação, auditoria).
- Execução local reproduzível (Docker) e README atualizado.

---

## 11. Riscos e Mitigações
- Crescimento do RAW → definir política de retenção/arquivamento (evolução).
- Dados maliciosos → limite de payload, validação rígida, rate limit, logs.
- Complexidade de regras de negócio → modularizar validações e documentar catálogos.
- Desempenho em consultas → índices e paginação obrigatória.

---

## 12. KPIs de Sucesso (qualidade do produto)
- Taxa de rejeição por origem (monitorável).
- Taxa de duplicidade detectada.
- Latência de ingestão/consulta (média e percentis).
- Cobertura de testes em módulos críticos.
- Auditoria completa sem “buracos” (toda alteração registrada).
