import { useEffect, useRef, useState, type CSSProperties } from 'react';
import { styles } from './styles';

const botaoVermelho: CSSProperties = {
  backgroundColor: '#b91c1c',
  color: '#ffffff',
  border: '1px solid #dc2626',
  borderRadius: '10px',
  padding: '10px 18px',
  fontSize: '14px',
  fontWeight: 700,
  cursor: 'pointer',
};

/** Botão vermelho no canto superior direito, que desliga o app depois de confirmar numa janela. */
export function FecharApp({ apiBase, aoFechar }: { apiBase: string; aoFechar: () => void }) {
  const [confirmando, setConfirmando] = useState(false);

  return (
    <>
      <div style={{ position: 'absolute', top: '16px', right: '16px' }}>
        <button type="button" style={botaoVermelho} title="Fechar o Power Request" onClick={() => setConfirmando(true)}>
          Fechar
        </button>
      </div>
      {confirmando && (
        <ConfirmarFechamento apiBase={apiBase} aoFechar={aoFechar} onCancelar={() => setConfirmando(false)} />
      )}
    </>
  );
}

function ConfirmarFechamento({
  apiBase,
  aoFechar,
  onCancelar,
}: {
  apiBase: string;
  aoFechar: () => void;
  onCancelar: () => void;
}) {
  const [fechando, setFechando] = useState(false);
  const [erro, setErro] = useState('');
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const janela = ref.current;
    if (janela && !janela.open) janela.showModal(); // o foco começa no primeiro botão ("Não")
  }, []);

  const fechar = async () => {
    setFechando(true);
    setErro('');
    try {
      const res = await fetch(`${apiBase}/api/encerrar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmar: true }),
      });
      if (res.ok) {
        aoFechar();
        return;
      }
      const data = await res.json().catch(() => null);
      setErro(typeof data?.detail === 'string' ? data.detail : 'Não foi possível fechar o app.');
    } catch {
      setErro('Não consegui falar com o app. Ele pode já estar fechado.');
    }
    setFechando(false);
  };

  return (
    <dialog
      ref={ref}
      aria-labelledby="titulo-fechar-app"
      onCancel={(e) => {
        e.preventDefault(); // tecla Esc
        if (!fechando) onCancelar();
      }}
      onClose={onCancelar} // se o navegador fechar a janela por conta própria
      style={{
        maxWidth: '420px',
        width: 'calc(100% - 32px)',
        padding: '20px',
        borderRadius: '14px',
        border: '1px solid #334155',
        backgroundColor: '#0b1220',
        color: '#e2e8f0',
        fontSize: '13.5px',
        lineHeight: 1.55,
      }}
    >
      <h2 id="titulo-fechar-app" style={{ margin: '0 0 10px', fontSize: '17px' }}>
        Deseja realmente fechar o Power Request?
      </h2>
      <p style={{ margin: '0 0 14px', color: '#94a3b8' }}>O que não foi salvo na tela se perde.</p>
      {erro && (
        <p role="alert" style={{ margin: '0 0 14px', color: '#fca5a5' }}>
          {erro}
        </p>
      )}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
        <button type="button" style={styles.btnSecondary} onClick={onCancelar} disabled={fechando}>
          Não
        </button>
        <button type="button" style={botaoVermelho} onClick={fechar} disabled={fechando}>
          {fechando ? 'Fechando…' : 'Sim, fechar'}
        </button>
      </div>
    </dialog>
  );
}

/** Tela que fica quando o navegador não deixa a aba fechar sozinha. */
export function AppEncerrado() {
  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <section style={styles.card} role="status">
          <h1 style={styles.title}>Power Request encerrado</h1>
          <p style={styles.subtitle}>
            Pode fechar esta aba. Para usar de novo, abra o Power Request.
          </p>
        </section>
      </div>
    </div>
  );
}
