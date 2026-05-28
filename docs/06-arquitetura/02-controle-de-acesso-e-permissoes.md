# Controle de Acesso e Permissões

> **Documento:** 06-arquitetura/02-controle-de-acesso-e-permissoes.md  
> **Status:** Rascunho  
> **Criado em:** Maio/2026  
> **Atualizado em:** Maio/2026

---

## 1. Modelo de Controle de Acesso

O sistema adota um modelo **RBAC (Role-Based Access Control)** com extensão de **overrides individuais**:

```
Perfil (role)
  └── Permissões padrão (role_permissions)
        └── Override por usuário (user_permission_overrides) ← Sobrepõe
              └── Permissão final aplicada ao usuário
```

**Regra de precedência:** Permissão individual (override) sobrepõe permissão de perfil. Se o campo do override for `NULL`, herda do perfil. Se for `true` ou `false`, sobrepõe.

---

## 2. Hierarquia de Perfis

```
Super Admin   (nível 5) → Acesso irrestrito, incluindo configurações do sistema
    ↓
Admin         (nível 4) → Gestão de usuários, permissões, workspaces (não pode alterar Super Admin)
    ↓
Gerente       (nível 3) → Visualização de relatórios do(s) seu(s) workspace(s) + KPIs da equipe
    ↓
Operador      (nível 2) → Visualização dos relatórios explicitamente liberados para ele
    ↓
Visitante     (nível 1) → Acesso read-only temporário, apenas relatórios autorizados
```

**Regra:** Um perfil não pode alterar permissões de outro perfil de nível igual ou superior.

---

## 3. Matriz de Permissões por Módulo e Perfil

### Legenda
- ✅ Permitido por padrão
- ❌ Negado
- ⚠️ Parcial (somente próprio registro ou contexto limitado)
- 🔧 Configurável por Admin

### 3.1 Gestão de Acesso (Módulos Administrativos)

| Módulo | Ação | Super Admin | Admin | Gerente | Operador | Visitante |
|--------|------|:-----------:|:-----:|:-------:|:--------:|:---------:|
| **Usuários** | Visualizar | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Criar | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Editar | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Bloquear/Desbloquear | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Excluir | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Permissões** | Visualizar | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Editar (por perfil) | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Editar (Super Admin) | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Workspaces (admin)** | CRUD | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Grupos de Exceção** | CRUD | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Expediente** | Visualizar | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Editar | ✅ | ✅ | ❌ | ❌ | ❌ |

### 3.2 Auditoria e Segurança

| Módulo | Ação | Super Admin | Admin | Gerente | Operador | Visitante |
|--------|------|:-----------:|:-----:|:-------:|:--------:|:---------:|
| **Logs de Auditoria** | Visualizar (todos) | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Visualizar (próprios) | ✅ | ✅ | ✅ | ✅ | ✅ |
| | Exportar | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Segurança** | Visualizar checklist | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Ver eventos suspeitos | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Configurações** | Visualizar | ✅ | ❌ | ❌ | ❌ | ❌ |
| | Editar | ✅ | ❌ | ❌ | ❌ | ❌ |

### 3.3 Consumo (Relatórios e Workspaces)

| Módulo | Ação | Super Admin | Admin | Gerente | Operador | Visitante |
|--------|------|:-----------:|:-----:|:-------:|:--------:|:---------:|
| **Home/Dashboard** | Visualizar (admin view) | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Visualizar (user view) | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Workspaces** | Ver todos | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| | Ver apenas autorizados | — | — | ✅ | ✅ | ✅ |
| **Relatórios** | Ver publicados autorizados | ✅ | ✅ | ✅ | ✅ | ✅ |
| | Ver rascunhos | ✅ | ✅ | ✅ | ❌ | ❌ |
| | Criar | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Editar | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Excluir | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Favoritos** | Gerenciar próprios | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Painel Gerencial** | Visualizar | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## 4. Permissões de Acesso Power BI

O acesso a relatórios PBI tem uma camada adicional além do RBAC dos módulos:

| Nível | Descrição | Como configurar |
|-------|-----------|----------------|
| `total` | Acesso a todos os relatórios do workspace | Na tabela `acessos_workspace`: `nivel_acesso = 'total'` |
| `apenas_relatorios` | Acesso apenas a relatórios específicos | `nivel_acesso = 'apenas_relatorios'` + registros em `acessos_relatorio` |
| `nenhum` | Sem acesso ao workspace | Não criar registro em `acessos_workspace` ou usar `nivel_acesso = 'nenhum'` |

---

## 5. Implementação das Dependências/Guards no FastAPI

### obter_usuario_atual
```python
# Valida se o token JWT é válido e não expirado
# Valida se a sessão vinculada ao token ainda está ativa no SQL Server
# Carrega o usuário do banco e injeta na rota
```

### exigir_perfil
```python
# Verifica se o perfil do usuário tem permissão para acessar o endpoint
# Usado como Depends(exigir_perfil("administrador", "super_administrador"))
```

### exigir_permissao
```python
# Verifica permissão granular (módulo × ação)
# Consulta: permissoes_perfil + sobrescritas_permissao
# Cache pode ser feito em memória/TanStack Query no frontend; a fonte da verdade é o SQL Server
# Usado como Depends(exigir_permissao("usuarios", "editar"))
```

### validar_expediente
```python
# Verifica se o usuário pode acessar com base no horário de expediente
# Consultado a cada requisição autenticada
# Verifica: regras_expediente + grupos_excecao + membros_grupo_excecao
```

---

## 6. Algoritmo de Resolução de Permissão

```python
def resolver_permissao(usuario_id: str, modulo: str, acao: str) -> bool:

  # 1. Carregar usuário e seu perfil
  usuario = repositorio_usuarios.buscar_por_id(usuario_id)

  # 2. Super Admin e Admin: acesso irrestrito
  if usuario.perfil in ("super_administrador", "administrador"):
      return True

  # 3. Verificar override individual primeiro (precedência)
  sobrescrita = repositorio_sobrescritas.buscar_por_usuario_modulo(usuario_id, modulo)
  if sobrescrita and getattr(sobrescrita, acao) is not None:
      return getattr(sobrescrita, acao)  # True ou False — override definitivo

  # 4. Fallback para permissão do perfil
  permissao_perfil = repositorio_permissoes.buscar_por_perfil_modulo(usuario.perfil, modulo)
  return getattr(permissao_perfil, acao, False) if permissao_perfil else False
```

---

## 7. Controle de Acesso a Relatórios PBI

```python
def pode_acessar_relatorio(usuario_id: str, relatorio_id: str) -> bool:

  usuario = repositorio_usuarios.buscar_por_id(usuario_id)

  # Admins têm acesso irrestrito
  if usuario.perfil in ("super_administrador", "administrador"):
      return True

  relatorio = repositorio_relatorios.buscar_por_id(relatorio_id)

  # Relatórios rascunho: apenas gerente+
  if relatorio.status == "rascunho" and usuario.perfil in ("operador", "visitante"):
      return False

  # Verificar acesso ao workspace
  acesso_workspace = repositorio_acessos_workspace.buscar(usuario_id, relatorio.espaco_trabalho_id)
  if not acesso_workspace:
      return False

  # Acesso total ao workspace
  if acesso_workspace.nivel_acesso == "total":
      return True

  # Acesso apenas a relatórios específicos
  if acesso_workspace.nivel_acesso == "apenas_relatorios":
      return repositorio_acessos_relatorio.existe(usuario_id, relatorio_id)

  return False
```

---

## Histórico de Alterações

| Versão | Data | Autor | Descrição |
|--------|------|-------|-----------|
| 1.0 | Maio/2026 | — | Criação inicial do documento |
