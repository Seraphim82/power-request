import { useRef, useState } from 'react';
import {
  MAX_TEXTO_ORGANIZAR,
  NOMES_CAMPOS,
  campoVazio,
  podeOrganizar,
  precisaPerguntar,
  type CamposOrganizados,
  type TrechoDeFora,
} from './organizar';
import type { CategoriaId } from './constants';
import { styles } from './styles';

export interface RespostaOrganizar {
  campos: CamposOrganizados;
  contexto: string;
  categoria_sugerida: CategoriaId;
  perguntas: { campo: string; pergunta: string; motivo: string }[];
  incoerencias: string[];
  avisos: string[];
  ficou_de_fora: TrechoDeFora[];
}

interface Props {
  apiBase: string;
  precisaConfirmar: boolean;
  contextoSalvoLigado: boolean;
  aoUsar: (resposta: RespostaOrganizar) => void;
}

const aviso = { marginTop: '8px', fontSize: '13px', color: '#fde68a', lineHeight: 1.5 } as const;
const bloco = { whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: '13px' } as const;

/** Cola um prompt pronto, mostra os campos separados e só preenche o formulário se a pessoa mandar. */
export function OrganizarPrompt({ apiBase, precisaConfirmar, contextoSalvoLigado, aoUsar }: Props) {
  const [texto, setTexto] = useState('');
  const [resposta, setResposta] = useState<RespostaOrganizar | null>(null);
  const [erro, setErro] = useState('');
  const [organizando, setOrganizando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const pedidoAtual = useRef(0);

  const mudarTexto = (novo: string) => {
    // O resultado mostrado sempre corresponde ao texto que está na caixa.
    pedidoAtual.current += 1;
    setTexto(novo);
    setResposta(null);
    setErro('');
    setOrganizando(false);
    setConfirmando(false);
  };

  const organizar = async () => {
    const id = ++pedidoAtual.current;
    setOrganizando(true);
    setResposta(null);
    setErro('');
    setConfirmando(false);
    try {
      const res = await fetch(`${apiBase}/api/organizar-prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto }),
      });
      const data = await res.json();
      if (id !== pedidoAtual.current) return;
      if (res.ok) setResposta(data);
      else setErro(typeof data.detail === 'string' ? data.detail : 'Não foi possível organizar o texto.');
    } catch {
      if (id === pedidoAtual.current) setErro('Não foi possível conectar ao servidor local.');
    } finally {
      if (id === pedidoAtual.current) setOrganizando(false);
    }
  };

  const tamanho = texto.trim().length;

  return (
    <div style={{ marginTop: '12px' }}>
      <label htmlFor="texto-organizar" style={styles.magicLabel}>
        Cole aqui o prompt que você já tem:
      </label>
      <textarea
        id="texto-organizar"
        rows={8}
        style={styles.textarea}
        value={texto}
        onChange={(e) => mudarTexto(e.target.value)}
      />
      <div style={{ ...styles.actionBar, alignItems: 'center', marginTop: '10px' }}>
        <button
          type="button"
          style={{ ...styles.btnSecondary, ...(podeOrganizar(texto) ? {} : { opacity: 0.5 }) }}
          onClick={organizar}
          disabled={organizando || !podeOrganizar(texto)}
        >
          {organizando ? 'Organizando...' : 'Organizar'}
        </button>
        <span style={{ fontSize: '12px', color: tamanho > MAX_TEXTO_ORGANIZAR ? '#fca5a5' : '#94a3b8' }}>
          {tamanho}/{MAX_TEXTO_ORGANIZAR}
          {tamanho > MAX_TEXTO_ORGANIZAR ? ' • texto grande demais para organizar' : ''}
        </span>
      </div>

      {erro && <div style={styles.alertBox}>{erro}</div>}

      {resposta && (
        <div style={{ marginTop: '14px' }} data-testid="resultado-organizar">
          {resposta.contexto && (
            <div style={{ padding: '12px', border: '1px solid #334155', borderRadius: '8px' }}>
              <strong>Contexto encontrado (separado dos campos)</strong>
              <div style={bloco}>{resposta.contexto}</div>
              <div style={aviso}>
                Este Contexto <strong>não vai junto</strong> e não altera o seu Contexto fixo.{' '}
                {contextoSalvoLigado
                  ? 'Ao gerar, entra o Contexto fixo que está salvo no app.'
                  : 'Ao gerar, o prompt sai sem Contexto, porque o Contexto fixo está desligado ou vazio.'}
              </div>
            </div>
          )}

          <dl style={{ margin: '12px 0' }}>
            {NOMES_CAMPOS.map(([campo, nome]) => {
              const valor = resposta.campos[campo];
              return (
                <div key={campo} style={{ marginBottom: '10px' }}>
                  <dt style={{ fontWeight: 700, fontSize: '13px', color: '#d4af37' }}>{nome}</dt>
                  <dd style={{ ...bloco, margin: '2px 0 0' }}>
                    {campoVazio(valor) ? (
                      <em style={{ color: '#94a3b8' }}>não encontrado</em>
                    ) : Array.isArray(valor) ? (
                      <ul style={{ margin: 0, paddingLeft: '18px' }}>
                        {valor.map((regra) => (
                          <li key={regra}>{regra}</li>
                        ))}
                      </ul>
                    ) : (
                      valor
                    )}
                  </dd>
                </div>
              );
            })}
          </dl>

          {resposta.perguntas.length > 0 && (
            <div style={aviso}>
              <strong>Vale completar depois nas etapas:</strong>
              <ul style={{ margin: '4px 0', paddingLeft: '18px' }}>
                {resposta.perguntas.map((p) => (
                  <li key={p.campo}>
                    <strong>{p.pergunta}</strong> {p.motivo}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {resposta.incoerencias.map((a) => (
            <div key={a} style={aviso}>
              {a}
            </div>
          ))}
          {resposta.ficou_de_fora.length > 0 && (
            <div role="alert" style={styles.alertBox} data-testid="ficou-de-fora">
              <strong>Atenção: parte do seu texto NÃO vai para o formulário.</strong>
              {resposta.avisos.map((a) => (
                <div key={a}>{a}</div>
              ))}
              <div style={{ maxHeight: '220px', overflow: 'auto', marginTop: '8px' }}>
                {resposta.ficou_de_fora.map((trecho, i) => (
                  <div key={i} style={{ marginBottom: '8px' }}>
                    <strong>{trecho.titulo}:</strong>
                    <div style={bloco}>{trecho.texto}</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: '8px' }}>
                Guarde o seu texto original. Se precisar do que ficou de fora, resuma ou acrescente
                nas etapas.
              </div>
            </div>
          )}
          <p style={styles.helpText}>A separação é automática e pode errar: confira antes de usar.</p>

          {confirmando ? (
            <div role="alert" style={aviso}>
              {resposta.ficou_de_fora.length > 0 && (
                <div>
                  <strong>Parte do texto vai ficar de fora</strong> (veja o quadro acima). Esta lista e
                  o texto colado somem da tela ao continuar: copie antes o que precisar.
                </div>
              )}
              {precisaConfirmar && (
                <div>
                  Isto substitui <strong>todos os campos</strong> do formulário (os não encontrados
                  ficam vazios) e limpa da tela a revisão, o prompt gerado e a conversa.
                </div>
              )}
              <div style={{ ...styles.actionBar, marginTop: '8px' }}>
                <button type="button" style={styles.btnPrimary} onClick={() => aoUsar(resposta)}>
                  {precisaConfirmar ? 'Substituir' : 'Continuar mesmo assim'}
                </button>
                <button type="button" style={styles.btnSecondary} onClick={() => setConfirmando(false)}>
                  Cancelar
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              style={styles.btnPrimary}
              onClick={() =>
                precisaPerguntar(precisaConfirmar, resposta.ficou_de_fora)
                  ? setConfirmando(true)
                  : aoUsar(resposta)
              }
            >
              Usar estes campos
            </button>
          )}
        </div>
      )}
    </div>
  );
}
