import { useEffect, useState } from 'react';
import {
  BRANDS,
  CATEGORIES,
  STEP_META,
  STORAGE_KEY,
  type AIConfigSalva,
  type AnaliseIntencao,
  type CategoriaConfig,
  type CategoriaId,
  type ItemHistorico,
  type LocalToolStatus,
  type ProviderInfo,
  type RevisaoPedido,
  type ResultadoPrompt,
} from './constants';
import { styles } from './styles';

const API_BASE = window.location.port === '5173' ? 'http://127.0.0.1:8000' : '';

function carregarConfigSalva(): AIConfigSalva {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        provider: parsed.provider || 'claude_cli',
        apiKey: parsed.apiKey || '',
        model: parsed.model || '',
        alias: parsed.alias || '',
        baseUrl: parsed.baseUrl || '',
        otimizarComIa: Boolean(parsed.otimizarComIa),
      };
    }
  } catch {
    // ignora erro de storage
  }
  return {
    provider: 'claude_cli',
    apiKey: '',
    model: '',
    alias: '',
    baseUrl: '',
    otimizarComIa: false,
  };
}

export default function App() {
  const configInicial = carregarConfigSalva();

  const [categoria, setCategoria] = useState<CategoriaId>('geral');
  const [etapa, setEtapa] = useState<number>(1);

  const [intencaoLivre, setIntencaoLivre] = useState<string>('');
  const [analisandoIntencao, setAnalisandoIntencao] = useState<boolean>(false);
  const [analiseInfo, setAnaliseInfo] = useState<AnaliseIntencao | null>(null);

  const [objetivo, setObjetivo] = useState<string>('');
  const [stack, setStack] = useState<string>('');
  const [entrada, setEntrada] = useState<string>('');
  const [saida, setSaida] = useState<string>('');
  const [regraAtual, setRegraAtual] = useState<string>('');
  const [regras, setRegras] = useState<string[]>([]);
  const [tratamentoErros, setTratamentoErros] = useState<string>('');

  const [revisao, setRevisao] = useState<RevisaoPedido | null>(null);
  const [resultado, setResultado] = useState<ResultadoPrompt | null>(null);
  const [erro, setErro] = useState<string>('');
  const [carregando, setCarregando] = useState<'revisar' | 'gerar' | null>(null);
  const [copiadoTexto, setCopiadoTexto] = useState<string>('');

  const [historicoAberto, setHistoricoAberto] = useState<boolean>(false);
  const [historico, setHistorico] = useState<ItemHistorico[]>([]);
  const [buscaHistorico, setBuscaHistorico] = useState<string>('');
  const [carregandoHistorico, setCarregandoHistorico] = useState<boolean>(false);
  const [confirmarLimpar, setConfirmarLimpar] = useState<boolean>(false);

  const [hubAberto, setHubAberto] = useState<boolean>(false);
  const [provedores, setProvedores] = useState<ProviderInfo[]>([]);
  const [ferramentasLocais, setFerramentasLocais] = useState<LocalToolStatus[]>([]);
  const [providerId, setProviderId] = useState<string>(configInicial.provider);
  const [apiKey, setApiKey] = useState<string>(configInicial.apiKey);
  const [model, setModel] = useState<string>(configInicial.model);
  const [alias] = useState<string>(configInicial.alias);
  const [baseUrl, setBaseUrl] = useState<string>(configInicial.baseUrl);
  const [otimizarComIa, setOtimizarComIa] = useState<boolean>(configInicial.otimizarComIa);
  const [statusConexao, setStatusConexao] = useState<string>('');
  const [testandoConexao, setTestandoConexao] = useState<boolean>(false);

  const catConfig: CategoriaConfig =
    CATEGORIES.find((c) => c.id === categoria) || CATEGORIES[0];
  const providerSelecionado: ProviderInfo | undefined = provedores.find(
    (p) => p.id === providerId
  );
  const ferramentaLocalAtual: LocalToolStatus | undefined = ferramentasLocais.find(
    (f) => f.provider_id === providerId
  );

  const etapasPreenchidas = [
    objetivo.trim().length > 0,
    stack.trim().length > 0,
    entrada.trim().length > 0,
    saida.trim().length > 0,
    regras.length > 0,
    tratamentoErros.trim().length > 0,
  ];
  const totalConcluidas = etapasPreenchidas.filter(Boolean).length;
  const progressoPct = Math.round((totalConcluidas / STEP_META.length) * 100);

  const carregarHistorico = async (termoBusca = '') => {
    setCarregandoHistorico(true);
    try {
      const params = new URLSearchParams();
      if (termoBusca.trim()) params.set('q', termoBusca.trim());
      params.set('limite', '30');
      const res = await fetch(`${API_BASE}/api/historico?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setHistorico(Array.isArray(data.itens) ? data.itens : []);
      }
    } catch {
      // ignora erro de rede transitório
    } finally {
      setCarregandoHistorico(false);
    }
  };

  useEffect(() => {
    carregarHistorico();

    fetch(`${API_BASE}/api/hub/providers`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.providers) {
          setProvedores(data.providers);
          const atual = data.providers.find(
            (p: ProviderInfo) => p.id === configInicial.provider
          );
          if (atual && !configInicial.model) {
            setModel(atual.modelo_padrao || '');
          }
          if (atual && !configInicial.baseUrl && atual.base_url_padrao) {
            setBaseUrl(atual.base_url_padrao);
          }
        }
      })
      .catch(() => {});

    fetch(`${API_BASE}/api/hub/local-tools`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.tools) setFerramentasLocais(data.tools);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    try {
      const payload: AIConfigSalva = {
        provider: providerId,
        apiKey,
        model,
        alias,
        baseUrl,
        otimizarComIa,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch {
      // ignora erro de storage
    }
  }, [providerId, apiKey, model, alias, baseUrl, otimizarComIa]);

  const selecionarProvedor = (novoId: string) => {
    setProviderId(novoId);
    setStatusConexao('');
    const info = provedores.find((p) => p.id === novoId);
    if (info) {
      setModel(info.modelo_padrao || '');
      setBaseUrl(info.base_url_padrao || '');
    }
  };

  const montarAiConfigPayload = () => {
    const usaChave = providerSelecionado?.auth_mode === 'api_key';
    if (usaChave && !apiKey.trim()) {
      return undefined;
    }
    return {
      provider: providerId,
      api_key: apiKey.trim(),
      model: model.trim(),
      alias: alias.trim(),
      base_url: baseUrl.trim(),
    };
  };

  const testarConexaoIa = async () => {
    setTestandoConexao(true);
    setStatusConexao('Testando conexão...');
    try {
      const res = await fetch(`${API_BASE}/api/hub/testar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: providerId,
          api_key: apiKey.trim(),
          model: model.trim(),
          alias: alias.trim(),
          base_url: baseUrl.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setStatusConexao(`Falha: ${data.detail || 'Verifique os dados.'}`);
      } else {
        setStatusConexao(`Conectado: ${data.mensagem}`);
      }
    } catch {
      setStatusConexao('Não foi possível conectar ao backend local.');
    } finally {
      setTestandoConexao(false);
    }
  };

  const analisarIntencaoLivre = async () => {
    if (!intencaoLivre.trim()) {
      setErro('Escreva o que você quer fazer para a IA estruturar os campos.');
      return;
    }
    setErro('');
    setAnalisandoIntencao(true);
    try {
      const res = await fetch(`${API_BASE}/api/analisar-intencao`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intencao: intencaoLivre.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setErro(data.detail || 'Não foi possível analisar sua ideia.');
        return;
      }
      setAnaliseInfo(data);
      if (data.categoria_sugerida) setCategoria(data.categoria_sugerida);
      if (data.rascunho) {
        setObjetivo(data.rascunho.objetivo || '');
        setStack(data.rascunho.stack || '');
        setEntrada(data.rascunho.entrada || '');
        setSaida(data.rascunho.saida || '');
        setRegras(Array.isArray(data.rascunho.regras) ? data.rascunho.regras : []);
        setTratamentoErros(data.rascunho.tratamento_erros || '');
      }
      setRevisao(null);
      setResultado(null);
    } catch {
      setErro('Erro ao falar com o backend. Verifique se o servidor está rodando.');
    } finally {
      setAnalisandoIntencao(false);
    }
  };

  const adicionarRegra = (texto?: string) => {
    const valor = (texto ?? regraAtual).trim();
    if (!valor) return;
    if (!regras.includes(valor)) {
      setRegras((prev) => [...prev, valor]);
    }
    if (texto === undefined) setRegraAtual('');
  };

  const removerRegra = (idx: number) => {
    setRegras((prev) => prev.filter((_, i) => i !== idx));
  };

  const payloadAtual = () => ({
    categoria,
    objetivo,
    stack,
    entrada,
    saida,
    regras,
    tratamento_erros: tratamentoErros,
    ai_config: montarAiConfigPayload(),
    otimizar_com_ia: otimizarComIa,
    salvar_historico: true,
  });

  const handleRevisar = async () => {
    setErro('');
    setResultado(null);
    setCarregando('revisar');
    try {
      const res = await fetch(`${API_BASE}/api/revisar-pedido`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadAtual()),
      });
      const data = await res.json();
      if (!res.ok) {
        setErro(data.detail || 'Erro ao revisar pedido.');
      } else {
        setRevisao(data);
      }
    } catch {
      setErro('Não foi possível conectar ao servidor local.');
    } finally {
      setCarregando(null);
    }
  };

  const handleGerar = async () => {
    setErro('');
    setCarregando('gerar');
    try {
      const res = await fetch(`${API_BASE}/api/gerar-prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadAtual()),
      });
      const data = await res.json();
      if (!res.ok) {
        setErro(data.detail || 'Erro ao gerar prompt.');
      } else {
        setResultado(data);
        setCopiadoTexto('');
        await carregarHistorico(buscaHistorico);
      }
    } catch {
      setErro('Não foi possível conectar ao servidor local.');
    } finally {
      setCarregando(null);
    }
  };

  const reabrirItemHistorico = (item: ItemHistorico) => {
    const catValida = CATEGORIES.some((c) => c.id === item.categoria)
      ? (item.categoria as CategoriaId)
      : 'geral';
    setCategoria(catValida);
    setObjetivo(item.objetivo || '');
    setStack(item.stack || '');
    setEntrada(item.entrada || '');
    setSaida(item.saida || '');
    setRegras(Array.isArray(item.regras) ? item.regras : []);
    setTratamentoErros(item.tratamento_erros || '');
    setResultado({
      prompt_final: item.prompt_final,
      tokens_estimados: item.tokens_estimados,
      gerado_por: item.gerado_por,
      historico_id: item.id,
    });
    setRevisao(null);
    setErro('');
    setEtapa(1);
    setHistoricoAberto(false);
  };

  const removerItemHistorico = async (id: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/historico/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setHistorico((prev) => prev.filter((item) => item.id !== id));
        if (resultado?.historico_id === id) {
          resetar();
        }
      }
    } catch {
      // ignora erro transitório
    }
  };

  const limparTodoHistorico = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/historico`, { method: 'DELETE' });
      if (res.ok) {
        setHistorico([]);
        setConfirmarLimpar(false);
        if (resultado?.historico_id) {
          resetar();
        }
      }
    } catch {
      // ignora erro transitório
    }
  };

  const copiarPrompt = async () => {
    if (!resultado?.prompt_final) return;
    try {
      await navigator.clipboard.writeText(resultado.prompt_final);
      setCopiadoTexto('Prompt copiado para a área de transferência.');
    } catch {
      setCopiadoTexto('Selecione e copie o texto do quadro acima.');
    }
  };

  const copiarAbrirEm = async (nomeMarca: string, chatUrl: string) => {
    if (!resultado?.prompt_final) return;
    try {
      await navigator.clipboard.writeText(resultado.prompt_final);
      setCopiadoTexto(`Prompt copiado! Abrindo ${nomeMarca}...`);
    } catch {
      setCopiadoTexto(`Abrindo ${nomeMarca} — se precisar, copie o prompt acima.`);
    }
    window.open(chatUrl, '_blank', 'noopener,noreferrer');
  };

  const resetar = () => {
    setEtapa(1);
    setIntencaoLivre('');
    setAnaliseInfo(null);
    setObjetivo('');
    setStack('');
    setEntrada('');
    setSaida('');
    setRegraAtual('');
    setRegras([]);
    setTratamentoErros('');
    setRevisao(null);
    setResultado(null);
    setErro('');
    setCopiadoTexto('');
  };

  const renderCampoEtapa = () => {
    switch (etapa) {
      case 1:
        return (
          <>
            <textarea
              rows={4}
              style={styles.textarea}
              placeholder={catConfig.placeholders.objetivo}
              value={objetivo}
              onChange={(e) => setObjetivo(e.target.value)}
            />
            <div style={styles.chipsRow}>
              <span style={styles.chipsLabel}>Exemplo rápido:</span>
              <button
                type="button"
                style={styles.chip}
                onClick={() => setObjetivo(catConfig.placeholders.objetivo.replace(/^Ex:\s*/i, ''))}
              >
                Usar exemplo desta categoria
              </button>
            </div>
          </>
        );
      case 2:
        return (
          <>
            <input
              type="text"
              style={styles.input}
              placeholder={catConfig.placeholders.stack}
              value={stack}
              onChange={(e) => setStack(e.target.value)}
            />
            <div style={styles.chipsRow}>
              <span style={styles.chipsLabel}>Sugestões:</span>
              {catConfig.sugestoes.stack.map((s) => (
                <button key={s} type="button" style={styles.chip} onClick={() => setStack(s)}>
                  + {s}
                </button>
              ))}
            </div>
          </>
        );
      case 3:
        return (
          <textarea
            rows={3}
            style={styles.textarea}
            placeholder={catConfig.placeholders.entrada}
            value={entrada}
            onChange={(e) => setEntrada(e.target.value)}
          />
        );
      case 4:
        return (
          <textarea
            rows={3}
            style={styles.textarea}
            placeholder={catConfig.placeholders.saida}
            value={saida}
            onChange={(e) => setSaida(e.target.value)}
          />
        );
      case 5:
        return (
          <>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                style={styles.input}
                placeholder={catConfig.placeholders.regra}
                value={regraAtual}
                onChange={(e) => setRegraAtual(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    adicionarRegra();
                  }
                }}
              />
              <button type="button" style={styles.btnSecondary} onClick={() => adicionarRegra()}>
                Adicionar
              </button>
            </div>
            <div style={styles.chipsRow}>
              <span style={styles.chipsLabel}>Regras rápidas:</span>
              {catConfig.sugestoes.regras.map((r) => (
                <button key={r} type="button" style={styles.chip} onClick={() => adicionarRegra(r)}>
                  + {r}
                </button>
              ))}
            </div>
            {regras.map((r, idx) => (
              <div key={`${r}-${idx}`} style={styles.ruleItem}>
                <span>• {r}</span>
                <button
                  type="button"
                  style={styles.removeBtn}
                  onClick={() => removerRegra(idx)}
                  title="Remover regra"
                >
                  ✕
                </button>
              </div>
            ))}
          </>
        );
      case 6:
      default:
        return (
          <>
            <textarea
              rows={3}
              style={styles.textarea}
              placeholder={catConfig.placeholders.tratamento_erros}
              value={tratamentoErros}
              onChange={(e) => setTratamentoErros(e.target.value)}
            />
            <div style={styles.chipsRow}>
              <span style={styles.chipsLabel}>Sugestões:</span>
              {catConfig.sugestoes.erros.map((errMsg) => (
                <button
                  key={errMsg}
                  type="button"
                  style={styles.chip}
                  onClick={() => setTratamentoErros(errMsg)}
                >
                  + {errMsg}
                </button>
              ))}
            </div>
          </>
        );
    }
  };

  const etapaAtualMeta = STEP_META[etapa - 1] || STEP_META[0];
  const modoAuth = providerSelecionado?.auth_mode || 'local_cli';

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <header style={styles.header}>
          <div>
            <div style={styles.badge}>POWER REQUEST • ENGENHARIA DE PROMPT GUIADA</div>
            <h1 style={styles.title}>Power Request</h1>
            <p style={styles.subtitle}>
              Transforme uma ideia simples em um pedido claro, revisado e econômico em tokens —
              sem precisar saber programar ou escrever prompts complexos.
            </p>
          </div>
          <div style={styles.headerActions}>
            <button
              type="button"
              style={styles.btnGhost}
              onClick={() => {
                const proximo = !historicoAberto;
                setHistoricoAberto(proximo);
                if (proximo) carregarHistorico(buscaHistorico);
              }}
            >
              {historicoAberto ? 'Fechar Histórico' : `Histórico (${historico.length})`}
            </button>
            <button type="button" style={styles.btnGhost} onClick={() => setHubAberto(!hubAberto)}>
              {hubAberto ? 'Fechar Hub de IAs' : 'Hub de IAs'}
            </button>
            <button type="button" style={styles.btnGhost} onClick={resetar}>
              Novo Pedido
            </button>
          </div>
        </header>

        {historicoAberto && (
          <section style={styles.card}>
            <div style={styles.historyHeaderRow}>
              <div>
                <h2 style={styles.sectionTitle}>Histórico Local (SQLite)</h2>
                <p style={styles.helpText}>
                  Seus prompts salvos ficam armazenados localmente no seu computador.
                </p>
              </div>
              {historico.length > 0 && (
                <div>
                  {!confirmarLimpar ? (
                    <button
                      type="button"
                      style={styles.btnDanger}
                      onClick={() => setConfirmarLimpar(true)}
                    >
                      Limpar tudo
                    </button>
                  ) : (
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <button
                        type="button"
                        style={styles.btnDanger}
                        onClick={limparTodoHistorico}
                      >
                        Confirmar apagar tudo
                      </button>
                      <button
                        type="button"
                        style={styles.btnGhost}
                        onClick={() => setConfirmarLimpar(false)}
                      >
                        Cancelar
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                style={styles.input}
                placeholder="Buscar por objetivo, tecnologia ou prompt..."
                value={buscaHistorico}
                onChange={(e) => {
                  const val = e.target.value;
                  setBuscaHistorico(val);
                  carregarHistorico(val);
                }}
              />
              {buscaHistorico && (
                <button
                  type="button"
                  style={styles.btnGhost}
                  onClick={() => {
                    setBuscaHistorico('');
                    carregarHistorico('');
                  }}
                >
                  Limpar
                </button>
              )}
            </div>

            {carregandoHistorico ? (
              <p style={styles.helpText}>Carregando histórico...</p>
            ) : historico.length === 0 ? (
              <p style={styles.helpText}>
                Nenhum prompt salvo ainda. Gere um prompt para ele aparecer aqui automaticamente.
              </p>
            ) : (
              <div style={styles.historyList}>
                {historico.map((item) => (
                  <div key={item.id} style={styles.historyItem}>
                    <div style={styles.historyItemTop}>
                      <span style={styles.historyTag}>{item.categoria.toUpperCase()}</span>
                      <span style={styles.historyMeta}>
                        ~{item.tokens_estimados} tokens • {item.gerado_por}
                      </span>
                    </div>
                    <div style={styles.historyObjective}>{item.objetivo}</div>
                    <div style={styles.historyActions}>
                      <button
                        type="button"
                        style={styles.btnSecondary}
                        onClick={() => reabrirItemHistorico(item)}
                      >
                        Reabrir e editar
                      </button>
                      <button
                        type="button"
                        style={styles.btnGhost}
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(item.prompt_final);
                            setCopiadoTexto('Prompt do histórico copiado!');
                          } catch {
                            setCopiadoTexto('Não foi possível copiar automaticamente.');
                          }
                        }}
                      >
                        Copiar
                      </button>
                      <button
                        type="button"
                        style={styles.btnDanger}
                        onClick={() => removerItemHistorico(item.id)}
                      >
                        Apagar
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {hubAberto && (
          <section style={styles.card}>
            <h2 style={styles.sectionTitle}>Hub de IAs (CLI Local, API Key ou Servidor Local)</h2>
            <p style={styles.helpText}>
              Use suas ferramentas CLI já autenticadas na máquina (como Claude ou Gemini/Antigravity)
              ou configure uma API / servidor local.
            </p>

            <div style={styles.hubGrid}>
              <div>
                <label style={styles.magicLabel}>Provedor / Ferramenta</label>
                <select
                  style={styles.select}
                  value={providerId}
                  onChange={(e) => selecionarProvedor(e.target.value)}
                >
                  {provedores.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label style={styles.magicLabel}>Modelo</label>
                <input
                  type="text"
                  style={styles.input}
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder={providerSelecionado?.modelo_padrao || 'ex: sonnet'}
                />
              </div>
            </div>

            {modoAuth === 'local_cli' && (
              <div style={styles.modeBox}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>
                  CLI Local:{' '}
                  {ferramentaLocalAtual?.installed
                    ? `Detectado (${ferramentaLocalAtual.command})`
                    : `Comando ${providerSelecionado?.cli_command || ''} não encontrado no PATH`}
                </div>
                <p style={styles.helpText}>
                  {providerSelecionado?.dica ||
                    'Usa a sessão já autenticada na sua máquina, sem colar chave de API.'}
                </p>
              </div>
            )}

            {modoAuth === 'api_key' && (
              <div style={styles.modeBox}>
                <label style={styles.magicLabel}>Chave de API (armazenada apenas no navegador)</label>
                <input
                  type="password"
                  style={styles.input}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Cole sua API Key aqui"
                />
                {providerSelecionado?.dica && <p style={styles.helpText}>{providerSelecionado.dica}</p>}
              </div>
            )}

            {modoAuth === 'local_server' && (
              <div style={styles.modeBox}>
                <label style={styles.magicLabel}>URL do Servidor Local</label>
                <input
                  type="text"
                  style={styles.input}
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="http://127.0.0.1:11434"
                />
              </div>
            )}

            <div style={styles.chipsRow}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
                <input
                  type="checkbox"
                  checked={otimizarComIa}
                  onChange={(e) => setOtimizarComIa(e.target.checked)}
                />
                Otimizar prompt final usando a IA selecionada
              </label>
            </div>

            <div style={styles.actionBar}>
              <button
                type="button"
                style={styles.btnSecondary}
                onClick={testarConexaoIa}
                disabled={testandoConexao}
              >
                {testandoConexao ? 'Testando...' : 'Testar Conexão'}
              </button>
            </div>

            {statusConexao && <div style={styles.statusMsg}>{statusConexao}</div>}
          </section>
        )}

        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>Passo 0 — Escolha o tipo de projeto ou deixe a IA identificar</h2>
          <p style={styles.helpText}>
            A categoria ajusta os exemplos e perguntas. Se preferir, escreva sua ideia livre abaixo e
            clique em <strong>Estruturar com IA</strong>.
          </p>

          <div style={styles.catGrid}>
            {CATEGORIES.map((cat) => {
              const ativa = cat.id === categoria;
              return (
                <button
                  key={cat.id}
                  type="button"
                  style={{ ...styles.catBtn, ...(ativa ? styles.catBtnActive : {}) }}
                  onClick={() => {
                    setCategoria(cat.id);
                    setRevisao(null);
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '4px' }}>
                    {cat.label}
                  </div>
                  <div style={{ fontSize: '12px', opacity: 0.85, lineHeight: 1.35 }}>{cat.desc}</div>
                </button>
              );
            })}
          </div>

          <div style={styles.magicBox}>
            <label htmlFor="intencao-livre" style={styles.magicLabel}>
              Não sabe por onde começar? Conte sua ideia em linguagem natural:
            </label>
            <textarea
              id="intencao-livre"
              rows={2}
              style={styles.textarea}
              placeholder="Ex: Quero um script em Python que organize faturas em PDF por mês e avise se faltar algum arquivo..."
              value={intencaoLivre}
              onChange={(e) => setIntencaoLivre(e.target.value)}
            />
            <div style={{ marginTop: '10px', display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
              <button
                type="button"
                style={styles.btnSecondary}
                onClick={analisarIntencaoLivre}
                disabled={analisandoIntencao}
              >
                {analisandoIntencao ? 'Analisando ideia...' : 'Estruturar com IA'}
              </button>
              {analiseInfo && (
                <span style={{ fontSize: '12px', color: '#86efac' }}>
                  Sugestão: <strong>{analiseInfo.categoria_sugerida}</strong> ({analiseInfo.motivo})
                </span>
              )}
            </div>
          </div>
        </section>

        <section style={styles.card}>
          <div style={styles.progressWrap}>
            <div style={styles.progressHeader}>
              <span>
                <strong>Progresso do pedido:</strong> {totalConcluidas} de {STEP_META.length} etapas preenchidas
              </span>
              <span style={{ color: '#d4af37', fontWeight: 700 }}>{progressoPct}%</span>
            </div>
            <div style={styles.progressTrack}>
              <div style={{ ...styles.progressFill, width: `${progressoPct}%` }} />
            </div>
          </div>

          <div style={styles.stepper}>
            {STEP_META.map((s) => {
              const ativa = s.num === etapa;
              const preenchida = etapasPreenchidas[s.num - 1];
              return (
                <button
                  key={s.num}
                  type="button"
                  style={{
                    ...styles.stepPill,
                    ...(preenchida && !ativa ? styles.stepPillDone : {}),
                    ...(ativa ? styles.stepPillActive : {}),
                  }}
                  onClick={() => setEtapa(s.num)}
                >
                  {s.num}. {s.key === 'tratamento_erros' ? 'Erros' : s.key.charAt(0).toUpperCase() + s.key.slice(1)}
                  {preenchida ? ' ✓' : ''}
                </button>
              );
            })}
          </div>

          <h2 style={styles.sectionTitle}>{etapaAtualMeta.titulo}</h2>
          <p style={styles.helpText}>{etapaAtualMeta.ajuda}</p>

          {renderCampoEtapa()}

          <div style={styles.navRow}>
            <button
              type="button"
              style={styles.btnGhost}
              disabled={etapa <= 1}
              onClick={() => setEtapa((e) => Math.max(1, e - 1))}
            >
              ← Anterior
            </button>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>
              Etapa {etapa} de {STEP_META.length}
            </span>
            <button
              type="button"
              style={styles.btnSecondary}
              disabled={etapa >= STEP_META.length}
              onClick={() => setEtapa((e) => Math.min(STEP_META.length, e + 1))}
            >
              Próxima →
            </button>
          </div>
        </section>

        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>Revisão e Geração do Prompt</h2>
          <p style={styles.helpText}>
            Revise a clareza do pedido antes de gerar ou gere direto o prompt compacto e pronto para colar na IA.
          </p>

          <div style={styles.actionBar}>
            <button
              type="button"
              style={styles.btnSecondary}
              onClick={handleRevisar}
              disabled={carregando !== null}
            >
              {carregando === 'revisar' ? 'Revisando...' : '1. Revisar Clareza'}
            </button>
            <button
              type="button"
              style={styles.btnPrimary}
              onClick={handleGerar}
              disabled={carregando !== null}
            >
              {carregando === 'gerar' ? 'Gerando...' : '2. Gerar Prompt Limpo'}
            </button>
          </div>

          {erro && <div style={styles.alertBox}>{erro}</div>}

          {revisao && (
            <div
              style={{
                marginTop: '20px',
                padding: '16px',
                borderRadius: '8px',
                backgroundColor: revisao.aprovado ? '#0d261c' : '#261e0d',
                border: `1px solid ${revisao.aprovado ? '#15803d' : '#b45309'}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ fontWeight: 700, color: revisao.aprovado ? '#4ade80' : '#fbbf24' }}>
                  Revisão do Pedido — Score: {revisao.score_qualidade}/100
                </div>
                {revisao.revisado_por && (
                  <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                    Revisor: {revisao.revisado_por}
                  </span>
                )}
              </div>
              {revisao.aprovado ? (
                <p style={{ margin: '8px 0 0', fontSize: '14px', color: '#bbf7d0' }}>
                  Pedido sólido e completo. Pode gerar o prompt final.
                </p>
              ) : (
                <ul style={{ margin: '8px 0 0', paddingLeft: '18px', fontSize: '14px', color: '#fde68a' }}>
                  {revisao.pendencias.map((p, idx) => (
                    <li key={idx}>{p}</li>
                  ))}
                </ul>
              )}
              {revisao.dica_extra && (
                <p
                  style={{
                    margin: '10px 0 0',
                    fontSize: '13.5px',
                    color: '#e2e8f0',
                    borderTop: '1px solid #334155',
                    paddingTop: '8px',
                  }}
                >
                  <strong>Dica extra:</strong> {revisao.dica_extra}
                </p>
              )}
            </div>
          )}

          {resultado && (
            <div
              style={{
                marginTop: '24px',
                padding: '20px',
                backgroundColor: '#050811',
                border: '1px solid #d4af37',
                borderRadius: '10px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '10px',
                  marginBottom: '12px',
                }}
              >
                <div>
                  <strong style={{ color: '#d4af37' }}>
                    Prompt Pronto (~{resultado.tokens_estimados} tokens)
                  </strong>
                  <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                    {resultado.gerado_por}
                    {resultado.historico_id ? ' • Salvo no Histórico' : ''}
                  </div>
                </div>
                <button type="button" style={styles.btnPrimary} onClick={copiarPrompt}>
                  Copiar Prompt
                </button>
              </div>

              <pre
                style={{
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                  fontSize: '13.5px',
                  color: '#e2e8f0',
                  lineHeight: 1.55,
                }}
              >
                {resultado.prompt_final}
              </pre>

              <div
                style={{
                  marginTop: '16px',
                  paddingTop: '14px',
                  borderTop: '1px solid #1e293b',
                }}
              >
                <div style={{ fontSize: '12.5px', color: '#94a3b8', marginBottom: '8px' }}>
                  Ou copie e abra direto na sua IA favorita:
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {BRANDS.filter((b) => b.chatUrl).map((b) => (
                    <button
                      key={b.id}
                      type="button"
                      style={{ ...styles.btnSecondary, borderColor: b.cor, color: b.cor }}
                      onClick={() => copiarAbrirEm(b.nome, b.chatUrl)}
                    >
                      Abrir no {b.nome}
                    </button>
                  ))}
                </div>
                {copiadoTexto && (
                  <div style={{ marginTop: '8px', fontSize: '13px', color: '#4ade80', fontWeight: 600 }}>
                    {copiadoTexto}
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
