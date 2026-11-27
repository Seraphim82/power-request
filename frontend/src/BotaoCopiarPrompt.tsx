import { useEffect, useRef, useState } from 'react';
import { styles } from './styles';

type Situacao = 'ocioso' | 'copiado' | 'falhou';

/** Copia o prompt e confirma no próprio botão, onde a pessoa está olhando. */
export function BotaoCopiarPrompt({ texto }: { texto: string }) {
  const [situacao, setSituacao] = useState<Situacao>('ocioso');
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  const copiar = async () => {
    window.clearTimeout(timer.current);
    try {
      await navigator.clipboard.writeText(texto);
      setSituacao('copiado');
      timer.current = window.setTimeout(() => setSituacao('ocioso'), 2000);
    } catch {
      setSituacao('falhou');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
      <button type="button" style={{ ...styles.btnPrimary, minWidth: '140px' }} onClick={copiar}>
        {situacao === 'copiado' ? 'Copiado ✓' : 'Copiar Prompt'}
      </button>
      <div role="status" style={{ fontSize: '12.5px', color: '#fde68a' }}>
        {situacao === 'falhou' ? 'Não consegui copiar. Selecione e copie o texto do quadro.' : ''}
        {/* Aviso só para leitor de tela: o texto do botão já mostra a confirmação. */}
        {situacao === 'copiado' && (
          <span style={{ position: 'absolute', width: '1px', height: '1px', overflow: 'hidden', clipPath: 'inset(50%)' }}>
            Prompt copiado.
          </span>
        )}
      </div>
    </div>
  );
}
