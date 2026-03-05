# Troubleshooting — Fase 8 (Deploy / Produção-Lite)

## Objetivo deste documento

Registrar problemas comuns encontrados durante o deploy da Fase 8 (Docker + Nginx + produção-lite) e as respectivas causas/soluções, com foco em execução em servidor Linux (Ubuntu/WSL).

---

## 1) `cp .env.prod.example .env.prod` falha com `No such file or directory`

### Sintoma
```bash
cp: cannot stat '.env.prod.example': No such file or directory
```

### Causa
A pasta de deploy foi criada, mas o repositório ainda **não foi clonado** nela.  
Ou seja, existe `/opt/projeto01`, mas sem os arquivos do projeto.

### Solução
Clonar o repositório para a pasta correta:

```bash
git clone https://github.com/r0b3rTdk/data_pipeline_api /opt/projeto01
cd /opt/projeto01
```

Se já existir `.env.prod` criado manualmente na pasta vazia, mover temporariamente e depois restaurar:

```bash
mv /opt/projeto01/.env.prod ~/
git clone https://github.com/r0b3rTdk/data_pipeline_api /opt/projeto01
mv ~/.env.prod /opt/projeto01/.env.prod
```

---

## 2) `docker-compose.prod.yml` não encontrado ao subir o ambiente

### Sintoma
Mensagens como:
- arquivo `docker-compose.prod.yml` não encontrado
- erro ao abrir `.../docker-compose.prod.yml`

### Causa
Mesmo cenário do item anterior: a pasta não continha o repositório clonado.

### Solução
Confirmar conteúdo da pasta e clonar o projeto:

```bash
ls -la /opt/projeto01
git clone https://github.com/r0b3rTdk/data_pipeline_api /opt/projeto01
```

---

## 3) Nginx em loop de restart (`Restarting`) logo após subir

### Sintoma
No `docker compose ps`, o serviço `nginx` aparece reiniciando continuamente:
- `Restarting (1) ...`

### Diagnóstico (logs)
```bash
docker logs --tail 80 projeto01_nginx
```

Erro observado:
```text
cannot load certificate "/etc/letsencrypt/live/SEU_DOMINIO/fullchain.pem": No such file or directory
```

### Causa
O bloco HTTPS (`listen 443 ssl`) estava ativo no `deploy/nginx/default.conf`, mas:
- ainda não havia domínio configurado
- os certificados do Let's Encrypt ainda não existiam

### Solução (produção-lite)
Desativar temporariamente o bloco HTTPS no Nginx e manter apenas HTTP (porta 80).

> **Importante:** Nginx não aceita comentário em bloco estilo `/* ... */`.  
> Use `#` em cada linha ou remova o bloco temporariamente.

Depois reiniciar o serviço:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d nginx
```

---

## 4) Tentativa de comentar Nginx com `/* ... */` (erro de sintaxe)

### Sintoma
Nginx continua quebrando após “comentar” o bloco HTTPS.

### Causa
Foi usado comentário de linguagem C/JS:
```nginx
/*
server {
  ...
}
*/
```

Esse formato **não é válido** em Nginx.

### Solução
Comentar linha a linha com `#`:

```nginx
# server {
#   listen 443 ssl http2;
#   ...
# }
```

---

## 5) Warning do Docker Compose: `POSTGRES_PASSWORD` não setado

### Sintoma
Ao rodar comandos `docker compose`:
```text
The "POSTGRES_PASSWORD" variable is not set. Defaulting to a blank string.
```

### Causa
O warning ocorre na fase de **interpolação do arquivo compose**, antes de o `env_file` do serviço ser considerado.  
Mesmo com `--env-file .env.prod`, o Compose pode emitir warning se a variável não estiver disponível no `.env` padrão ou no ambiente de shell.

### Situação observada
Apesar do warning:
- `db` subiu e ficou healthy
- `api` subiu e ficou healthy
- ambiente funcionou normalmente

### Mitigação aplicada
Criar `.env` local no servidor (não versionado), copiando o `.env.prod`:

```bash
cp .env.prod .env
```

Isso eliminou o warning nos comandos subsequentes.

### Observação adicional
Também foi adicionado `env_file: [.env.prod]` no serviço `db`, o que é útil para runtime, mas não necessariamente elimina warning de interpolação do Compose.

---

## 6) Login retorna `401 invalid_credentials` após `Seed OK`

### Sintoma
```json
{"detail":"invalid_credentials","code":"HTTP_ERROR", ...}
```

### Causa
Foi testado login com senha diferente da configurada em `SEED_ADMIN_PASSWORD` no `.env.prod`.

Exemplo de erro de teste:
- seed criou admin com senha forte definida no `.env.prod`
- teste foi feito com `admin123`

### Solução
Usar a senha real do seed configurada no `.env.prod`:

```bash
curl -i -X POST http://localhost/api/v1/auth/login   -H "Content-Type: application/json"   -d '{"username":"admin","password":"SENHA_REAL_DO_SEED"}'
```

---

## 7) `curl` falha logo após `docker compose restart` com `connection reset`

### Sintoma
```bash
curl: (56) Recv failure: Connection reset by peer
```

### Causa
O request foi executado **imediatamente após** `docker compose restart`, enquanto:
- `db` ainda estava em `health: starting`
- `api` ainda iniciando
- `nginx` reiniciando

### Solução
Aguardar alguns segundos e testar novamente:

```bash
docker compose -f docker-compose.prod.yml ps
curl -i http://localhost/api/v1/health
```

Verificar se `db` e `api` estão `healthy` antes de concluir que houve falha real.

---

## 8) `.env.prod` inconsistente (senha do DB diferente em `DATABASE_URL`)

### Sintoma
Erros de conexão com banco (API pode não subir corretamente, ou falhar ao acessar DB).

### Causa
`POSTGRES_PASSWORD` e a senha dentro de `DATABASE_URL` estavam diferentes.

Exemplo inconsistente:
```env
POSTGRES_PASSWORD=MINHA_SENHA
DATABASE_URL=postgresql+psycopg://appuser:OUTRA_SENHA@db:5432/appdb
```

### Solução
Usar **a mesma senha** nos dois campos:

```env
POSTGRES_PASSWORD=MINHA_SENHA
DATABASE_URL=postgresql+psycopg://appuser:MINHA_SENHA@db:5432/appdb
```

---

## 9) Valores fracos/placeholders em `.env.prod` (risco de produção)

### Sintoma
- `JWT_SECRET=change-me-in-production`
- `CORS_ORIGINS=r0b3rT` (valor inválido)
- `SEED_ADMIN_EMAIL` inválido
- API key e senhas muito curtas

### Causa
Uso de valores de teste/local em ambiente de deploy.

### Solução
Ajustar para valores válidos e fortes:
- `APP_ENV=prod`
- `JWT_SECRET` forte (32+ chars)
- `CORS_ORIGINS` com URL válida
- emails válidos
- senhas e API keys fortes

---

## 10) Nginx com 443 publicado, mas HTTPS desativado (situação temporária)

### Sintoma
No `docker compose ps`, porta 443 aparece publicada:
- `0.0.0.0:443->443/tcp`

Mesmo com bloco HTTPS desativado no Nginx.

### Causa
A publicação de porta está no `docker-compose.prod.yml`, mas o bloco TLS foi desativado no `default.conf` até gerar certificados.

### Impacto
Não bloqueia o deploy em HTTP. É apenas uma configuração temporária.

### Opções
- **Manter assim temporariamente** (aceitável em produção-lite)
- Ou remover `443:443` do compose até ativar Certbot/HTTPS

---

## 11) Arquivo errado editado por engano (`nano docker-compose.prod`)

### Sintoma
Comando:
```bash
nano docker-compose.prod
```

### Causa
Nome digitado sem extensão `.yml`, podendo criar arquivo novo acidentalmente.

### Solução
Editar sempre o arquivo correto:
```bash
nano docker-compose.prod.yml
```

E conferir com:
```bash
ls -la | grep docker-compose
```

---

## 12) Como diagnosticar rapidamente o estado do deploy

### Checklist de comandos úteis

#### Status dos serviços
```bash
docker compose -f docker-compose.prod.yml ps
```

#### Logs do Nginx
```bash
docker compose -f docker-compose.prod.yml logs -n 200 nginx
```

#### Logs da API
```bash
docker compose -f docker-compose.prod.yml logs -n 200 api
```

#### Logs do DB
```bash
docker compose -f docker-compose.prod.yml logs -n 200 db
```

#### Health endpoint via Nginx
```bash
curl -i http://localhost/api/v1/health
```

---

## 13) Situação de HTTPS nesta fase (adiado conscientemente)

### Status
HTTPS **não foi validado** nesta fase porque o projeto ainda não possui domínio real apontando para IP público.

### Estrutura já preparada
- Nginx com bloco HTTPS planejado
- caminho de certificados Let's Encrypt previsto
- fluxo de ativação documentado para etapa futura

### Próximo passo futuro (quando houver domínio)
1. Configurar DNS (registro A)
2. Ajustar `server_name`
3. Gerar certificado com Certbot
4. Reativar bloco HTTPS
5. Validar `https://SEU_DOMINIO/api/v1/health`

---

## Resultado final da troubleshooting da Fase 8

Os principais problemas de deploy foram resolvidos com sucesso, incluindo:
- pasta sem clone do projeto
- Nginx quebrando por certificado inexistente
- warning de interpolação do Compose
- erros de teste por credenciais incorretas
- falha temporária de curl durante restart

O ambiente ficou estável e funcional em modo **produção-lite (HTTP)**.
