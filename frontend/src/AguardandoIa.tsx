import { formatarTempo } from './tempoEspera';

/**
 * Animação de espera: o prompt "viaja" até o computador.
 * Mostra só que o app está esperando. Não mede o progresso da IA.
 * Os movimentos (classes espera-*) estão no index.html.
 */
export function AguardandoIa({ segundos }: { segundos: number }) {
  return (
    <div
      data-testid="aguardando-ia"
      style={{
        marginTop: '12px',
        padding: '14px 16px',
        borderRadius: '10px',
        border: '1px solid #334155',
        backgroundColor: '#020617',
        maxWidth: '440px',
      }}
    >
      <div aria-hidden="true" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <svg width="46" height="40" viewBox="0 0 46 40" fill="none" style={{ flexShrink: 0 }}>
          <rect x="2" y="5" width="42" height="30" rx="5" stroke="#d4af37" strokeWidth="2" />
          <path d="M10 14l6 6-6 6" stroke="#d4af37" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M21 27h13" stroke="#e2e8f0" strokeWidth="2.5" strokeLinecap="round" />
        </svg>
        <div style={{ position: 'relative', flex: 1, height: '12px' }}>
          <div style={{ position: 'absolute', left: 0, right: 0, top: '5px', height: '2px', backgroundColor: '#1e293b' }} />
          <div className="espera-ponto" />
        </div>
        <svg width="46" height="40" viewBox="0 0 46 40" fill="none" style={{ flexShrink: 0 }}>
          <rect className="espera-tela" x="5" y="4" width="36" height="25" rx="3" stroke="#4ade80" strokeWidth="2" />
          <path d="M23 29v6M14 36h18" stroke="#4ade80" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>
      <div style={{ marginTop: '8px', fontSize: '13px', color: '#cbd5e1', textAlign: 'center' }}>
        <span role="status">Aguardando a resposta da IA...</span>{' '}
        <span style={{ fontVariantNumeric: 'tabular-nums', color: '#94a3b8' }}>{formatarTempo(segundos)}</span>
      </div>
    </div>
  );
}
