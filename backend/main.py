from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from database import engine, get_db, Base
from models import Usuario, LogAuditoria, EspacoTrabalho, Relatorio, AcessoWorkspace

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CGID API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAX_TENTATIVAS = 5


# ─── Schemas ─────────────────────────────────────────────────────────────────
class LoginInput(BaseModel):
    email: str
    senha: str

class UsuarioPublico(BaseModel):
    id: str
    nome: str
    email: str
    perfil: str
    foto_url: Optional[str] = None

    model_config = {"from_attributes": True}

class LoginResponse(BaseModel):
    sucesso: bool
    mensagem: str
    usuario: Optional[UsuarioPublico] = None


# ─── Utilitários ─────────────────────────────────────────────────────────────
def registrar_log(db: Session, tipo: str, modulo: str, detalhe: str,
                  usuario: Optional[Usuario] = None, ip: Optional[str] = None):
    db.add(LogAuditoria(
        usuario_id    = usuario.id    if usuario else None,
        nome_usuario  = usuario.nome  if usuario else None,
        email_usuario = usuario.email if usuario else None,
        tipo_evento   = tipo,
        modulo        = modulo,
        detalhe       = detalhe,
        endereco_ip   = ip,
    ))


# ─── Endpoints ───────────────────────────────────────────────────────────────
@app.get("/")
def inicio():
    return {"mensagem": "CGID no ar!"}


@app.post("/login", response_model=LoginResponse)
def login(dados: LoginInput, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    if not usuario:
        return LoginResponse(sucesso=False, mensagem="E-mail ou senha incorretos.")

    if usuario.status == "bloqueado":
        return LoginResponse(sucesso=False, mensagem="Conta bloqueada. Entre em contato com o administrador.")

    if usuario.status == "inativo":
        return LoginResponse(sucesso=False, mensagem="Conta inativa. Entre em contato com o administrador.")

    if not pwd.verify(dados.senha, usuario.hash_senha):
        usuario.tentativas_login += 1
        if usuario.tentativas_login >= MAX_TENTATIVAS:
            usuario.status = "bloqueado"
            registrar_log(db, "seguranca", "autenticacao",
                          f"Conta bloqueada após {MAX_TENTATIVAS} tentativas", usuario)
            db.commit()
            return LoginResponse(sucesso=False, mensagem="Conta bloqueada após 5 tentativas incorretas.")
        db.commit()
        restantes = MAX_TENTATIVAS - usuario.tentativas_login
        return LoginResponse(sucesso=False, mensagem=f"E-mail ou senha incorretos. {restantes} tentativa(s) restante(s).")

    usuario.tentativas_login = 0
    usuario.ultimo_login = datetime.now(timezone.utc)
    registrar_log(db, "autenticacao", "autenticacao", "Login realizado com sucesso", usuario)
    db.commit()

    return LoginResponse(
        sucesso=True,
        mensagem="Login realizado com sucesso.",
        usuario=UsuarioPublico.model_validate(usuario),
    )


# ─── Schemas de Usuários ─────────────────────────────────────────────────────

class UsuarioListItem(BaseModel):
    id: str
    nome: str
    email: str
    perfil: str
    status: str
    ultimo_login: Optional[datetime] = None
    foto_url: Optional[str] = None
    criado_em: Optional[datetime] = None
    model_config = {"from_attributes": True}

class UsuarioCriar(BaseModel):
    nome: str
    email: str
    senha: Optional[str] = None   # padrão: Mudar@123
    perfil: str

class UsuarioAtualizar(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    perfil: Optional[str] = None
    status: Optional[str] = None
    senha: Optional[str] = None


# ─── Gestão de Usuários ───────────────────────────────────────────────────────

PERFIS_VALIDOS  = {"super_administrador", "administrador", "gerente", "operador", "visitante"}
STATUS_VALIDOS  = {"ativo", "inativo", "bloqueado"}
PERFIS_ADMIN    = {"super_administrador", "administrador"}

@app.get("/usuarios", response_model=List[UsuarioListItem])
def listar_usuarios(
    status: Optional[str] = None,
    perfil: Optional[str] = None,
    busca: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Usuario)
    if status:
        q = q.filter(Usuario.status == status)
    if perfil:
        q = q.filter(Usuario.perfil == perfil)
    if busca:
        q = q.filter(
            (Usuario.nome.ilike(f"%{busca}%")) |
            (Usuario.email.ilike(f"%{busca}%"))
        )
    return q.order_by(Usuario.nome).all()


def _vincular_admin_workspaces(usuario_id: str, db: Session):
    """Vincula automaticamente todos os workspaces ativos para admins."""
    todos = db.query(EspacoTrabalho).filter(EspacoTrabalho.status == "ativo").all()
    db.query(AcessoWorkspace).filter(AcessoWorkspace.usuario_id == usuario_id).delete()
    for ws in todos:
        db.add(AcessoWorkspace(
            usuario_id=usuario_id,
            espaco_trabalho_id=ws.id,
            nivel_acesso="total",
        ))


@app.post("/usuarios", response_model=UsuarioListItem, status_code=201)
def criar_usuario(dados: UsuarioCriar, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
    if dados.perfil not in PERFIS_VALIDOS:
        raise HTTPException(status_code=422, detail="Perfil inválido.")
    senha = dados.senha if dados.senha else SENHA_PADRAO
    usuario = Usuario(
        nome       = dados.nome,
        email      = dados.email,
        hash_senha = pwd.hash(senha),
        perfil     = dados.perfil,
        status     = "ativo",
    )
    db.add(usuario)
    db.flush()
    if dados.perfil in PERFIS_ADMIN:
        _vincular_admin_workspaces(usuario.id, db)
    registrar_log(db, "usuario", "usuarios", f"Usuário criado: {dados.email}")
    db.commit()
    db.refresh(usuario)
    return usuario


@app.put("/usuarios/{usuario_id}", response_model=UsuarioListItem)
def atualizar_usuario(usuario_id: str, dados: UsuarioAtualizar, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if dados.email and dados.email != usuario.email:
        if db.query(Usuario).filter(Usuario.email == dados.email).first():
            raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
        usuario.email = dados.email
    if dados.nome:
        usuario.nome = dados.nome
    perfil_anterior = usuario.perfil
    if dados.perfil:
        if dados.perfil not in PERFIS_VALIDOS:
            raise HTTPException(status_code=422, detail="Perfil inválido.")
        usuario.perfil = dados.perfil
        # se passou a ser admin, auto-vincula todos os workspaces
        if dados.perfil in PERFIS_ADMIN and perfil_anterior not in PERFIS_ADMIN:
            _vincular_admin_workspaces(usuario.id, db)
    if dados.status:
        if dados.status not in STATUS_VALIDOS:
            raise HTTPException(status_code=422, detail="Status inválido.")
        if dados.status == "ativo":
            usuario.tentativas_login = 0
        usuario.status = dados.status
    if dados.senha:
        usuario.hash_senha = pwd.hash(dados.senha)
    registrar_log(db, "usuario", "usuarios", f"Usuário atualizado: {usuario.email}")
    db.commit()
    db.refresh(usuario)
    return usuario


SENHA_PADRAO = "Mudar@123"

@app.post("/usuarios/{usuario_id}/resetar-senha", status_code=200)
def resetar_senha(usuario_id: str, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    usuario.hash_senha = pwd.hash(SENHA_PADRAO)
    usuario.tentativas_login = 0
    if usuario.status == "bloqueado":
        usuario.status = "ativo"
    registrar_log(db, "usuario", "usuarios", f"Senha redefinida para padrão: {usuario.email}")
    db.commit()
    return {"mensagem": f"Senha redefinida para o padrão com sucesso."}


@app.delete("/usuarios/{usuario_id}", status_code=204)
def excluir_usuario(usuario_id: str, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    registrar_log(db, "usuario", "usuarios", f"Usuário excluído: {usuario.email}")
    db.delete(usuario)
    db.commit()


# ─── Workspaces ───────────────────────────────────────────────────────────────

class WorkspaceItem(BaseModel):
    id: str
    nome: str
    icone: Optional[str] = None
    cor: Optional[str] = None
    status: str
    model_config = {"from_attributes": True}

class AcessoWorkspaceItem(BaseModel):
    espaco_trabalho_id: str
    nome: str
    icone: Optional[str] = None
    cor: Optional[str] = None
    nivel_acesso: str

class AcessoWorkspaceInput(BaseModel):
    espaco_trabalho_id: str
    nivel_acesso: str  # total | apenas_relatorios | nenhum

NIVEIS_VALIDOS = {"total", "apenas_relatorios", "nenhum"}

@app.get("/workspaces", response_model=List[WorkspaceItem])
def listar_workspaces(db: Session = Depends(get_db)):
    return db.query(EspacoTrabalho).filter(EspacoTrabalho.status == "ativo").order_by(EspacoTrabalho.nome).all()


@app.get("/usuarios/{usuario_id}/acessos", response_model=List[AcessoWorkspaceItem])
def listar_acessos_usuario(usuario_id: str, db: Session = Depends(get_db)):
    acessos = (
        db.query(AcessoWorkspace, EspacoTrabalho)
        .join(EspacoTrabalho, AcessoWorkspace.espaco_trabalho_id == EspacoTrabalho.id)
        .filter(AcessoWorkspace.usuario_id == usuario_id)
        .all()
    )
    return [
        AcessoWorkspaceItem(
            espaco_trabalho_id=a.espaco_trabalho_id,
            nome=ws.nome,
            icone=ws.icone,
            cor=ws.cor,
            nivel_acesso=a.nivel_acesso,
        )
        for a, ws in acessos
    ]


@app.put("/usuarios/{usuario_id}/acessos", status_code=200)
def salvar_acessos_usuario(
    usuario_id: str,
    acessos: List[AcessoWorkspaceInput],
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # admins sempre têm acesso total a tudo — ignora a lista enviada
    if usuario.perfil in PERFIS_ADMIN:
        _vincular_admin_workspaces(usuario_id, db)
        registrar_log(db, "acesso", "acessos_workspace", f"Acessos atualizados (admin): {usuario.email}")
        db.commit()
        return {"mensagem": "Acessos salvos com sucesso."}

    for item in acessos:
        if item.nivel_acesso not in NIVEIS_VALIDOS:
            raise HTTPException(status_code=422, detail=f"Nível de acesso inválido: {item.nivel_acesso}")

    # remove acessos anteriores e recria
    db.query(AcessoWorkspace).filter(AcessoWorkspace.usuario_id == usuario_id).delete()
    for item in acessos:
        if item.nivel_acesso != "nenhum":
            db.add(AcessoWorkspace(
                usuario_id=usuario_id,
                espaco_trabalho_id=item.espaco_trabalho_id,
                nivel_acesso=item.nivel_acesso,
            ))

    registrar_log(db, "acesso", "acessos_workspace", f"Acessos atualizados: {usuario.email}")
    db.commit()
    return {"mensagem": "Acessos salvos com sucesso."}


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/dashboard/kpis")
def dashboard_kpis(db: Session = Depends(get_db)):
    total_usuarios   = db.query(Usuario).filter(Usuario.status == "ativo").count()
    bloqueados       = db.query(Usuario).filter(Usuario.status == "bloqueado").count()
    workspaces_ativos = db.query(EspacoTrabalho).filter(EspacoTrabalho.status == "ativo").count()

    hoje = datetime.now(timezone.utc).date()
    acessos_negados = db.query(LogAuditoria).filter(
        LogAuditoria.tipo_evento == "seguranca",
        func.date(LogAuditoria.momento) == hoje,
    ).count()

    return {
        "usuarios_ativos":   total_usuarios,
        "usuarios_bloqueados": bloqueados,
        "acessos_negados_hoje": acessos_negados,
        "workspaces_ativos": workspaces_ativos,
    }


@app.get("/dashboard/eventos")
def dashboard_eventos(db: Session = Depends(get_db)):
    logs = (
        db.query(LogAuditoria)
        .order_by(LogAuditoria.momento.desc())
        .limit(5)
        .all()
    )

    ICONES = {
        "autenticacao": {"icon": "fa-right-to-bracket", "color": "#d1fae5", "iconColor": "#059669"},
        "seguranca":    {"icon": "fa-user-lock",        "color": "#fef3c7", "iconColor": "#d97706"},
        "usuario":      {"icon": "fa-user-pen",         "color": "#eff6ff", "iconColor": "#3b82f6"},
        "permissao":    {"icon": "fa-key",              "color": "#eff6ff", "iconColor": "#3b82f6"},
        "acesso":       {"icon": "fa-ban",              "color": "#fee2e2", "iconColor": "#ef4444"},
        "relatorio":    {"icon": "fa-chart-bar",        "color": "#f5f3ff", "iconColor": "#7c3aed"},
        "sistema":      {"icon": "fa-gear",             "color": "#f1f5f9", "iconColor": "#64748b"},
    }

    agora = datetime.now(timezone.utc)

    def tempo_relativo(momento):
        if momento is None:
            return "—"
        if momento.tzinfo is None:
            momento = momento.replace(tzinfo=timezone.utc)
        diff = int((agora - momento).total_seconds())
        if diff < 60:
            return "agora"
        if diff < 3600:
            return f"{diff // 60}min"
        if diff < 86400:
            return f"{diff // 3600}h"
        return f"{diff // 86400}d"

    return [
        {
            **ICONES.get(log.tipo_evento, ICONES["sistema"]),
            "title": log.detalhe,
            "sub":   log.email_usuario or "sistema",
            "time":  tempo_relativo(log.momento),
        }
        for log in logs
    ]


@app.get("/dashboard/workspaces")
def dashboard_workspaces(db: Session = Depends(get_db)):
    workspaces = (
        db.query(EspacoTrabalho)
        .filter(EspacoTrabalho.status == "ativo")
        .order_by(EspacoTrabalho.nome)
        .all()
    )

    resultado = []
    for ws in workspaces:
        total_relatorios = db.query(Relatorio).filter(
            Relatorio.espaco_trabalho_id == ws.id,
            Relatorio.status == "publicado",
        ).count()

        acesso_total = db.query(AcessoWorkspace).filter(
            AcessoWorkspace.espaco_trabalho_id == ws.id,
            AcessoWorkspace.nivel_acesso == "total",
        ).count()

        acesso_parcial = db.query(AcessoWorkspace).filter(
            AcessoWorkspace.espaco_trabalho_id == ws.id,
            AcessoWorkspace.nivel_acesso == "apenas_relatorios",
        ).count()

        resultado.append({
            "nome":          ws.nome,
            "reports":       total_relatorios,
            "totalAccess":   acesso_total,
            "partialAccess": acesso_parcial,
        })

    return resultado
