# Arquitetura Geral do Sistema

> **Documento:** 06-arquitetura/01-arquitetura-geral.md  
> **Status:** Rascunho  
> **Criado em:** Maio/2026  
> **Atualizado em:** Maio/2026

---

## 1. Visão Geral da Arquitetura (C4 — Nível 1: Contexto)

```
                      ┌─────────────────────────────────┐
                      │                                 │
    [Colaborador]──▶ │   BrasilTerrenos                │──▶ [Power BI Service]
    [Gerente]    ──▶ │   Portal Corporativo            │──▶ [Azure Active Directory]
    [Admin]      ──▶ │                                 │──▶ [Serv. E-mail transacional]
                      │   Sistema de Governança         │
                      │   Analítica                     │
                      └─────────────────────────────────┘
```

---

## 2. Diagrama de Containers (C4 — Nível 2)

```
┌──────────────────────────────────────────────────────────────────────┐
│                      BrasilTerrenos Portal                           │
│                                                                      │
│  ┌────────────────┐   HTTPS/REST    ┌──────────────────────────┐     │
│  │   React SPA    │ ◀────────────▶ │    NestJS API (Backend)  │     │
│  │  (Frontend)    │  + JWT Bearer   │                          │     │
│  │  TypeScript    │                 │   Módulos:               │     │
│  │  Vite          │                 │   - AuthModule           │     │
│  │  React Query   │                 │   - UsersModule          │     │ 
│  │  Zustand       │                 │   - WorkspacesModule     │     │ 
│  │  powerbi-client│                 │   - ReportsModule        │     │ 
│  └────────────────┘                 │   - PermissionsModule    │     │ 
│                                     │   - ScheduleModule       │     │ 
│                                     │   - AuditModule          │     │ 
│                                     │   - PbiModule            │     │ 
│                                     │   - SettingsModule       │     │
│                                     └──────────────┬───────────┘     │
│                                                   │                  │
│                                     ┌─────────────┼──────────────┐   │
│                                     │             │              │   │
│                              ┌──────▼──┐    ┌────▼────┐  ┌──────▼┐   │
│                              │Postgres │    │  Redis  │  │ Queue │   │
│                              │  (Dados)│    │ (Cache/ │  │(Jobs) │   │
│                              │         │    │Sessions)│  │BullMQ │   │
│                              └─────────┘    └─────────┘  └───────┘   │
└──────────────────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────┼──────────────────────┐
              ▼                     ▼                       ▼
    [Azure Active Directory]  [Power BI REST API]  [SMTP / SendGrid]
```

---

## 3. Camadas da Aplicação

### 3.1 Frontend (React SPA)

**Responsabilidade:** Interface do usuário, navegação, exibição de dados e embed de relatórios PBI.

| Camada | Tecnologia | Responsabilidade |
|--------|-----------|-----------------|
| Framework | React 18 + TypeScript | Componentização, tipagem |
| Build | Vite | Bundling, HMR, otimização |
| Roteamento | React Router v6 | Navegação client-side |
| Estado servidor | TanStack Query (React Query) | Cache de dados, fetch, loading states |
| Estado global | Zustand | Autenticação, preferências do usuário |
| UI Components | Design system próprio (CSS vars do protótipo) | Componentes visuais padronizados |
| PBI Embed | powerbi-client (SDK oficial) | Renderização inline de relatórios |
| HTTP | Axios + interceptors | Chamadas à API; renovação automática de token |

**Regras do Frontend:**
- Sem lógica de negócio crítica no cliente
- Toda validação de segurança ocorre no backend (RBAC, permissões)
- Tokens armazenados apenas em memória React Query + `httpOnly cookies` para refresh
- Nunca armazenar access token em localStorage ou sessionStorage

---

### 3.2 Backend — API (NestJS)

**Responsabilidade:** Toda a lógica de negócio, autenticação, autorização, integração PBI e persistência.

**Estrutura de módulos NestJS:**

```
src/
├── modules/
│   ├── auth/
│   │   ├── auth.controller.ts       # POST /auth/login, /refresh, /logout
│   │   ├── auth.service.ts          # Lógica de autenticação
│   │   ├── strategies/              # local.strategy.ts, jwt.strategy.ts
│   │   └── guards/                  # jwt.guard.ts, roles.guard.ts
│   │
│   ├── users/
│   │   ├── users.controller.ts      # GET/POST/PUT/DELETE /users
│   │   ├── users.service.ts
│   │   └── dto/                     # CreateUserDto, UpdateUserDto
│   │
│   ├── workspaces/
│   ├── reports/
│   ├── permissions/
│   ├── schedule/
│   ├── exception-groups/
│   ├── audit/
│   │   ├── audit.service.ts         # log() — usado por todos os módulos
│   │   └── audit.controller.ts      # GET /audit/logs (filtros, paginação)
│   │
│   ├── pbi/
│   │   ├── pbi.service.ts           # Comunicação com Azure AD + PBI API
│   │   └── pbi.controller.ts        # GET /reports/:id/embed-token
│   │
│   └── settings/
│
├── common/
│   ├── guards/
│   │   ├── jwt-auth.guard.ts
│   │   └── roles.guard.ts
│   ├── decorators/
│   │   ├── current-user.decorator.ts
│   │   └── roles.decorator.ts
│   ├── interceptors/
│   │   ├── logging.interceptor.ts
│   │   └── transform.interceptor.ts
│   ├── filters/
│   │   └── http-exception.filter.ts
│   └── pipes/
│       └── validation.pipe.ts
│
├── database/
│   ├── migrations/
│   └── seeds/
│
└── config/
    ├── database.config.ts
    ├── jwt.config.ts
    └── pbi.config.ts
```

**Pipeline de uma requisição autenticada:**

```
Request
  → Helmet (headers de segurança)
  → CORS
  → Rate Limiter (ThrottlerGuard)
  → JwtAuthGuard (valida token, carrega usuário)
  → RolesGuard (verifica perfil)
  → PermissionsGuard (verifica permissão granular)
  → ValidationPipe (valida DTO)
  → Controller → Service → Repository
  → TransformInterceptor (normaliza resposta)
  → LoggingInterceptor (loga métricas)
Response
```

---

### 3.3 Banco de Dados (PostgreSQL)

- Banco relacional com suporte a JSONB (para campos de auditoria e overrides)
- Schema versionado com Prisma Migrate
- Conexão via pool (pg-pool) gerenciado pelo Prisma Client
- Tabela `audit_logs` com trigger que impede UPDATE e DELETE
- Índices nas colunas de busca mais frequentes

---

### 3.4 Cache (Redis)

| Uso | Chave | TTL |
|-----|-------|:---:|
| Refresh tokens (revogação) | `refresh:{userId}:{tokenId}` | 24h |
| Access token blocklist (logout) | `blocklist:{tokenJti}` | TTL = expiração restante |
| Cache de permissões por usuário | `perms:{userId}` | 5min |
| Cache de token de embed PBI | `pbi_token:{userId}:{reportId}` | 55min |
| Rate limiting | `rate:{ip}` | 1min |
| Sessão de MFA pendente | `mfa_pending:{userId}` | 5min |

---

### 3.5 Filas Assíncronas (BullMQ — v1.1+)

| Fila | Responsabilidade |
|------|-----------------|
| `email-notifications` | Envio de e-mails (recuperação de senha, alertas) |
| `audit-export` | Geração de arquivos CSV/XLSX de logs grandes |
| `pbi-sync` | Sincronização periódica de workspaces/relatórios do PBI Service |

---

## 4. Autenticação

### Fluxo de Tokens

```
Login bem-sucedido:
  access_token  → JWT RS256, 1h, retornado no body
  refresh_token → UUID v4 opaco, 24h, retornado em Set-Cookie httpOnly

A cada requisição:
  Authorization: Bearer <access_token>

Renovação:
  POST /auth/refresh (com cookie httpOnly)
  → Novo access_token + rotação do refresh_token

Logout:
  POST /auth/logout
  → Access token adicionado à blocklist Redis
  → Refresh token removido do Redis
  → Cookie limpo (Max-Age: 0)
```

### Estrutura do JWT (access_token)

```json
{
  "sub": "uuid-do-usuario",
  "email": "usuario@empresa.com",
  "role": "admin",
  "jti": "uuid-unico-do-token",
  "iat": 1700000000,
  "exp": 1700003600
}
```

---

## 5. API REST — Endpoints Principais

### Autenticação
```
POST   /api/v1/auth/login           → { accessToken, user }
POST   /api/v1/auth/refresh         → { accessToken }
POST   /api/v1/auth/logout          → 200
POST   /api/v1/auth/forgot-password → 200
POST   /api/v1/auth/reset-password  → 200
```

### Usuários
```
GET    /api/v1/users                → Listagem paginada com filtros
POST   /api/v1/users                → Criar usuário
GET    /api/v1/users/:id            → Detalhes
PUT    /api/v1/users/:id            → Atualizar
PATCH  /api/v1/users/:id/status     → Ativar/inativar/bloquear
DELETE /api/v1/users/:id            → Excluir (soft delete)
```

### Workspaces e Relatórios
```
GET    /api/v1/workspaces           → Listagem (filtrada por perfil)
POST   /api/v1/workspaces           → Criar
PUT    /api/v1/workspaces/:id       → Atualizar
GET    /api/v1/workspaces/:id/reports → Relatórios do workspace
POST   /api/v1/reports              → Criar relatório
GET    /api/v1/reports/:id/embed-token → Gerar token PBI (server-side)
```

### Permissões
```
GET    /api/v1/permissions/roles           → Permissões por perfil
PUT    /api/v1/permissions/roles           → Atualizar permissões de perfil
GET    /api/v1/permissions/users/:userId   → Overrides do usuário
PUT    /api/v1/permissions/users/:userId   → Definir override
```

### Auditoria
```
GET    /api/v1/audit/logs           → Listagem com filtros e paginação
GET    /api/v1/audit/logs/export    → Exportação CSV
```

### Expediente
```
GET    /api/v1/schedule             → Regras atuais
PUT    /api/v1/schedule             → Atualizar regras
GET    /api/v1/exception-groups     → Grupos de exceção
POST   /api/v1/exception-groups     → Criar grupo
```

### Configurações (Super Admin only)
```
GET    /api/v1/settings             → Configurações (sem secrets)
PUT    /api/v1/settings             → Atualizar configurações
POST   /api/v1/settings/pbi/test    → Testar conexão PBI
```

---

## 6. Variáveis de Ambiente

```env
# App
NODE_ENV=production
PORT=3001
FRONTEND_URL=https://portal.brasilterrenos.com.br

# Database
DATABASE_URL=postgresql://user:pass@host:5432/btportal

# Redis
REDIS_URL=redis://host:6379

# JWT
JWT_PRIVATE_KEY=<RS256 private key PEM>
JWT_PUBLIC_KEY=<RS256 public key PEM>
JWT_ACCESS_EXPIRES=3600          # 1 hora em segundos
JWT_REFRESH_EXPIRES=86400        # 24 horas em segundos

# Power BI
PBI_CLIENT_ID=<azure-client-id>
PBI_TENANT_ID=<azure-tenant-id>
PBI_CLIENT_SECRET=<azure-client-secret>  # usar cofre de segredos em produção

# Email (v1.1)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=<sendgrid-api-key>
EMAIL_FROM=noreply@brasilterrenos.com.br
```

---

## Histórico de Alterações

| Versão | Data | Autor | Descrição |
|--------|------|-------|-----------|
| 1.0 | Maio/2026 | — | Criação inicial do documento |