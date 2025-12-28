# MyLib Back (reorganizado) — FastAPI + SQLite(FTS5) + JWT + Permissão por Diretório Raiz

Este projeto é uma reorganização do seu **MyLib-Back** para:
- Estrutura de pastas escalável (`app/` com camadas)
- **Autenticação JWT**
- **Controle de acesso por diretório raiz** (`root_id`) com níveis `reader | editor | admin`
- Download **seguro** por `file_id` (evita `path` arbitrário)

---

## Estrutura de pastas

```
MyLib-Back-reorg/
  app/
    main.py
    api/
      router.py
      routers/
        auth.py
        pastas.py
        scan.py
        indexacao.py
        busca.py
        arquivos.py
        download.py
    core/
      config.py
      security.py
      deps.py
    db/
      database.py
      init_db.py
    models/
      models.py
  requirements.txt
  .env (opcional)
```

---

## Requisitos

- Python 3.11+ (recomendado)
- SQLite com suporte a **FTS5** (normalmente já vem no Python do Windows/Linux)

---

## Instalação (Windows / PowerShell)

```powershell
cd MyLib-Back-reorg
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Rodar o servidor:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Healthcheck:

- `GET /health`

---

## Configuração (.env)

Crie um arquivo `.env` na raiz (opcional):

```env
APP_NAME=MyLib Back
ENV=dev
DATABASE_URL=sqlite:///./mylib.db

JWT_SECRET_KEY=COLOQUE_UM_SEGREDO_FORTE_AQUI
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=720

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
```

> Na inicialização, o projeto cria (se não existir) o usuário `ADMIN_USERNAME` como **superuser**.

---

## Autenticação JWT

### Login

`POST /auth/login` (form urlencoded)

Campos:
- `username`
- `password`

Exemplo com curl:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Resposta:

```json
{ "access_token": "....", "token_type": "bearer" }
```

Use nas chamadas:

`Authorization: Bearer <token>`

### Usuário atual

`GET /auth/me`

---

## Controle de acesso por diretório raiz (root_id)

Tabela: `root_folder_permissions`

Níveis:
- `reader`: pode listar e pesquisar / baixar
- `editor`: pode fazer scan/indexação
- `admin`: reservado para casos especiais por root (você ainda tem o `superuser` global)

Regras:
- `superuser` acessa tudo
- Usuário comum precisa ter linha em `root_folder_permissions` para acessar aquele `root_id`

### Conceder permissão (Admin)

`POST /auth/roots/{root_id}/permissions`

Body:

```json
{ "user_id": 2, "access_level": "reader" }
```

---

## Endpoints principais

### Pastas raiz (somente superuser)

- `GET /roots`
- `POST /roots`
- `PUT /roots/{root_id}`
- `DELETE /roots/{root_id}`

### Scan (exige permissão `editor` no root)

- `POST /scan/{root_id}?ext=pdf,docx,xlsx`

### Indexação (exige `editor` no root)

Mantém o comportamento do seu projeto (extrai texto e popula `docs` FTS5 + `map`).

### Busca (exige login; se filtrar por root_id, valida permissão)

- `GET /search?q=...`
- `GET /search?q=...&root_id=1`

A resposta já retorna:
- `download_url` no formato `/download/{file_id}`

### Download seguro (exige login + permissão no root do arquivo)

- `GET /download/{file_id}`

### Metadados de arquivos

- `GET /files?root_id=1`
- `GET /files/{file_id}`

---

## Migração do seu projeto atual

O seu projeto antigo tinha arquivos soltos na raiz:
- `api_*.py`, `database.py`, `main.py`

Nesta versão:
- Routers foram movidos para `app/api/routers/*.py`
- DB/Models foram centralizados em `app/db` e `app/models`
- O entrypoint virou `app/main.py`

Se você tiver o front antigo apontando para `/download?path=...`, **atualize** para usar o `download_url` retornado pela busca, que agora é `/download/{file_id}`.

---

## Próximos passos que eu sugiro (curto e prático)

1) **Amarrar indexação/busca por root_id** também no endpoint de index (se houver variações no seu `api_indexacao.py`).
2) Criar endpoints de administração de usuários (já existe `POST /auth/users` para superuser).
3) Se você for publicar fora da rede interna: trocar `allow_origins=["*"]` por lista de origins do seu front Node.

---
