import { useState } from 'react'
import '../styles/modal-confirmacao.css'

export default function ModalConfirmacao({
  titulo,
  mensagem,
  labelConfirmar = 'Confirmar',
  labelCancelar  = 'Cancelar',
  variante       = 'primary',  // 'primary' | 'danger' | 'warning'
  icone,
  modo           = 'confirm',  // 'confirm' | 'alert'
  digitarConfirmar = false,    // quando true, exige digitar "CONFIRMAR" para habilitar o botão
  onConfirmar,
  onCancelar,
}) {
  const [digitado, setDigitado] = useState('')
  const confirmacaoValida = !digitarConfirmar || digitado === 'CONFIRMAR'

  function handleOverlay(e) {
    if (e.target === e.currentTarget) {
      modo === 'alert' ? onConfirmar?.() : onCancelar?.()
    }
  }

  const iconePadrao = {
    danger:  'fa-triangle-exclamation',
    warning: 'fa-circle-exclamation',
    primary: 'fa-circle-info',
  }[variante]

  return (
    <div className="mc-overlay" onClick={handleOverlay}>
      <div className="mc-box" role="dialog" aria-modal="true">
        <div className={`mc-icon-wrap mc-icon-${variante}`}>
          <i className={`fa-solid ${icone || iconePadrao}`} />
        </div>

        <div className="mc-body">
          {titulo && <div className="mc-titulo">{titulo}</div>}
          <div className="mc-mensagem">{mensagem}</div>
        </div>

        {digitarConfirmar && (
          <div style={{ width: '100%' }}>
            <div style={{ fontSize: 12, color: 'var(--gray-500)', marginBottom: 6, textAlign: 'left' }}>
              Digite <strong>CONFIRMAR</strong> para prosseguir:
            </div>
            <input
              className="modal-input"
              autoFocus
              value={digitado}
              onChange={e => setDigitado(e.target.value)}
              placeholder="CONFIRMAR"
              style={{ textTransform: 'uppercase', letterSpacing: 1 }}
            />
          </div>
        )}

        <div className="mc-actions">
          {modo === 'confirm' && (
            <button className="btn btn-ghost" onClick={onCancelar}>
              {labelCancelar}
            </button>
          )}
          <button
            className={`btn btn-${variante === 'danger' ? 'danger' : 'primary'}`}
            onClick={onConfirmar}
            disabled={!confirmacaoValida}
            autoFocus={!digitarConfirmar}
          >
            {labelConfirmar}
          </button>
        </div>
      </div>
    </div>
  )
}
