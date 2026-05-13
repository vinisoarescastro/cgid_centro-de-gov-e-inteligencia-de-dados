# Manutenção e Observabilidade

> **Documento:** 07-estrategias/03-manutencao-e-observabilidade.md 
> **Status:** Rascunho  
> **Criado em:** Maio/2026  
> **Atualizado em:** Maio/2026

---

## 1. Estratégia de Manutenção

### 1.1 Gerenciamento de Dependências
```
Frequência de atualização:
  - Patches de segurança: imediato (< 48h após publicação do CVE)
  - Minor updates: mensal
  - Major updates: trimestral com planejamento de migração

Ferramentas:
  - Dependabot (GitHub): alertas automáticos de vulnerabilidades
  - npm audit --audit-level=high: bloqueia build se houver vulnerabilidade alta
  - renovate.json: PRs automáticos de atualização de dependências
```

### 1.2 Versionamento de Banco de Dados
```
Prisma Migrate:
  - Migration gerada automaticamente pelo Prisma
  - Revisão obrigatória de toda migration antes de aplicar em produção
  - Cada migration com script de rollback documentado
  - Migrations aplicadas automaticamente no start do container em staging
  - Migrations em produção aplicadas manualmente com aprovação

Nomeclatura:
  20260501_001_create_users_table
  20260501_002_create_workspaces_table
  20260515_001_add_mfa_columns_to_users
```

### 1.3 Janelas de Manutenção
```
Manutenção programada:
  - Janela: Sábados, 02h–04h (fora do expediente de todos os fusos)
  - Notificação: e-mail para admins 48h antes
  - Manutenção exibida via banner no portal (24h antes)
  - Máximo de 2h de downtime por janela
```

---

## 2. Estratégia de Observabilidade

A observabilidade segue os **três pilares**: Logs, Métricas e Traces.

### 2.1 Logs Estruturados

```typescript
// Todos os logs em formato JSON estruturado
// Biblioteca: pino (alta performance, baixo overhead)

logger.info({
  requestId: uuid,
  userId: user.id,
  method: 'POST',
  path: '/api/v1/auth/login',
  statusCode: 200,
  durationMs: 145,
  ip: '192.168.1.1',
});

// Níveis:
// error   → Erros de aplicação, exceções não tratadas
// warn    → Situações anômalas mas não fatais
// info    → Eventos relevantes (login, criação de usuário, acesso PBI)
// debug   → Apenas em desenvolvimento e staging
```

**Coleta de logs em produção:**
- Logs enviados para **stdout** (padrão para containers)
- Coletados por **Fluent Bit** (sidecar no container)
- Enviados para **Azure Monitor Logs** ou **Datadog**
- Retenção: 90 dias online + 1 ano em storage frio

### 2.2 Métricas

```
Biblioteca: @opentelemetry/sdk-node + prom-client

Métricas de aplicação expostas em /metrics (Prometheus scrape):

http_requests_total{method, route, status_code}   — Total de requisições
http_request_duration_seconds{method, route}      — Latência (histograma)
pbi_token_generation_duration_seconds             — Tempo de geração de token PBI
active_sessions_total                             — Sessões ativas no Redis
login_attempts_total{result}                      — Tentativas de login (success/fail)
blocked_users_total                               — Total de usuários bloqueados
audit_log_entries_total{event_type}               — Volume de eventos por tipo

Infraestrutura (coletadas pelo provedor cloud):
  CPU, Memória, Disco, Conexões de rede
  Conexões do pool PostgreSQL
  Hit rate do cache Redis
  Latência de resposta do Power BI API
```

**Stack de visualização:**
- **Prometheus** → coleta e armazenamento de métricas
- **Grafana** → dashboards e alertas visuais
- Alternativa gerenciada: **Azure Monitor + Application Insights**

### 2.3 Traces (Distributed Tracing)

```typescript
// @opentelemetry/sdk-node com auto-instrumentação para:
// - HTTP (incoming requests)
// - PostgreSQL (queries via Prisma)
// - Redis (operações de cache)
// - HTTP outgoing (chamadas Azure AD e PBI API)

// Trace ID propagado em todos os logs:
logger.info({ traceId: span.spanContext().traceId, ... });

// Backend para traces:
//   Jaeger (self-hosted) ou Azure Application Insights
```

### 2.4 Alertas

| Alerta | Condição | Canal | Severidade |
|--------|----------|-------|-----------|
| Alta taxa de erros 5xx | > 1% das requisições em 5min | Slack + e-mail | 🔴 Crítico |
| Latência elevada | p95 > 3s por 5min | Slack | 🟡 Alto |
| Muitas tentativas de login | > 50 falhas/min por IP | Slack + e-mail | 🔴 Crítico |
| Usuários bloqueados em massa | > 5 bloqueios em 10min | Slack + e-mail | 🔴 Crítico |
| Pool de conexões esgotado | > 90% do max pool | Slack | 🟡 Alto |
| Disco do banco > 80% | — | Slack | 🟡 Alto |
| PBI API indisponível | 3 falhas consecutivas | Slack | 🟡 Alto |
| Certificado TLS expirando | < 30 dias para expirar | Slack + e-mail | 🟡 Alto |

### 2.5 Health Checks

```
GET /health               → Status geral (200 OK ou 503)
GET /health/live          → Liveness (o processo está vivo?)
GET /health/ready         → Readiness (pode receber tráfego? DB + Redis conectados?)

Exemplo de resposta:
{
  "status": "ok",
  "checks": {
    "database": "up",
    "redis": "up",
    "pbiService": "up"
  },
  "timestamp": "2026-05-01T10:00:00Z",
  "version": "1.2.3"
}
```

### 2.6 Dashboard de Observabilidade Sugerido (Grafana)

| Painel | Métricas |
|--------|---------|
| Visão Geral | Req/s, latência p50/p95/p99, taxa de erros, usuários ativos |
| Autenticação | Logins/min (success/fail), bloqueios, tentativas por IP |
| Power BI | Tempo de geração de token, hits de cache, erros de integração |
| Banco de Dados | Conexões ativas, query duration, slow queries |
| Redis | Hit rate, memória usada, operações/s |
| Segurança | Eventos críticos no log de auditoria, acessos negados por expediente |

---

## Histórico de Alterações

| Versão | Data | Autor | Descrição |
|--------|------|-------|-----------|
| 1.0 | Maio/2026 | Vinicius Soares | Criação inicial do documento |