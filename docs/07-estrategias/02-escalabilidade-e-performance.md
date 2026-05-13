# Escalabilidade, Performance e Observabilidade

> **Documento:** 07-estrategias/02-escalabilidade-e-performance.md
> **Status:** Rascunho  
> **Criado em:** Maio/2026  
> **Atualizado em:** Maio/2026

---

## 1. Estratégia de Performance

### 1.1 Metas de Performance (SLOs)

| Métrica | Meta | Medição |
|---------|------|---------|
| Navegação entre páginas (exceto embed) | p95 < 1,5s | Lighthouse CI + RUM |
| First Contentful Paint (FCP) | < 2s (4G) | Lighthouse |
| Time to Interactive (TTI) | < 3s (4G) | Lighthouse |
| Geração de token de embed PBI | p95 < 3s | APM (OpenTelemetry) |
| Consulta de log de auditoria (com filtros) | p95 < 2s (100k registros) | Teste de carga |
| Requisições de API (GET simples) | p95 < 500ms | APM |
| Usuários simultâneos sem degradação | ≥ 200 | Teste de carga k6 |
| Throughput da API (leitura) | ≥ 500 req/s | Teste de carga |
| Bundle JavaScript (gzipped) | < 500KB | Vite build stats |

---

### 1.2 Performance no Frontend

#### Build e Bundle
```
Vite (bundler):
  - Code splitting automático por rota
  - Tree shaking de dependências não utilizadas
  - Lazy loading de módulos administrativos (importados apenas quando necessário)
  - Pré-carregamento de módulos mais acessados

Exemplo de lazy loading:
  const AdminUsers = lazy(() => import('./pages/admin/UsersPage'));
  const AuditLogs  = lazy(() => import('./pages/admin/AuditLogsPage'));
```

#### Cache de Dados (TanStack Query)
```typescript
// Relatórios de um workspace: cache de 5 minutos
useQuery({ queryKey: ['reports', workspaceId], staleTime: 5 * 60 * 1000 });

// Permissões do usuário: cache de 5 minutos (invalidado ao alterar permissões)
useQuery({ queryKey: ['permissions', userId], staleTime: 5 * 60 * 1000 });

// Dados de auditoria: sem cache (dados em tempo real)
useQuery({ queryKey: ['audit', filters], staleTime: 0 });
```

#### Otimizações Adicionais
- Virtualização de listas longas com `react-window` (logs de auditoria com 1000+ registros)
- Debounce de 300ms em campos de busca antes de disparar requisição
- Paginação server-side para todas as listagens (padrão: 20 itens/página)
- Imagens e ícones em SVG inline ou sprite para evitar múltiplas requisições
- Fontes carregadas com `font-display: swap` e subset latino

---

### 1.3 Performance no Backend

#### Cache com Redis
```
Estratégia de cache em camadas:

L1 — Cache em memória do processo (5s):
  → Configurações do sistema (não mudam frequentemente)

L2 — Redis (TTL variável):
  → Permissões do usuário: 5 minutos (invalidado via evento)
  → Workspaces disponíveis: 2 minutos
  → Tokens de embed PBI: 55 minutos
  → Schedule rules: 30 segundos

Cache invalidation:
  → Ao alterar permissões de um usuário: DEL perms:{userId}
  → Ao alterar schedule: DEL schedule:*
  → Ao alterar workspace: DEL workspaces:*
```

#### Pool de Conexões ao Banco
```
PostgreSQL connection pool:
  - Min connections: 5
  - Max connections: 20 (por instância do backend)
  - Idle timeout: 30s
  - Connection timeout: 3s
  - Query timeout: 10s (timeout para evitar queries travadas)
```

#### Índices no Banco de Dados
```sql
-- Consultas frequentes já indexadas:
audit_logs(timestamp DESC)      -- paginação por data (uso mais comum)
audit_logs(user_id)             -- filtro por usuário
audit_logs(event_type)          -- filtro por tipo
audit_logs(module)              -- filtro por módulo
users(email)                    -- login (UNIQUE implica index)
users(status)                   -- filtro por status
reports(workspace_id, status)   -- relatórios publicados por workspace
user_workspace_access(user_id)  -- acesso do usuário a workspaces

-- Index para ILIKE em buscas textuais (se necessário):
CREATE INDEX idx_reports_name_gin ON reports USING GIN(to_tsvector('portuguese', name));
```

---

## 2. Estratégia de Escalabilidade

### 2.1 Escala Vertical (Scale Up) — Caminho Inicial

Para o MVP com até 200 usuários simultâneos, o dimensionamento inicial é suficiente:

| Componente | Configuração inicial |
|------------|---------------------|
| Backend (NestJS) | 1 instância, 2 vCPU, 4GB RAM |
| PostgreSQL | 1 instância, 2 vCPU, 8GB RAM, 100GB SSD |
| Redis | 1 instância, 1 vCPU, 1GB RAM |

### 2.2 Escala Horizontal (Scale Out) — Crescimento

**Backend (Stateless — já preparado para horizontal scaling):**
```
→ Múltiplas instâncias do NestJS atrás de load balancer
→ Sessão/autenticação mantida no Redis (não em memória do processo)
→ Load balancer: NGINX, Azure App Gateway ou AWS ALB
→ Deploy via containers Docker (K8s ou Azure Container Apps)
```

**PostgreSQL (Read Replicas):**
```
→ Operações de leitura intensiva (ex: listagem de logs) roteadas para réplica
→ Escrita sempre na instância primária
→ Implementação: PostgreSQL streaming replication
→ ORM (Prisma) configurado com datasource separado para réplica
```

**Redis (Cluster Mode — se necessário):**
```
→ Redis Cluster com 3 shards para distribuição de carga de cache
→ Redis Sentinel para alta disponibilidade
→ Alternativa gerenciada: Azure Cache for Redis ou AWS ElastiCache
```

### 2.3 Limites por Tier

| Cenário | Usuários simultâneos | Arquitetura |
|---------|:--------------------:|-------------|
| MVP / Go-live | ≤ 200 | Single instance (backend + DB + Redis) |
| Crescimento médio | 200–500 | 2 instâncias backend, réplica read do DB |
| Crescimento alto | 500–2000 | 3–5 instâncias backend, DB cluster, Redis cluster |
| Enterprise | 2000+ | Kubernetes, auto-scaling, DB distribuído |

---

## Histórico de Alterações

| Versão | Data | Autor | Descrição |
|--------|------|-------|-----------|
| 1.0 | Maio/2026 | Vinicius Soares | Criação inicial do documento |