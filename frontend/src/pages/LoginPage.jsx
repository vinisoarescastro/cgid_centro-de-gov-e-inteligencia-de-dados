import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/login.css'
import logoBranco from '../assets/logo-bt-branco.png'
import logoColorido from '../assets/logo-bt-colorido.png'

export default function LoginPage() {
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!email || !password) {
      setError('Preencha e-mail e senha para continuar.')
      return
    }
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, senha: password }),
      })
      const data = await res.json()
      if (data.sucesso) {
        sessionStorage.setItem('cgid_user', JSON.stringify(data.usuario))
        navigate('/')
      } else {
        setError(data.mensagem || 'E-mail ou senha incorretos.')
      }
    } catch {
      setError('Não foi possível conectar ao servidor. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-screen">
      <div className="login-bg" />
      <div className="login-grid" />

      <div className="login-wrap">
        {/* Lado esquerdo — branding */}
        <div className="login-left">
          <div className="login-left-brand">
            <img src={logoBranco} alt="Brasil Terrenos" className="login-left-logo" />
          </div>

          <div className="login-left-body">
            <div className="login-left-tagline">
              Centro de Governança<br/>e Inteligência de Dados
            </div>
            <div className="login-left-desc">
              Plataforma centralizada para gestão de indicadores, monitoramento de
              performance e tomada de decisão baseada em dados.
            </div>
            <div className="login-left-pills">
              {[
                { icon: 'fa-chart-line', label: 'Dashboards' },
                { icon: 'fa-shield-halved', label: 'Governança' },
                { icon: 'fa-brain-circuit', label: 'IA & Analytics' },
                { icon: 'fa-bell', label: 'Alertas' },
              ].map(({ icon, label }) => (
                <span key={label} className="login-left-pill">
                  <i className={`fa-solid ${icon}`} />
                  {label}
                </span>
              ))}
            </div>
          </div>

          <div className="login-footer-left">
            © {new Date().getFullYear()} Brasil Terrenos · CGID v1.0
          </div>
        </div>

        {/* Lado direito — formulário */}
        <div className="login-right">
          <img src={logoColorido} alt="Brasil Terrenos" className="login-right-logo-mobile" />
          <div className="login-right-brand-mobile">Centro de Governança e Inteligência de Dados</div>
          <div className="login-right-title">Bem-vindo de volta</div>
          <div className="login-right-sub">Entre com suas credenciais corporativas</div>

          <form onSubmit={handleSubmit} noValidate>
            <div className="lf-group">
              <label className="lf-label">E-mail</label>
              <div className="lf-wrap">
                <i className="fa-solid fa-envelope lf-icon" />
                <input
                  className="lf-input"
                  type="email"
                  placeholder="email@btsa.com"
                  autoComplete="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="lf-group">
              <label className="lf-label">Senha</label>
              <div className="lf-wrap">
                <i className="fa-solid fa-lock lf-icon" />
                <input
                  className="lf-input"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••••"
                  autoComplete="current-password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  className="lf-eye"
                  onClick={() => setShowPassword(v => !v)}
                  aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                >
                  <i className={`fa-solid ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`} />
                </button>
              </div>
            </div>

            <div className="lf-forgot">
              <a href="#">Esqueceu a senha?</a>
            </div>

            {error && (
              <div className="lf-error">
                <i className="fa-solid fa-circle-exclamation" />
                {error}
              </div>
            )}

            <button type="submit" className="btn-login-submit" disabled={loading}>
              {loading
                ? <><i className="fa-solid fa-circle-notch fa-spin" /> Entrando…</>
                : <><i className="fa-solid fa-arrow-right-to-bracket" /> Entrar</>
              }
            </button>
          </form>

          <div className="login-footer">
            Acesso restrito a colaboradores autorizados
          </div>
        </div>
      </div>
    </div>
  )
}
