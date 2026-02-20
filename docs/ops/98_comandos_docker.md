# Comandos Docker — Projeto (API + DB)
## Guia rápido para rodar, entrar nos containers e debugar

> Objetivo: referência rápida para o dia a dia durante o desenvolvimento.

---

## 0) Ir para a pasta do projeto
Sempre rode os comandos na pasta onde está o `docker-compose.yml`:

```powershell
cd "E:\PROGRAMACAO\PROJETOS\PROJETO 01"
```

---

## 1) Ver status dos serviços
```powershell
docker compose ps
```

Você precisa ver `api` e `db` como **running**.

---

## 2) Subir o stack (API + DB)
```powershell
docker compose up -d --build
```

---

## 3) Entrar no container da API
### Opção padrão (mais comum)
```powershell
docker compose exec api sh
```

### Alternativa (se `sh` não existir)
```powershell
docker compose exec api bash
```

### Sair do container
Dentro do container:
```sh
exit
```

---

## 4) Rodar comando dentro da API sem “entrar” (atalho)
Exemplos:
```powershell
docker compose exec api alembic current
docker compose exec api alembic upgrade head
docker compose exec api python --version
```

---

## 5) Ver logs da API
### Últimas linhas
```powershell
docker compose logs -n 200 api
```

### Acompanhar ao vivo
```powershell
docker compose logs -f api
```

---

## 6) Entrar no Postgres (container `db`) com `psql`
```powershell
docker compose exec db psql -U appuser -d appdb
```

Comandos úteis no `psql`:
- listar tabelas:
```sql
\dt
```
- sair:
```sql
\q
```

---

## 7) Se aparecer “service api is not running”
1) Suba de novo:
```powershell
docker compose up -d --build
```

2) Se continuar caindo, veja o erro:
```powershell
docker compose logs -n 200 api
```

---

## 8) Parar tudo / reiniciar do zero
Parar e remover containers (mantém volume se você não passar `-v`):
```powershell
docker compose down
```

Subir novamente:
```powershell
docker compose up -d --build
```

> **Atenção:** se você usar `docker compose down -v`, você apaga o volume do Postgres (perde dados do banco).

---

## 9) Quando o `docker` não for reconhecido no terminal (PATH)
### Correção temporária (só nesta janela)
```powershell
$env:Path += ";C:\Program Files\Docker\Docker\resources\bin"
docker --version
```

### Correção permanente
```powershell
setx PATH "$env:PATH;C:\Program Files\Docker\Docker\resources\bin"
```

Depois feche e reabra VS Code/PowerShell.
