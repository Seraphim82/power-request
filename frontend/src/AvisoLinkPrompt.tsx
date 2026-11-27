import { useEffect, useRef, useState } from 'react';
import { styles } from './styles';
import type { EscolhaAviso } from './avisoLink';

interface Props {
  nome: string;
  atalhoColar: string;
  onEscolher: (escolha: EscolhaAviso, ciente: boolean) => void;
  onCancelar: () => void;
}

/** Aparece toda vez antes de abrir a IA com o prompt no endereço. A ciência não fica guardada. */
export function AvisoLinkPrompt({ nome, atalhoColar, onEscolher, onCancelar }: Props) {
  const [ciente, setCiente] = useState(false);
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const janela = ref.current;
    if (janela && !janela.open) janela.showModal();
  }, []);

  return (
    <dialog
      ref={ref}
      aria-labelledby="titulo-aviso-link"
      onCancel={(e) => {
        e.preventDefault(); // tecla Esc
        onCancelar();
      }}
      style={{
        maxWidth: '460px',
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
      <h2 id="titulo-aviso-link" style={{ margin: '0 0 10px', fontSize: '17px' }}>
        Antes de abrir o {nome}
      </h2>
      <p style={{ margin: '0 0 10px' }}>
        Seu prompt vai dentro do endereço da página. O site <strong>recebe o texto assim que a página abre</strong>,
        antes de você apertar Enter, e ele pode ficar no histórico do navegador, inclusive no sincronizado.
      </p>
      <p style={{ margin: '0 0 10px', color: '#fde68a' }}>
        Não envie dados de clientes, senhas nem informações sigilosas.
      </p>
      <p style={{ margin: '0 0 14px', color: '#94a3b8' }}>
        Em <strong>Só copiar e abrir</strong>, o texto não vai no endereço. Para enviar, cole ({atalhoColar}) na
        caixa do site.
      </p>
      <label style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '14px' }}>
        <input type="checkbox" checked={ciente} onChange={(e) => setCiente(e.target.checked)} />
        Li e estou ciente
      </label>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
        <button type="button" style={styles.btnSecondary} onClick={onCancelar} autoFocus>
          Cancelar
        </button>
        <button type="button" style={styles.btnSecondary} onClick={() => onEscolher('so-copiar', ciente)}>
          Só copiar e abrir
        </button>
        <button
          type="button"
          style={{ ...styles.btnPrimary, opacity: ciente ? 1 : 0.45, cursor: ciente ? 'pointer' : 'not-allowed' }}
          disabled={!ciente}
          onClick={() => onEscolher('preenchido', ciente)}
        >
          Abrir preenchido
        </button>
      </div>
    </dialog>
  );
}
