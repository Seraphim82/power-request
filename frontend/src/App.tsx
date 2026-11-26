import { useEffect, useRef, useState } from 'react';
import {
  BRANDS,
  CATEGORIES,
  CONTEXTO_ATIVO_KEY,
  LEMBRAR_CHAVE_KEY,
  PASTA_TERMINAL_KEY,
  PASTA_TERMINAL_PADRAO,
  CONTEXTO_MAX,
  ESTADO_IA_META,
  STEP_META,
  STACK_AUTO,
  STORAGE_KEY,
  type AIConfigSalva,
  type AnaliseIntencao,
  type CategoriaConfig,
  type CategoriaId,
  type EstadoIa,
  type ItemHistorico,
  type Rodada,
  type LocalToolStatus,
  type ProviderInfo,
  type RevisaoPedido,
  type ResultadoPrompt,
} from './constants';
import { montarLinkIa } from './abrirNaIa';
import {
  LIMITE_ENVIO_PADRAO,
  MARCA_RESPOSTA_CORTADA,
  recortarRodadas,
  respostaFoiCortada,
  tamanhoDoPrompt,
} from './tamanhoEnvio';
import { styles } from './styles';

const API_BASE = window.location.port === '5173' ? 'http://127.0.0.1:8000' : '';

function carregarConfigSalva(): AIConfigSalva {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        provider: parsed.provider || 'claude_cli',
        // A chave só é restaurada se a pessoa optou por lembrá-la neste navegador.
        apiKey: localStorage.getItem(LEMBRAR_CHAVE_KEY) === '1' ? parsed.apiKey || '' : '',
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
  const [lembrarChave, setLembrarChave] = useState<boolean>(() => {
    try {
      return localStorage.getItem(LEMBRAR_CHAVE_KEY) === '1';
    } catch {
      return false;
    }
  });
  const [model, setModel] = useState<string>(configInicial.model);
  const [alias] = useState<string>(configInicial.alias);
  const [baseUrl, setBaseUrl] = useState<string>(configInicial.baseUrl);
  const [otimizarComIa, setOtimizarComIa] = useState<boolean>(configInicial.otimizarComIa);
  const [statusConexao, setStatusConexao] = useState<string>('');
  const [testandoConexao, setTestandoConexao] = useState<boolean>(false);
  const [estadoIa, setEstadoIa] = useState<EstadoIa>('desconhecido');
  const [detalheIa, setDetalheIa] = useState<string>('');
  const verificacaoAtual = useRef<number>(0);

  const [enviando, setEnviando] = useState<boolean>(false);
  const [segundosEnvio, setSegundosEnvio] = useState<number>(0);
  const [respostaIa, setRespostaIa] = useState<{ texto: string; origem: string } | null>(null);
  const [erroEnvio, setErroEnvio] = useState<string>('');
  const [respostaCopiada, setRespostaCopiada] = useState<string>('');
  // Sequenciar: rodadas já respondidas (a 1ª tem pedido vazio = o prompt original).
  const [rodadas, setRodadas] = useState<Rodada[]>([]);
  const [proximoPedido, setProximoPedido] = useState<string>('');
  const [infoSequencia, setInfoSequencia] = useState<string>('');
  const envioAtual = useRef<number>(0);
  const [limiteEnvio, setLimiteEnvio] = useState<number>(LIMITE_ENVIO_PADRAO);

  const [pastaTerminal, setPastaTerminal] = useState<string>(() => {
    try {
      return localStorage.getItem(PASTA_TERMINAL_KEY) || PASTA_TERMINAL_PADRAO;
    } catch {
      return PASTA_TERMINAL_PADRAO;
    }
  });
  const [abrindoTerminal, setAbrindoTerminal] = useState<boolean>(false);
  const [avisoTerminal, setAvisoTerminal] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(null);

  // Envio automático pelo site da IA (experimental, desligado por padrão)
  const [autoAtivado, setAutoAtivado] = useState<boolean>(false);
  const [autoPerfis, setAutoPerfis] = useState<{ suportado: boolean; perfis: { chave: string; nome: string }[]; nao_validados?: string[]; navegadores: string[] } | null>(null);
  const [autoIa, setAutoIa] = useState<string>('claude');
  const [autoNavegador, setAutoNavegador] = useState<string>('');
  const [contagemAuto, setContagemAuto] = useState<number | null>(null);
  const [autoEnviando, setAutoEnviando] = useState<boolean>(false);
  const [autoAviso, setAutoAviso] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(null);
  const [autoTeste, setAutoTeste] = useState<{ ok: boolean; itens: { item: string; ok: boolean; detalhe: string }[] } | null>(null);
  const [autoTestando, setAutoTestando] = useState<boolean>(false);

  const [contextoAberto, setContextoAberto] = useState<boolean>(false);
  const [contextoFixo, setContextoFixo] = useState<string>('');
  const [contextoSalvo, setContextoSalvo] = useState<string>('');
  const [usarContexto, setUsarContexto] = useState<boolean>(() => {
    try {
      return localStorage.getItem(CONTEXTO_ATIVO_KEY) !== '0';
    } catch {
      return true;
    }
  });
  const [salvandoContexto, setSalvandoContexto] = useState<boolean>(false);
  const [statusContexto, setStatusContexto] = useState<string>('');

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
    fetch(`${API_BASE}/api/health`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (Number(d?.limite_envio) > 0) setLimiteEnvio(Number(d.limite_envio));
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    carregarHistorico();

    fetch(`${API_BASE}/api/hub/providers`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (Array.isArray(data?.providers)) {
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

    fetch(`${API_BASE}/api/contexto`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (typeof data?.contexto === 'string') {
          setContextoFixo(data.contexto);
          setContextoSalvo(data.contexto);
        }
      })
      .catch(() => {});

    fetch(`${API_BASE}/api/hub/local-tools`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (Array.isArray(data?.tools)) setFerramentasLocais(data.tools);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    try {
      const payload: AIConfigSalva = {
        provider: providerId,
        // Por padrão a chave fica só na memória; guardar em texto claro exige opt-in explícito.
        apiKey: lembrarChave ? apiKey : '',
        model,
        alias,
        baseUrl,
        otimizarComIa,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
      localStorage.setItem(LEMBRAR_CHAVE_KEY, lembrarChave ? '1' : '0');
    } catch {
      // ignora erro de storage
    }
  }, [providerId, apiKey, lembrarChave, model, alias, baseUrl, otimizarComIa]);

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

  const verificarConexaoIa = async () => {
    const id = ++verificacaoAtual.current;
    setTestandoConexao(true);
    setEstadoIa('verificando');
    setDetalheIa('');
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
      if (id !== verificacaoAtual.current) return;
      if (!res.ok) {
        const motivo = String(data.detail || 'Verifique os dados.');
        setStatusConexao(`Falha: ${motivo}`);
        setEstadoIa('offline');
        setDetalheIa(motivo);
      } else {
        setStatusConexao(`Conectado: ${data.mensagem}`);
        setEstadoIa('online');
        setDetalheIa(String(data.mensagem || ''));
      }
    } catch {
      if (id !== verificacaoAtual.current) return;
      const motivo = 'Não foi possível conectar ao backend local.';
      setStatusConexao(motivo);
      setEstadoIa('offline');
      setDetalheIa(motivo);
    } finally {
      if (id === verificacaoAtual.current) setTestandoConexao(false);
    }
  };

  const testarConexaoIa = verificarConexaoIa;

  // Teste automático só para IAs locais (gratuitas). Com chave de API o teste é manual,
  // para não gastar cota sem você pedir. Qualquer mudança de configuração zera o status.
  useEffect(() => {
    verificacaoAtual.current += 1;
    setTestandoConexao(false);
    setEstadoIa('desconhecido');
    setDetalheIa('');

    const modo = providerSelecionado?.auth_mode;
    if (modo === 'local_cli') {
      if (ferramentasLocais.length === 0) return;
      if (!ferramentaLocalAtual?.installed) {
        setEstadoIa('offline');
        setDetalheIa('Comando não encontrado neste computador.');
        return;
      }
    } else if (modo !== 'local_server') {
      return;
    }
    const timer = setTimeout(verificarConexaoIa, 600);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [providerId, model, baseUrl, apiKey, providerSelecionado?.auth_mode, ferramentaLocalAtual?.installed, ferramentasLocais.length]);

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
        if (data.rascunho.objetivo) setObjetivo(data.rascunho.objetivo);
        if (data.rascunho.stack) setStack(data.rascunho.stack);
        if (data.rascunho.entrada) setEntrada(data.rascunho.entrada);
        if (data.rascunho.saida) setSaida(data.rascunho.saida);
        if (Array.isArray(data.rascunho.regras) && data.rascunho.regras.length > 0) {
          setRegras(data.rascunho.regras);
        }
        if (data.rascunho.tratamento_erros) setTratamentoErros(data.rascunho.tratamento_erros);
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

  useEffect(() => {
    if (!enviando) return;
    const timer = setInterval(() => setSegundosEnvio((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [enviando]);

  // Invalida qualquer envio em andamento (ex: ao iniciar novo pedido) para que uma
  // resposta atrasada não apareça junto de outro prompt.
  const limparEnvio = () => {
    envioAtual.current += 1;
    setAvisoTerminal(null);
    setEnviando(false);
    setSegundosEnvio(0);
    setRespostaIa(null);
    setErroEnvio('');
    setRespostaCopiada('');
    setRodadas([]);
    setProximoPedido('');
    setInfoSequencia('');
  };

  const sequenciar = async () => {
    const novo = proximoPedido.trim();
    if (!resultado?.prompt_final || enviando || !novo || rodadas.length === 0) return;
    const cfg = montarAiConfigPayload();
    if (!cfg) {
      setErroEnvio('Informe a chave desta IA no Hub de IAs antes de enviar.');
      setHubAberto(true);
      return;
    }
    const id = ++envioAtual.current;
    setEnviando(true);
    setSegundosEnvio(0);
    setErroEnvio('');
    setRespostaCopiada('');
    const { enviadas, anteriores } = recortarRodadas(rodadas);
    try {
      const res = await fetch(`${API_BASE}/api/sequenciar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt_base: resultado.prompt_final,
          rodadas: enviadas.map((r) => ({ pedido: r.pedido, resposta: r.resposta })),
          rodadas_anteriores: anteriores,
          novo_pedido: novo,
          ai_config: cfg,
          ...(resultado.historico_id ? { pedido_id: resultado.historico_id } : {}),
        }),
      });
      const data = await res.json();
      if (id !== envioAtual.current) return;
      if (!res.ok) {
        setErroEnvio(String(data.detail || 'Não foi possível sequenciar.'));
      } else {
        const origem = `${data.alias} (${data.model})`;
        const texto = String(data.resposta || '') + (data.cortada ? MARCA_RESPOSTA_CORTADA : '');
        setRespostaIa({ texto, origem });
        setRodadas((prev) => [...prev, { pedido: novo, resposta: texto, origem }]);
        setProximoPedido('');
        const omitidas = Number(data.rodadas_omitidas || 0);
        const cortadas: number[] = Array.isArray(data.rodadas_cortadas) ? data.rodadas_cortadas : [];
        setInfoSequencia(
          `Enviei o pedido original + ${data.rodadas_enviadas} resposta(s) anterior(es) + seu novo pedido (~${data.tokens_estimados} tokens).` +
            (omitidas ? ` ${omitidas} rodada(s) mais antiga(s) ficaram de fora.` : '') +
            (cortadas.length
              ? ` Atenção: a resposta da(s) rodada(s) ${cortadas.join(', ')} foi enviada sem o meio, por falta de espaço.`
              : ''),
        );
      }
    } catch {
      if (id !== envioAtual.current) return;
      setErroEnvio('Não foi possível conectar ao servidor local.');
    } finally {
      if (id === envioAtual.current) setEnviando(false);
    }
  };

  const enviarParaIa = async () => {
    if (!resultado?.prompt_final || enviando) return;
    const cfg = montarAiConfigPayload();
    if (!cfg) {
      setErroEnvio('Informe a chave desta IA no Hub de IAs antes de enviar.');
      setHubAberto(true);
      return;
    }
    const id = ++envioAtual.current;
    setEnviando(true);
    setSegundosEnvio(0);
    setErroEnvio('');
    setRespostaIa(null);
    setRespostaCopiada('');
    try {
      const res = await fetch(`${API_BASE}/api/enviar-prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: resultado.prompt_final,
          ai_config: cfg,
          ...(resultado.historico_id ? { pedido_id: resultado.historico_id } : {}),
        }),
      });
      const data = await res.json();
      if (id !== envioAtual.current) return;
      if (!res.ok) {
        setErroEnvio(String(data.detail || 'Não foi possível enviar o prompt.'));
      } else {
        const origem = `${data.alias} (${data.model})`;
        const texto = String(data.resposta || '') + (data.cortada ? MARCA_RESPOSTA_CORTADA : '');
        setRespostaIa({ texto, origem });
        setRodadas([{ pedido: '', resposta: texto, origem }]);
        setProximoPedido('');
        setInfoSequencia('');
      }
    } catch {
      if (id !== envioAtual.current) return;
      setErroEnvio('Não foi possível conectar ao servidor local.');
    } finally {
      if (id === envioAtual.current) setEnviando(false);
    }
  };

  const abrirNoTerminal = async () => {
    if (!resultado?.prompt_final || abrindoTerminal) return;
    const cfg = montarAiConfigPayload();
    if (!cfg) return;
    setAbrindoTerminal(true);
    setAvisoTerminal(null);
    try {
      localStorage.setItem(PASTA_TERMINAL_KEY, pastaTerminal);
    } catch {
      // ignora erro de storage
    }
    try {
      const res = await fetch(`${API_BASE}/api/abrir-terminal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: resultado.prompt_final, pasta: pastaTerminal, ai_config: cfg }),
      });
      const data = await res.json();
      if (!res.ok) {
        setAvisoTerminal({ tipo: 'erro', texto: String(data.detail || 'Não foi possível abrir o Terminal.') });
      } else {
        setAvisoTerminal({
          tipo: 'ok',
          texto:
            data.modo === 'argumento'
              ? `Terminal aberto em ${data.pasta}. A IA já começou com o seu prompt.`
              : `Terminal aberto em ${data.pasta}. O prompt foi copiado: cole com ⌘V quando a IA abrir.`,
        });
      }
    } catch {
      setAvisoTerminal({ tipo: 'erro', texto: 'Não foi possível conectar ao servidor local.' });
    } finally {
      setAbrindoTerminal(false);
    }
  };

  useEffect(() => {
    let ativo = true;
    fetch(`${API_BASE}/api/envio-automatico/perfis`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (ativo && d) setAutoPerfis(d);
      })
      .catch(() => undefined);
    return () => {
      ativo = false;
    };
  }, []);

  const dispararEnvioAuto = async () => {
    if (!resultado?.prompt_final) return;
    setAutoEnviando(true);
    setAutoAviso(null);
    try {
      const res = await fetch(`${API_BASE}/api/envio-automatico`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: resultado.prompt_final,
          ia: autoIa,
          navegador: autoNavegador || null,
          aviso_aceito: true,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setAutoAviso({ tipo: 'erro', texto: String(data.detail || 'Não foi possível enviar pelo site.') });
      } else {
        setAutoAviso({ tipo: data.status === 'confirmado' ? 'ok' : 'erro', texto: String(data.mensagem || '') });
      }
    } catch {
      setAutoAviso({ tipo: 'erro', texto: 'Não foi possível conectar ao servidor local.' });
    } finally {
      setAutoEnviando(false);
    }
  };

  // Contagem regressiva de 3s antes de mexer no teclado; dá tempo de Cancelar.
  useEffect(() => {
    if (contagemAuto === null) return;
    if (contagemAuto <= 0) {
      setContagemAuto(null);
      void dispararEnvioAuto();
      return;
    }
    const t = window.setTimeout(() => setContagemAuto((c) => (c === null ? null : c - 1)), 1000);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contagemAuto]);

  const testarAutomacao = async () => {
    if (autoTestando) return;
    setAutoTestando(true);
    setAutoTeste(null);
    try {
      const res = await fetch(`${API_BASE}/api/envio-automatico/testar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ navegador: autoNavegador || null }),
      });
      const data = await res.json();
      if (res.ok) {
        setAutoTeste(data);
      } else {
        setAutoTeste({ ok: false, itens: [{ item: 'Teste', ok: false, detalhe: String(data.detail || 'Falhou.') }] });
      }
    } catch {
      setAutoTeste({ ok: false, itens: [{ item: 'Servidor', ok: false, detalhe: 'Não foi possível conectar ao servidor local.' }] });
    } finally {
      setAutoTestando(false);
    }
  };

  const copiarResposta = async () => {
    if (!respostaIa?.texto) return;
    try {
      await navigator.clipboard.writeText(respostaIa.texto);
      setRespostaCopiada('Resposta copiada.');
    } catch {
      setRespostaCopiada('Selecione e copie o texto acima.');
    }
  };

  const alternarUsoContexto = (ativo: boolean) => {
    setUsarContexto(ativo);
    try {
      localStorage.setItem(CONTEXTO_ATIVO_KEY, ativo ? '1' : '0');
    } catch {
      // ignora erro de storage
    }
  };

  const salvarContexto = async () => {
    setSalvandoContexto(true);
    setStatusContexto('');
    try {
      const res = await fetch(`${API_BASE}/api/contexto`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contexto: contextoFixo }),
      });
      const data = await res.json();
      if (!res.ok) {
        setStatusContexto(`Não foi possível salvar: ${data.detail || 'verifique o texto.'}`);
      } else {
        setContextoFixo(data.contexto);
        setContextoSalvo(data.contexto);
        setStatusContexto('Contexto salvo.');
      }
    } catch {
      setStatusContexto('Não foi possível conectar ao backend local.');
    } finally {
      setSalvandoContexto(false);
    }
  };

  const contextoAtivoNoPedido = usarContexto && contextoSalvo.trim().length > 0;

  const payloadAtual = () => ({
    contexto_fixo: contextoAtivoNoPedido ? contextoSalvo : '',
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

  const validarCamposObrigatorios = (): boolean => {
    const faltando: { etapa: number; nome: string }[] = [];
    if (!objetivo.trim()) faltando.push({ etapa: 1, nome: 'o que você quer criar' });
    if (!stack.trim()) faltando.push({ etapa: 2, nome: 'a tecnologia (ou "Deixar a IA escolher")' });
    if (!entrada.trim()) faltando.push({ etapa: 3, nome: 'o que entra no sistema' });
    if (!saida.trim()) faltando.push({ etapa: 4, nome: 'o que deve sair' });
    if (regras.length === 0) faltando.push({ etapa: 5, nome: 'pelo menos 1 regra' });
    if (faltando.length === 0) return true;
    setErro(`Falta preencher: ${faltando.map((f) => f.nome).join('; ')}.`);
    setEtapa(faltando[0].etapa);
    return false;
  };

  const handleRevisar = async () => {
    setErro('');
    if (!validarCamposObrigatorios()) return;
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
    if (!validarCamposObrigatorios()) return;
    limparEnvio();
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
    limparEnvio();
    const idItem = item.id;
    fetch(`${API_BASE}/api/historico/${idItem}/rodadas`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        const lista: Rodada[] = Array.isArray(d?.rodadas)
          ? d.rodadas.map((r: { pedido_texto: string; resposta: string; origem: string }) => ({
              pedido: r.pedido_texto || '',
              resposta: r.resposta || '',
              origem: r.origem || 'IA',
            }))
          : [];
        if (lista.length === 0) return;
        setRodadas(lista);
        const ultima = lista[lista.length - 1];
        setRespostaIa({ texto: ultima.resposta, origem: ultima.origem });
      })
      .catch(() => undefined);
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

  const copiarAbrirEm = async (marca: (typeof BRANDS)[number]) => {
    if (!resultado?.prompt_final) return;
    // Calcula o link ANTES de qualquer espera: o navegador só deixa abrir a aba logo após o clique.
    const link = montarLinkIa(marca, resultado.prompt_final);
    const atalhoColar = /Mac/i.test(navigator.platform) ? '⌘V' : 'Ctrl+V';
    const aba = window.open(link.url, '_blank', 'noopener,noreferrer');
    let copiou = true;
    try {
      // Cópia de segurança: se o site não preencher sozinho, é só colar.
      await navigator.clipboard.writeText(resultado.prompt_final);
    } catch {
      copiou = false;
    }
    if (!aba) {
      setCopiadoTexto(`O navegador bloqueou a nova aba. Abra ${marca.nome} e cole o prompt (${atalhoColar}).`);
    } else if (link.preenchido) {
      setCopiadoTexto(`Abrindo ${marca.nome} com o prompt já preenchido. Confira e aperte Enter. Se a caixa vier vazia, cole (${atalhoColar}).`);
    } else if (copiou) {
      setCopiadoTexto(`Prompt copiado! Em ${marca.nome}, clique na caixa de texto, cole (${atalhoColar}) e aperte Enter.`);
    } else {
      setCopiadoTexto(`Abrindo ${marca.nome} — copie o prompt do quadro acima e cole na caixa de texto.`);
    }
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
    limparEnvio();
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
              {[...catConfig.sugestoes.stack, STACK_AUTO].map((s) => (
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
          <img
            src="/logo.svg"
            alt="Logo Power Request"
            width={76}
            height={76}
            style={{ flexShrink: 0, borderRadius: '18px' }}
          />
          <div>
            <div style={styles.badge}>POWER REQUEST • ENGENHARIA DE PROMPT GUIADA</div>
            <h1 style={styles.title}>Power Request</h1>
            <p style={styles.subtitle}>
              Transforme uma ideia simples em um pedido claro, revisado e econômico em tokens —
              sem precisar saber programar ou escrever prompts complexos.
            </p>
          </div>
          </div>
          <div style={styles.headerActions}>
            {providerSelecionado && (
              <button
                type="button"
                className="ia-status"
                style={styles.iaPill}
                role="status"
                aria-live="polite"
                title={`${providerSelecionado.nome} (${model || providerSelecionado.modelo_padrao}) — ${ESTADO_IA_META[estadoIa].rotulo}${detalheIa ? `: ${detalheIa}` : ''}`}
                onClick={() => setHubAberto(true)}
              >
                <span
                  className={`ia-dot-${estadoIa}`}
                  style={{ ...styles.iaDot, backgroundColor: ESTADO_IA_META[estadoIa].cor }}
                />
                <span style={styles.iaPillName}>{providerSelecionado.nome}</span>
                <span style={{ color: ESTADO_IA_META[estadoIa].cor, fontWeight: 700 }}>
                  {ESTADO_IA_META[estadoIa].rotulo}
                </span>
              </button>
            )}
            <button
              type="button"
              className="btn-header"
              style={{ ...styles.btnHeader, ...(historicoAberto ? styles.btnHeaderActive : {}) }}
              onClick={() => {
                const proximo = !historicoAberto;
                setHistoricoAberto(proximo);
                if (proximo) carregarHistorico(buscaHistorico);
              }}
            >
              {historicoAberto ? 'Fechar Histórico' : `Histórico (${historico.length})`}
            </button>
            <button
              type="button"
              className="btn-header"
              style={{ ...styles.btnHeader, ...(hubAberto ? styles.btnHeaderActive : {}) }}
              onClick={() => setHubAberto(!hubAberto)}
            >
              {hubAberto ? 'Fechar Hub de IAs' : 'Hub de IAs'}
            </button>
            <button
              type="button"
              className="btn-header"
              style={{ ...styles.btnHeader, ...(contextoAberto ? styles.btnHeaderActive : {}) }}
              onClick={() => setContextoAberto(!contextoAberto)}
              title={contextoAtivoNoPedido ? 'Contexto fixo ligado: entra em todos os pedidos' : 'Contexto fixo desligado ou vazio'}
            >
              {contextoAberto ? 'Fechar Contexto' : 'Contexto fixo'}
              {contextoAtivoNoPedido && !contextoAberto ? ' ●' : ''}
            </button>
            <button type="button" className="btn-header" style={styles.btnHeader} onClick={resetar}>
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
                <label style={styles.magicLabel}>Chave de API</label>
                <input
                  type="password"
                  style={styles.input}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Cole sua API Key aqui"
                  autoComplete="off"
                />
                <label style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', marginTop: '10px', fontSize: '13px', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={lembrarChave}
                    onChange={(e) => setLembrarChave(e.target.checked)}
                    style={{ marginTop: '3px' }}
                  />
                  <span>
                    Lembrar esta chave neste navegador
                    <span style={{ display: 'block', color: '#94a3b8', fontSize: '12px' }}>
                      Desmarcado (recomendado): a chave fica só na memória e some ao recarregar a página.
                      Marcado: fica guardada <strong>sem criptografia</strong> neste navegador.
                    </span>
                  </span>
                </label>
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

        {contextoAberto && (
          <section style={styles.card}>
            <h2 style={styles.sectionTitle}>Contexto fixo — vale para todos os pedidos</h2>
            <p style={styles.helpText}>
              Escreva aqui o que deve ser igual em todos os seus projetos (stack padrão, idioma, estilo de
              código, testes). Ele entra no início de cada prompt gerado e também na revisão pela IA. Use só
              preferências estáveis: o histórico de cada projeto fica com o seu ai-memory.
            </p>
            <textarea
              rows={5}
              style={styles.textarea}
              maxLength={CONTEXTO_MAX}
              value={contextoFixo}
              onChange={(e) => {
                setContextoFixo(e.target.value);
                setStatusContexto('');
              }}
              placeholder={'Ex:\n- Interface sempre em português do Brasil\n- Stack padrão: Python + FastAPI e React + TypeScript\n- Código tipado, comentado e com testes automatizados'}
            />
            <div style={{ ...styles.actionBar, alignItems: 'center' }}>
              <button
                type="button"
                style={styles.btnSecondary}
                onClick={salvarContexto}
                disabled={salvandoContexto || contextoFixo === contextoSalvo}
              >
                {salvandoContexto ? 'Salvando...' : 'Salvar contexto'}
              </button>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
                <input
                  type="checkbox"
                  checked={usarContexto}
                  onChange={(e) => alternarUsoContexto(e.target.checked)}
                />
                Incluir nos pedidos
              </label>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                {contextoFixo.length}/{CONTEXTO_MAX}
                {contextoFixo !== contextoSalvo ? ' • alterações não salvas' : ''}
              </span>
            </div>
            {statusContexto && <div style={styles.statusMsg}>{statusContexto}</div>}
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
                    {resultado.aviso ? ` • ${resultado.aviso}` : ''}
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
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    style={{
                      ...styles.btnPrimary,
                      opacity: enviando || tamanhoDoPrompt(resultado.prompt_final) > limiteEnvio ? 0.5 : 1,
                    }}
                    onClick={enviarParaIa}
                    disabled={enviando || tamanhoDoPrompt(resultado.prompt_final) > limiteEnvio}
                  >
                    {enviando
                      ? `Enviando... ${segundosEnvio}s`
                      : `Enviar para ${providerSelecionado?.nome ?? 'a IA ativa'}`}
                  </button>
                  <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                    {modoAuth === 'api_key'
                      ? 'Usa a sua chave de API (consome a sua cota). A resposta aparece aqui.'
                      : 'Usa a IA já logada neste computador. A resposta aparece aqui.'}
                  </span>
                </div>

                {tamanhoDoPrompt(resultado.prompt_final) > limiteEnvio ? (
                  <div
                    role="status"
                    data-testid="tamanho-prompt"
                    style={{ marginTop: '8px', fontSize: '13px', color: '#fde68a', lineHeight: 1.5 }}
                  >
                    Prompt com {tamanhoDoPrompt(resultado.prompt_final).toLocaleString('pt-BR')} caracteres: passa do
                    limite de {limiteEnvio.toLocaleString('pt-BR')} do botão Enviar. Reduza o pedido (menos regras ou
                    textos menores) ou use <strong>Copiar Prompt</strong>
                    {modoAuth === 'local_cli' ? ' ou Abrir no Terminal' : ''}.
                  </div>
                ) : (
                  <div data-testid="tamanho-prompt" style={{ marginTop: '8px', fontSize: '12px', color: '#94a3b8' }}>
                    Tamanho: {tamanhoDoPrompt(resultado.prompt_final).toLocaleString('pt-BR')} de{' '}
                    {limiteEnvio.toLocaleString('pt-BR')} caracteres para o botão Enviar.
                  </div>
                )}

                {modoAuth === 'local_cli' && (
                  <div
                    style={{
                      marginTop: '14px',
                      padding: '12px 14px',
                      borderRadius: '12px',
                      border: '1px solid #1e293b',
                      backgroundColor: '#0b1220',
                    }}
                  >
                    <div style={{ fontSize: '13px', color: '#cbd5e1', marginBottom: '8px' }}>
                      <strong>Projeto grande?</strong> Abra no Terminal: a IA trabalha numa pasta sua, com
                      todas as ferramentas (cria arquivos e roda testes), sem limite de tamanho.
                    </div>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                      <input
                        aria-label="Pasta do projeto"
                        style={{ ...styles.input, flex: '1 1 240px', minWidth: 0 }}
                        value={pastaTerminal}
                        onChange={(e) => setPastaTerminal(e.target.value)}
                        placeholder="Ex: Desktop/meu-projeto (dentro da sua pasta de usuário)"
                        maxLength={500}
                      />
                      <button
                        type="button"
                        style={{ ...styles.btnSecondary, opacity: abrindoTerminal ? 0.7 : 1 }}
                        onClick={abrirNoTerminal}
                        disabled={abrindoTerminal || !pastaTerminal.trim()}
                      >
                        {abrindoTerminal ? 'Abrindo...' : 'Abrir no Terminal'}
                      </button>
                    </div>
                    {avisoTerminal && (
                      <div
                        role={avisoTerminal.tipo === 'erro' ? 'alert' : 'status'}
                        data-testid="aviso-terminal"
                        style={{
                          marginTop: '10px',
                          fontSize: '13px',
                          color: avisoTerminal.tipo === 'erro' ? '#fecaca' : '#bbf7d0',
                        }}
                      >
                        {avisoTerminal.texto}
                      </div>
                    )}
                  </div>
                )}

                {autoPerfis && (
                  <div
                    data-testid="bloco-envio-automatico"
                    style={{
                      marginTop: '14px',
                      padding: '12px 14px',
                      borderRadius: '12px',
                      border: '1px solid #1e293b',
                      backgroundColor: '#0b1220',
                    }}
                  >
                    <label style={{ display: 'flex', gap: '8px', alignItems: 'center', fontSize: '13px', color: '#cbd5e1' }}>
                      <input
                        type="checkbox"
                        checked={autoAtivado}
                        onChange={(e) => {
                          setAutoAtivado(e.target.checked);
                          setContagemAuto(null);
                          setAutoAviso(null);
                        }}
                      />
                      <span>
                        <strong>Abrir no site da IA</strong> (experimental): o app abre o site, cola o prompt e envia.
                        A conversa fica no histórico da própria IA.
                      </span>
                    </label>

                    {autoAtivado && !autoPerfis.suportado && (
                      <div style={{ marginTop: '10px', fontSize: '13px', color: '#fde68a' }}>
                        Ainda não funciona neste sistema (só macOS). Use <strong>Copiar Prompt</strong> e cole no site.
                      </div>
                    )}

                    {autoAtivado && autoPerfis.suportado && (
                      <>
                        <div style={{ marginTop: '10px', fontSize: '12.5px', color: '#94a3b8', lineHeight: 1.5 }}>
                          O macOS vai pedir permissão de <strong>Acessibilidade</strong> (para o app apertar ⌘V e
                          Enter). Revise o prompt antes: ele pode ter dados de terceiros. Depois de clicar, aguarde
                          3 segundos e não mexa no teclado até terminar. Se não der para confirmar o envio, o texto
                          fica copiado.
                        </div>
                        <div style={{ marginTop: '10px', display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                          <select
                            aria-label="IA do site"
                            style={{ ...styles.input, flex: '0 1 160px', minWidth: 0 }}
                            value={autoIa}
                            onChange={(e) => setAutoIa(e.target.value)}
                          >
                            {autoPerfis.perfis.map((p) => (
                              <option key={p.chave} value={p.chave}>
                                {p.nome}
                                {autoPerfis.nao_validados?.includes(p.chave) ? ' (ainda não validado)' : ''}
                              </option>
                            ))}
                          </select>
                          <select
                            aria-label="Navegador"
                            style={{ ...styles.input, flex: '0 1 180px', minWidth: 0 }}
                            value={autoNavegador}
                            onChange={(e) => setAutoNavegador(e.target.value)}
                          >
                            <option value="">Navegador: automático</option>
                            {autoPerfis.navegadores.map((n) => (
                              <option key={n} value={n}>
                                {n}
                              </option>
                            ))}
                          </select>
                          {contagemAuto === null ? (
                            <button
                              type="button"
                              style={{ ...styles.btnSecondary, opacity: autoEnviando ? 0.7 : 1 }}
                              onClick={() => {
                                setAutoAviso(null);
                                setContagemAuto(3);
                              }}
                              disabled={autoEnviando || !autoIa}
                            >
                              {autoEnviando ? 'Enviando...' : 'Enviar pelo site'}
                            </button>
                          ) : (
                            <button type="button" style={styles.btnSecondary} onClick={() => setContagemAuto(null)}>
                              Cancelar ({contagemAuto})
                            </button>
                          )}
                          <button
                            type="button"
                            style={{ ...styles.btnSecondary, opacity: autoTestando ? 0.7 : 1 }}
                            onClick={testarAutomacao}
                            disabled={autoTestando || autoEnviando || contagemAuto !== null}
                          >
                            {autoTestando ? 'Testando...' : 'Testar automação'}
                          </button>
                        </div>
                      </>
                    )}

                    {autoAviso && (
                      <div
                        role={autoAviso.tipo === 'erro' ? 'alert' : 'status'}
                        data-testid="aviso-envio-automatico"
                        style={{ marginTop: '10px', fontSize: '13px', color: autoAviso.tipo === 'erro' ? '#fecaca' : '#bbf7d0' }}
                      >
                        {autoAviso.texto}
                      </div>
                    )}
                    {autoTeste && (
                      <ul data-testid="resultado-teste-automacao" style={{ margin: '10px 0 0', paddingLeft: '18px', fontSize: '13px' }}>
                        {autoTeste.itens.map((i) => (
                          <li key={i.item} style={{ color: i.ok ? '#bbf7d0' : '#fecaca' }}>
                            {i.ok ? '✓' : '✗'} {i.item}: {i.detalhe}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {erroEnvio && (
                  <div
                    role="alert"
                    style={{
                      marginTop: '12px',
                      padding: '10px 14px',
                      borderRadius: '10px',
                      border: '1px solid #7f1d1d',
                      backgroundColor: '#2a1010',
                      color: '#fecaca',
                      fontSize: '13px',
                    }}
                  >
                    {erroEnvio}
                  </div>
                )}

                {respostaIa && (
                  <div
                    style={{
                      marginTop: '12px',
                      padding: '14px',
                      borderRadius: '12px',
                      border: '1px solid #15803d',
                      backgroundColor: '#07140e',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: '8px',
                        flexWrap: 'wrap',
                        marginBottom: '10px',
                      }}
                    >
                      <strong style={{ color: '#4ade80', fontSize: '14px' }}>
                        Resposta de {respostaIa.origem}
                      </strong>
                      <button type="button" style={styles.btnSecondary} onClick={copiarResposta}>
                        Copiar resposta
                      </button>
                    </div>
                    {respostaFoiCortada(respostaIa.texto) && (
                      <div
                        role="alert"
                        data-testid="aviso-resposta-cortada"
                        style={{ marginBottom: '10px', fontSize: '13px', color: '#fde68a' }}
                      >
                        Atenção: esta resposta chegou <strong>cortada</strong> pelo limite de tamanho. Está incompleta.
                      </div>
                    )}
                    <pre
                      data-testid="resposta-ia"
                      style={{
                        margin: 0,
                        maxHeight: '480px',
                        overflow: 'auto',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                        fontSize: '13.5px',
                        color: '#e2e8f0',
                        lineHeight: 1.55,
                      }}
                    >
                      {respostaIa.texto}
                    </pre>
                    {respostaCopiada && (
                      <div style={{ marginTop: '8px', fontSize: '12.5px', color: '#bbf7d0' }}>{respostaCopiada}</div>
                    )}
                  </div>
                )}

                {rodadas.length > 0 && (
                  <div
                    data-testid="bloco-sequenciar"
                    style={{
                      marginTop: '12px',
                      padding: '14px',
                      borderRadius: '12px',
                      border: '1px solid #334155',
                      backgroundColor: '#0b1220',
                    }}
                  >
                    <strong style={{ color: '#e2e8f0', fontSize: '14px' }}>
                      Continuar a conversa (Sequenciar) · {rodadas.length} rodada(s)
                    </strong>
                    <p style={{ margin: '6px 0 10px', fontSize: '12.5px', color: '#94a3b8', lineHeight: 1.5 }}>
                      Escreva o próximo pedido. O app reenvia o pedido original, o novo pedido e até as 3 últimas respostas
                      que couberem no limite (as mais antigas são cortadas primeiro, com aviso). O Histórico guarda até 50
                      rodadas por pedido.
                    </p>
                    <textarea
                      data-testid="proximo-pedido"
                      value={proximoPedido}
                      onChange={(e) => setProximoPedido(e.target.value)}
                      maxLength={2000}
                      rows={3}
                      disabled={enviando}
                      placeholder="Ex.: Agora adicione login com e-mail e senha."
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        padding: '10px',
                        borderRadius: '8px',
                        border: '1px solid #334155',
                        backgroundColor: '#020617',
                        color: '#e2e8f0',
                        fontSize: '14px',
                        fontFamily: 'inherit',
                        resize: 'vertical',
                      }}
                    />
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', marginTop: '8px' }}>
                      <button
                        type="button"
                        data-testid="btn-sequenciar"
                        style={styles.btnPrimary}
                        disabled={enviando || !proximoPedido.trim()}
                        onClick={sequenciar}
                      >
                        {enviando ? `Enviando... ${segundosEnvio}s` : 'Sequenciar'}
                      </button>
                      {infoSequencia && <span style={{ fontSize: '12.5px', color: '#94a3b8' }}>{infoSequencia}</span>}
                    </div>
                    {rodadas.length > 1 && (
                      <details style={{ marginTop: '10px' }}>
                        <summary style={{ cursor: 'pointer', color: '#94a3b8', fontSize: '12.5px' }}>
                          Ver rodadas anteriores
                        </summary>
                        {rodadas.slice(0, -1).map((r, i) => (
                          <div key={i} style={{ marginTop: '8px', fontSize: '12.5px', color: '#cbd5e1' }}>
                            <div style={{ color: '#94a3b8' }}>
                              Rodada {i + 1}
                              {r.pedido ? ` — pedido: ${r.pedido}` : ' — prompt original'}
                            </div>
                            <pre style={{ margin: '4px 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '160px', overflow: 'auto' }}>
                              {r.resposta}
                            </pre>
                          </div>
                        ))}
                      </details>
                    )}
                  </div>
                )}
              </div>

              <div
                style={{
                  marginTop: '16px',
                  paddingTop: '14px',
                  borderTop: '1px solid #1e293b',
                }}
              >
                <div style={{ fontSize: '12.5px', color: '#94a3b8', marginBottom: '8px' }}>
                  Abrir direto na sua IA (o prompt vai na caixa de texto; você só confere e aperta Enter):
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {BRANDS.filter((b) => b.chatUrl).map((b) => (
                    <button
                      key={b.id}
                      type="button"
                      style={{ ...styles.btnSecondary, borderColor: b.cor, color: b.cor }}
                      onClick={() => copiarAbrirEm(b)}
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
