import { styles } from './styles';

/** Explica por que o botão está apagado e deixa a pessoa testar a IA de novo. */
export function AvisoIaOffline({ motivo, aoTestar }: { motivo: string; aoTestar: () => void }) {
  const detalhe = motivo.trim().replace(/[.\s]+$/, '');
  return (
    <div
      role="status"
      data-testid="aviso-ia-offline"
      style={{ marginTop: '8px', fontSize: '13px', color: '#fde68a', lineHeight: 1.5 }}
    >
      A IA ativa está offline{detalhe ? `: ${detalhe}` : ''}. Teste de novo ou use <strong>Copiar Prompt</strong>.
      <div style={{ marginTop: '6px' }}>
        <button type="button" style={styles.btnSecondary} onClick={aoTestar}>
          Testar de novo
        </button>
      </div>
    </div>
  );
}
