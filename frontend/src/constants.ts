export type CategoriaId = 'geral' | 'bot' | 'jogo' | 'mobile' | 'web' | 'automacao';

export interface CategoriaConfig {
  id: CategoriaId;
  label: string;
  desc: string;
  placeholders: {
    objetivo: string;
    stack: string;
    entrada: string;
    saida: string;
    regra: string;
    tratamento_erros: string;
  };
  sugestoes: {
    stack: string[];
    regras: string[];
    erros: string[];
  };
}

export interface AnaliseIntencao {
  categoria_sugerida: CategoriaId;
  confianca: 'alta' | 'media';
  motivo: string;
  rascunho: {
    objetivo: string;
    stack: string;
    entrada: string;
    saida: string;
    regras: string[];
    tratamento_erros: string;
  };
}

export interface RevisaoPedido {
  score_qualidade: number;
  aprovado: boolean;
  pendencias: string[];
  dica_extra?: string;
  revisado_por?: string;
}

export interface ResultadoPrompt {
  prompt_final: string;
  tokens_estimados: number;
  gerado_por?: string;
  historico_id?: number;
  aviso?: string;
}

export interface ItemHistorico {
  id: number;
  criado_em: string;
  categoria: string;
  objetivo: string;
  stack: string;
  entrada: string;
  saida: string;
  regras: string[];
  tratamento_erros: string;
  prompt_final: string;
  tokens_estimados: number;
  gerado_por: string;
}

export type AuthMode = 'local_cli' | 'api_key' | 'oauth_pkce' | 'local_server';

export interface ProviderInfo {
  id: string;
  nome: string;
  auth_mode: AuthMode;
  cli_command?: string;
  modelo_padrao: string;
  modelos_sugeridos: string[];
  base_url_padrao?: string;
  console_url?: string;
  oauth_authorize_url?: string;
  dica: string;
}

export interface LocalToolStatus {
  provider_id: string;
  command: string;
  installed: boolean;
  path?: string | null;
}

export interface AIConfigSalva {
  provider: string;
  apiKey: string;
  model: string;
  alias: string;
  baseUrl: string;
  otimizarComIa: boolean;
}

export const CATEGORIES: CategoriaConfig[] = [
  {
    id: 'geral',
    label: 'Geral / Ideia Solta',
    desc: 'Qualquer projeto, análise, texto técnico ou ferramenta',
    placeholders: {
      objetivo: 'Ex: Criar um sistema simples de controle de tarefas com prioridade e prazo',
      stack: 'Ex: Python, SQLite, HTML/CSS ou sem preferência ainda',
      entrada: 'Ex: Tarefas digitadas pelo usuário com título, categoria e data limite',
      saida: 'Ex: Lista organizada, filtros rápidos e resumo do que vence hoje',
      regra: 'Ex: Manter código simples, modular e fácil de rodar localmente',
      tratamento_erros: 'Ex: Avisar com mensagem clara se faltar título ou data inválida',
    },
    sugestoes: {
      stack: ['Python + SQLite', 'TypeScript + React', 'Sem preferência (sugira a melhor)'],
      regras: ['Código limpo e modular', 'Sem dependências desnecessárias', 'Explicação direta'],
      erros: ['Validar campos vazios com mensagem clara', 'Não quebrar em entradas inesperadas'],
    },
  },
  {
    id: 'bot',
    label: 'Bot / Assistente',
    desc: 'WhatsApp, Telegram, Discord, Slack ou automação de atendimento',
    placeholders: {
      objetivo: 'Ex: Bot de atendimento que responde dúvidas frequentes e registra chamados',
      stack: 'Ex: Node.js ou Python + API oficial / webhook',
      entrada: 'Ex: Mensagens de texto, comandos (/ajuda, /status) e respostas de botão',
      saida: 'Ex: Respostas objetivas, confirmação de protocolo e encaminhamento humano',
      regra: 'Ex: Não inventar informações fora da base e responder em até 3 segundos',
      tratamento_erros: 'Ex: Fallback amigável quando a API cair ou a mensagem não for entendida',
    },
    sugestoes: {
      stack: ['Python + FastAPI', 'Node.js + TypeScript', 'Webhook REST'],
      regras: ['Respostas curtas e objetivas', 'Registrar logs sem expor dados sensíveis', 'Comando de fallback'],
      erros: ['Timeout de rede com nova tentativa', 'Mensagem padrão se serviço externo falhar'],
    },
  },
  {
    id: 'jogo',
    label: 'Jogo',
    desc: '2D, 3D, puzzle, plataforma, RPG, web ou protótipo jogável',
    placeholders: {
      objetivo: 'Ex: Jogo 2D de desvio e coleta com fases progressivas, pontuação e som',
      stack: 'Ex: HTML5 Canvas / JS, Godot, Unity ou Python Pygame',
      entrada: 'Ex: Setas/WASD, barra de espaço, mouse/toque e pausa (ESC)',
      saida: 'Ex: Loop a 60 FPS, HUD com vidas/pontos, tela de vitória e game over',
      regra: 'Ex: Física consistente independente do FPS e reinício instantâneo sem recarregar',
      tratamento_erros: 'Ex: Evitar objetos saindo da tela ou colisões duplicadas no mesmo frame',
    },
    sugestoes: {
      stack: ['HTML5 + TypeScript', 'Godot (GDScript)', 'Python (Pygame)'],
      regras: ['60 FPS estáveis com delta time', 'Controles responsivos', 'Reinício rápido'],
      erros: ['Limites de arena/tela', 'Reset limpo de estados e timers'],
    },
  },
  {
    id: 'mobile',
    label: 'App Mobile',
    desc: 'Aplicativo para celular (Android / iOS / PWA responsivo)',
    placeholders: {
      objetivo: 'Ex: App de finanças pessoais com lançamentos rápidos, metas e gráficos mensais',
      stack: 'Ex: React Native / Expo, Flutter ou PWA',
      entrada: 'Ex: Valor, categoria, data, toque em botões e filtros por mês',
      saida: 'Ex: Saldo atualizado, lista por categoria e persistência local no aparelho',
      regra: 'Ex: Interface thumb-friendly, carregamento rápido e funcionamento offline básico',
      tratamento_erros: 'Ex: Bloquear valor zero/negativo e avisar se falhar ao salvar local',
    },
    sugestoes: {
      stack: ['React Native + Expo', 'Flutter', 'PWA (React + Vite)'],
      regras: ['Toque confortável em telas pequenas', 'Persistência local', 'Visual limpo'],
      erros: ['Validar valores numéricos', 'Estado vazio amigável quando não há itens'],
    },
  },
  {
    id: 'web',
    label: 'Site / Sistema Web',
    desc: 'Landing page, dashboard, CRUD, painel administrativo ou API web',
    placeholders: {
      objetivo: 'Ex: Painel web para cadastrar clientes, buscar rápido e exportar resumo',
      stack: 'Ex: React + TypeScript + FastAPI ou Node',
      entrada: 'Ex: Formulários, barra de busca, filtros e cliques em ações',
      saida: 'Ex: Tabela/cards atualizados, feedback visual de sucesso/erro e persistência',
      regra: 'Ex: Layout responsivo (desktop e mobile) e componentes bem separados',
      tratamento_erros: 'Ex: Exibir erro legível se a API falhar ou campos obrigatórios estiverem vazios',
    },
    sugestoes: {
      stack: ['React + TypeScript + FastAPI', 'Next.js', 'HTML + Tailwind + JS'],
      regras: ['Responsivo desktop e mobile', 'Feedback claro de loading/erro', 'Código tipado'],
      erros: ['Tratar erro HTTP da API', 'Validar formulários antes de enviar'],
    },
  },
  {
    id: 'automacao',
    label: 'Automação / Script',
    desc: 'Organizar arquivos, planilhas, PDFs, relatórios ou tarefas repetitivas',
    placeholders: {
      objetivo: 'Ex: Script que lê planilhas/arquivos de uma pasta, consolida dados e gera relatório',
      stack: 'Ex: Python (pandas/openpyxl/pathlib) ou Bash/PowerShell',
      entrada: 'Ex: Caminho da pasta de origem, filtros de data e formato de saída',
      saida: 'Ex: Arquivo consolidado + log resumido de processados e ignorados',
      regra: 'Ex: Modo seguro (não apagar arquivos originais sem confirmação)',
      tratamento_erros: 'Ex: Pular arquivo corrompido registrando aviso em vez de abortar tudo',
    },
    sugestoes: {
      stack: ['Python 3 (stdlib + pandas)', 'Python + openpyxl', 'Shell script'],
      regras: ['Execução segura sem perda de dados', 'Log claro ao final', 'Configurável por argumentos'],
      erros: ['Arquivo inexistente ou sem permissão', 'Linha/registro inválido ignorado com aviso'],
    },
  },
];

// `preenchimento` só onde o site aceita o prompt pelo endereço (confirmado). Nos demais: copiar e colar.
export const BRANDS = [
  {
    id: 'chatgpt',
    nome: 'ChatGPT',
    cor: '#10a37f',
    chatUrl: 'https://chatgpt.com/',
    preenchimento: { param: 'q' },
  },
  {
    id: 'claude',
    nome: 'Claude',
    cor: '#d97757',
    chatUrl: 'https://claude.ai/new',
    preenchimento: { param: 'q' },
  },
  { id: 'gemini', nome: 'Gemini', cor: '#4285f4', chatUrl: 'https://gemini.google.com/app' },
  { id: 'grok', nome: 'Grok', cor: '#e5e7eb', chatUrl: 'https://grok.com/' },
  { id: 'deepseek', nome: 'DeepSeek', cor: '#6366f1', chatUrl: 'https://chat.deepseek.com/' },
  { id: 'perplexity', nome: 'Perplexity', cor: '#20b2aa', chatUrl: 'https://www.perplexity.ai/' },
  { id: 'copilot', nome: 'Copilot', cor: '#38bdf8', chatUrl: 'https://copilot.microsoft.com/' },
  { id: 'openrouter', nome: 'OpenRouter', cor: '#a855f7', chatUrl: 'https://openrouter.ai/chat' },
];

export const STEP_META = [
  { num: 1, key: 'objetivo', titulo: '1. O que você quer criar?', ajuda: 'Explique com suas palavras o resultado principal, sem se preocupar com termos técnicos.' },
  { num: 2, key: 'stack', titulo: '2. Qual tecnologia prefere?', ajuda: 'Se já tiver uma linguagem ou ferramenta em mente, coloque aqui. Se não tiver, clique em "Deixar a IA escolher".' },
  { num: 3, key: 'entrada', titulo: '3. O que entra no sistema?', ajuda: 'Quais informações, comandos, cliques ou arquivos o usuário ou o sistema vai fornecer?' },
  { num: 4, key: 'saida', titulo: '4. O que deve sair / acontecer?', ajuda: 'Qual é o resultado esperado na tela, no arquivo, na resposta ou no comportamento?' },
  { num: 5, key: 'regras', titulo: '5. Regras importantes', ajuda: 'Informe pelo menos 1 regra: limites, estilo, performance ou condições que não podem falhar. Você pode adicionar várias.' },
  { num: 6, key: 'tratamento_erros', titulo: '6. O que fazer se algo der errado?', ajuda: 'Como o sistema deve reagir a erro de rede, dado inválido, arquivo ausente ou falha inesperada.' },
] as const;

export const STORAGE_KEY = 'power_request_ai_hub_v1';

export const STACK_AUTO = 'Deixar a IA escolher a melhor opção';

export type EstadoIa = 'desconhecido' | 'verificando' | 'online' | 'offline';

export const ESTADO_IA_META: Record<EstadoIa, { rotulo: string; cor: string }> = {
  desconhecido: { rotulo: 'Não testada', cor: '#94a3b8' },
  verificando: { rotulo: 'Verificando...', cor: '#fbbf24' },
  online: { rotulo: 'Online', cor: '#4ade80' },
  offline: { rotulo: 'Offline', cor: '#f87171' },
};

export const CONTEXTO_MAX = 2000;
export const CONTEXTO_ATIVO_KEY = 'power_request_contexto_ativo_v1';

export const PASTA_TERMINAL_KEY = 'power_request_pasta_terminal_v1';
export const PASTA_TERMINAL_PADRAO = 'Desktop/meu-projeto';
export const LEMBRAR_CHAVE_KEY = 'power_request_lembrar_chave_v1';
