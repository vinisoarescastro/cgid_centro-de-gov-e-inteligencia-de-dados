import { useState, useEffect } from 'react'

const API = 'http://localhost:8000'

export default function ModalHistoricoCritico({ entidade, entidadeId, campo, titulo, onClose }) {
  const [registros, setRegistros] = useState([])
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    const url = `${API}/historico-critico?entidade=${entidade}${entidadeId ? `&entidade_id=${entidadeId}` : ''}`
    fetch(url)
      .then(r => r.json())
      .then(data => setRegistros(campo ? data.filter(r => r.campo === campo) : data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [entidade, entidadeId, campo])

  function formatarMomento(iso) {
    return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-box" style={{ maxWidth: 560 }}>
        <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <i className="fa-solid fa-clock-rotate-left" style={{ color: 'var(--brand-500)' }} />
          {titulo || 'Histórico de Alterações'}
        </div>

        {loading ? (
          <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--gray-400)', fontSize: 13 }}>
            <i className="fa-solid fa-spinner fa-spin" style={{ marginRight: 8 }} />Carregando...
          </div>
        ) : registros.length === 0 ? (
          <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--gray-400)', fontSize: 13 }}>
            <i className="fa-solid fa-circle-info" style={{ marginRight: 8 }} />Nenhuma alteração registrada ainda.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 400, overflowY: 'auto' }}>
            {registros.map(r => (
              <div key={r.id} style={{
                border: '1px solid var(--gray-200)', borderRadius: 'var(--r-md)',
                padding: '12px 14px', background: 'var(--gray-50)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, gap: 8 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--gray-500)', fontFamily: 'monospace' }}>
                    {r.campo}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--gray-400)', whiteSpace: 'nowrap' }}>
                    {formatarMomento(r.momento)}
                    {r.alterado_por_nome && <> · <strong>{r.alterado_por_nome}</strong></>}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: '#dc2626', marginBottom: 3 }}>ANTES</div>
                    <div style={{
                      fontFamily: 'monospace', fontSize: 11, padding: '6px 8px',
                      background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6,
                      wordBreak: 'break-all', color: '#7f1d1d',
                    }}>
                      {r.valor_anterior || <em style={{ color: '#fca5a5' }}>vazio</em>}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', color: 'var(--gray-400)', fontSize: 14 }}>
                    <i className="fa-solid fa-arrow-right" />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: '#16a34a', marginBottom: 3 }}>DEPOIS</div>
                    <div style={{
                      fontFamily: 'monospace', fontSize: 11, padding: '6px 8px',
                      background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 6,
                      wordBreak: 'break-all', color: '#14532d',
                    }}>
                      {r.valor_novo || <em style={{ color: '#86efac' }}>vazio</em>}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="modal-actions">
          <button className="btn btn-primary" onClick={onClose}>Fechar</button>
        </div>
      </div>
    </div>
  )
}
