# CGID - Centro de Governança e Inteligência de Dados

Portal web para centralizar relatórios **Power BI Embedded** com controle de permissões, auditoria e gestão de acesso corporativo.

---

## O que é este projeto?

O CGID é um portal interno onde usuários da empresa podem visualizar relatórios do Power BI de acordo com suas permissões. Administradores controlam quem vê o quê, e todas as ações ficam registradas em log de auditoria.

---

## Stack atual

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 19 + JavaScript + Vite 8 |
| Roteamento | React Router v7 |
| Backend | Python 3.12 + FastAPI |
| Banco de dados | SQLite (desenvolvimento) → SQL Server (produção) |
| ORM | SQLAlchemy 2.0 |
| Senhas | passlib + bcrypt |
| Power BI | powerbi-client SDK (Microsoft) — v1.1 |

---

## Estrutura do repositório

```
cgid/
│
├── backend/
│   ├── main.py          ← servidor FastAPI (começa aqui)
│   ├── database.py      ← conexão SQLite + sessão SQLAlchemy
│   ├── models.py        ← 14 tabelas do banco (SQLAlchemy ORM)
│   ├── schemas.py       ← validação de entrada/saída (Pydantic)
│   ├── seed.py          ← popular banco com dados iniciais
│   └── cgid.db          ← banco SQLite (gerado automaticamente)
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx    ← tela de login
│   │   │   ├── HomePage.jsx     ← home (dashboard)
│   │   │   └── UsersPage.jsx    ← gestão de usuários
│   │   ├── styles/
│   │   │   ├── global.css       ← tokens, reset, tipografia
│   │   │   ├── login.css        ← estilos da tela de login
│   │   │   ├── home.css         ← estilos do app shell e home
│   │   │   └── users.css        ← estilos da gestão de usuários
│   │   ├── routes/
│   │   │   └── AppRoutes.jsx    ← definição de rotas + rota protegida
│   │   ├── components/
│   │   │   └── Avatar.jsx       ← avatar com foto ou iniciais
│   │   ├── assets/              ← logos e imagens
│   │   ├── App.jsx              ← monta BrowserRouter + AppRoutes
│   │   └── main.jsx             ← inicializa o React
│   ├── package.json
│   └── vite.config.js
│
└── docs/                ← documentação técnica e de produto
    └── prototipo/       ← protótipo visual (portal_v4_8.html)
```

---

## Pré-requisitos

| Software | Versão | Link |
|---|---|---|
| Python | 3.12+ | [python.org](https://python.org/downloads) |
| Node.js | 20 LTS | [nodejs.org](https://nodejs.org) |

> Não é necessário SQL Server nem ODBC Driver para rodar em desenvolvimento. O banco SQLite é criado automaticamente.

---

## Como rodar localmente

### 1. Instale as dependências do backend

```powershell
cd backend
pip install fastapi uvicorn sqlalchemy passlib bcrypt pydantic
```

### 2. Crie e popule o banco de dados

```powershell
python seed.py
```

Isso cria o arquivo `cgid.db` com as 14 tabelas e os dados iniciais.

### 3. Inicie o backend

```powershell
uvicorn main:app --reload
```

### 4. Inicie o frontend

Abra um segundo terminal:

```powershell
cd frontend
npm install
npm run dev
```

### 5. Acesse a aplicação

| URL | O que abre |
|---|---|
| http://localhost:5173 | Aplicação React |
| http://localhost:8000/docs | Documentação interativa da API (Swagger) |

---

## Credenciais de acesso (desenvolvimento)

| E-mail | Senha | Perfil |
|---|---|---|
| admin@cgid.com | Admin@2025 | Super Administrador |
| carlos@cgid.com | Carlos@123 | Gerente |
| mariana@cgid.com | Mariana@123 | Operador |
| visitante@cgid.com | Visitante@123 | Visitante |

---

## Regras de negócio importantes

| Regra | Detalhe |
|---|---|
| Senha padrão | Novos usuários recebem `Mudar@123` se nenhuma senha for informada |
| Reset de senha | Admin pode redefinir a senha de qualquer usuário para `Mudar@123` |
| Bloqueio automático | Conta bloqueada após 5 tentativas de login incorretas |
| Acesso admin | Super Admin e Admin têm acesso automático a todos os workspaces com nível total |
| Acesso por perfil | Gerente, Operador e Visitante precisam ter workspaces vinculados manualmente |
| Último acesso | Registrado automaticamente a cada login bem-sucedido |

---

## Páginas disponíveis

| Rota | Página | Descrição |
|---|---|---|
| `/login` | LoginPage | Tela de autenticação |
| `/` | HomePage | Dashboard com KPIs, eventos e workspaces |
| `/usuarios` | UsersPage | Gestão completa de usuários (CRUD + acessos) |

---

## Endpoints disponíveis

### Autenticação
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/` | Health check |
| POST | `/login` | Autenticação — retorna dados do usuário e registra último acesso |

### Dashboard
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/dashboard/kpis` | KPIs: usuários ativos, bloqueados, acessos negados, workspaces |
| GET | `/dashboard/eventos` | Últimos 5 eventos do log de auditoria |
| GET | `/dashboard/workspaces` | Workspaces com contagem de relatórios e acessos |

### Gestão de Usuários
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/usuarios` | Lista usuários com filtros por status, perfil e busca |
| POST | `/usuarios` | Cria usuário (senha padrão `Mudar@123` se não informada) |
| PUT | `/usuarios/{id}` | Atualiza dados do usuário |
| DELETE | `/usuarios/{id}` | Exclui usuário |
| POST | `/usuarios/{id}/resetar-senha` | Redefine senha para `Mudar@123` |

### Workspaces e Acessos
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/workspaces` | Lista workspaces ativos |
| GET | `/usuarios/{id}/acessos` | Acessos de um usuário por workspace |
| PUT | `/usuarios/{id}/acessos` | Salva acessos (auto-total para admin/super_admin) |

---

## Banco de dados

O banco possui **14 tabelas** conforme a documentação de modelagem:

| Tabela | Conteúdo |
|---|---|
| `usuarios` | Contas de acesso ao portal |
| `sessoes_autenticacao` | Sessões e refresh tokens |
| `espacos_trabalho` | Workspaces (agrupamentos de relatórios) |
| `relatorios` | Relatórios Power BI cadastrados |
| `acessos_workspace` | Permissão de usuário por workspace |
| `acessos_relatorio` | Permissão de usuário por relatório |
| `permissoes_perfil` | Matriz de permissões por perfil (RBAC) |
| `sobrescritas_permissao` | Exceções de permissão por usuário |
| `regras_expediente` | Horários de acesso permitidos por dia |
| `grupos_excecao` | Grupos com acesso fora do expediente |
| `membros_grupo_excecao` | Membros dos grupos de exceção |
| `favoritos` | Relatórios favoritos por usuário |
| `logs_auditoria` | Registro imutável de todas as ações |
| `configuracoes_sistema` | Parâmetros globais do sistema |

---

## Documentação

Consulte a pasta [`docs/`](docs/README.md) para requisitos, arquitetura, modelagem e roadmap.

O protótipo visual está em [`docs/prototipo/portal_v4_8.html`](docs/prototipo/portal_v4_8.html).
