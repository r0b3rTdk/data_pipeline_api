# 10 — Fase 10: CI/CD (GitHub Actions)

Nesta fase, implementamos **Integração Contínua (CI)** com **GitHub Actions** para validar o projeto automaticamente a cada **push** e **pull request**.

---

## Objetivo

Garantir que o repositório **não quebre antes do merge**, automatizando:

- instalação de dependências
- lint do código (flake8)
- migrations do banco (Alembic)
- testes automatizados (Pytest)

---

## O que foi criado

### 1) Workflow do GitHub Actions

Arquivo principal do pipeline:

- `.github/workflows/ci.yml`

Esse workflow é executado automaticamente quando ocorrer:

- `push` para `main` ou `develop`
- `pull_request` para `main` ou `develop`

### 2) Configuração do lint

Para adequar o lint ao padrão do projeto e evitar falhas por regras puramente estéticas, foi criado:

- `.flake8`

---

## Como o pipeline funciona

Em cada execução, o GitHub Actions:

1. Faz **checkout** do repositório
2. Configura o **Python 3.12**
3. Instala dependências do `requirements.txt`
4. Executa **flake8** no diretório `app/`
5. Sobe um **PostgreSQL** como service container
6. Roda **migrations**: `alembic upgrade head`
7. Executa **testes**: `pytest -q`

---

## Variáveis de ambiente no CI

O workflow define variáveis para o ambiente de teste, incluindo:

- `APP_ENV=test`
- `DATABASE_URL` apontando para o Postgres do GitHub Actions
- `JWT_SECRET`, `JWT_ALG`, `JWT_EXPIRES_MIN`
- `PYTHONPATH=.`

> Observação: o projeto utiliza `psycopg` (v3), por isso o `DATABASE_URL` no CI usa `postgresql+psycopg://...`.

---

## Como validar a fase

1) Commit e push do workflow:

```bash
git add .github/workflows/ci.yml .flake8
git commit -m "feat: add CI pipeline with GitHub Actions"
git push
```

2) No GitHub:

- abra a aba **Actions**
- selecione o workflow
- verifique se o run ficou **verde (passed)**

---

## Resultado esperado

- Pipeline executa automaticamente em push/PR
- Lint, migrations e testes passam no ambiente do GitHub Actions
- O repositório ganha validação automática antes de merge

---

## Troubleshooting

Se algo falhar, consulte:

- `docs/99_troubleshooting_fase10.md`
