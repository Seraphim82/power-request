# Power Request

[![CI](https://github.com/Seraphim82/power-request/actions/workflows/ci.yml/badge.svg)](https://github.com/Seraphim82/power-request/actions/workflows/ci.yml) [![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE)

Formalizador de pedidos para IA: transforma uma ideia solta em um prompt estruturado, revisado e econômico em tokens.
Roda 100% local (FastAPI + React), com histórico em SQLite e Hub opcional para usar sua IA favorita.

## Como funciona

1. **Ideia** — você descreve o que quer; o motor identifica a categoria (bot, jogo, mobile, web, automação, geral).
2. **6 etapas guiadas** — objetivo, tecnologia, entrada, saída, regras (mínimo 1) e tratamento de erros.
3. **Revisão** — o motor local aponta lacunas e incoerências; se houver IA conectada, ela também revisa.
4. **Prompt final** — Markdown compacto, com estimativa de tokens, salvo no histórico local.
5. **Enviar** — três caminhos a partir do prompt pronto (veja abaixo).

## Enviar o prompt para a IA

| Opção | Para quê | Como funciona |
|---|---|---|
| **Enviar para a IA** | perguntas, textos, trechos de código | o app chama a IA ativa por trás e mostra a resposta na tela (com botão de copiar). Respostas muito longas podem ser cortadas pela própria IA. |
| **Abrir no Terminal** (macOS) | projetos grandes, vários arquivos | abre o Terminal numa pasta sua com a IA local (Claude ou Antigravity/Gemini) já iniciada, **com todas as ferramentas**: ela cria arquivos e roda testes, sem limite de tamanho. No Claude o prompt entra como pedido inicial; no Antigravity/Gemini ele é copiado para a área de transferência e você cola com ⌘V. |
| **Abrir no ChatGPT/Claude/Gemini...** | usar a IA no navegador | copia o prompt e abre o site. |

O Enviar por trás roda a IA **sem ferramentas e numa pasta temporária vazia** (mais seguro). O Terminal é o oposto: dá poder total à IA, só dentro da pasta que você escolher.

**Contexto fixo:** botão no topo para guardar preferências que valem para todos os projetos (stack padrão, idioma, estilo de código). Ele entra como `### Contexto` no início de cada prompt e na revisão pela IA, e pode ser ligado ou desligado. Fica salvo no SQLite local, então sobrevive à troca de IA e de navegador. É para preferências estáveis; o histórico de cada projeto fica com ferramentas como o ai-memory.

Sem IA conectada tudo funciona offline com o motor local. Se a IA escolhida falhar, o app cai para o motor local e avisa o motivo.

## Estrutura

```
backend/
  main.py             API FastAPI + serve o frontend compilado
  prompt_engine.py    motor de regras (intenção, validação, revisão, prompt final)
  ai_hub.py           Hub de IAs (chaves próprias, CLIs locais, Ollama) com proteções
  history_store.py    histórico em SQLite (~/.power_request/history.db)
  desktop_app.py      sobe o servidor local e abre o navegador
  tests/              suíte de testes (pytest)
frontend/             React + TypeScript (Vite)
assets/               logo e ícone do app
build_mac_app.sh      gera o Power Request.app (macOS)
Makefile              atalhos: setup, test, typecheck, build, check, run, app
```

## Começando

```bash
make setup     # cria o venv, instala dependências do backend e do frontend
make check     # testes + checagem de tipos + build (rode antes de cada commit)
make run       # http://127.0.0.1:8765
make app       # gera o Power Request.app (rode de novo se mover a pasta)
make icon      # após trocar o logo em assets/, regenera o ícone e a cópia usada na interface
```

Modo desenvolvimento (recarrega sozinho): `make dev` mostra os dois comandos (API em `:8000`, Vite em `:5173`).

## Hub de IAs

| Tipo | Provedores | Observação |
|---|---|---|
| CLI local | Claude (`claude`), Antigravity/Gemini (`agy`/`gemini`) | usa o login já feito no terminal, sem chave |
| Servidor local | Ollama | só `localhost`/`127.0.0.1` |
| Chave de API | OpenRouter, Gemini, Claude, OpenAI | a chave fica só no navegador (`localStorage`) |

## Segurança

- O servidor só atende `127.0.0.1`/`localhost` (proteção contra DNS rebinding).
- Operações que alteram dados rejeitam qualquer origem que não seja o próprio app (proteção contra sites abertos no navegador).
- CORS liberado apenas para o Vite em desenvolvimento, sem credenciais.
- Campos de texto passam por limite de tamanho e filtro de injeção; consultas SQL são parametrizadas.
- CLIs locais só rodam da lista fixa de comandos, sem shell, com limite de entrada e de tempo.
- Chaves de API são mascaradas em mensagens de erro.
- **Enviar para a IA:** o CLI local roda numa pasta temporária vazia (apagada ao fim) e, no Claude, sem ferramentas (`--tools ""`), então não lê seus arquivos nem executa comandos. No máximo 2 envios simultâneos; a resposta é exibida como texto puro.
- **Abrir no Terminal:** o prompt nunca vai dentro de um comando de shell; fica num arquivo temporário privado (permissão 0600) que o script lê e apaga antes de iniciar a IA. A pasta precisa estar dentro da sua pasta de usuário (a própria pasta de usuário, pastas ocultas como `.ssh`, `Library` e links para fora são recusados). Só funciona com IAs locais e só no macOS.
- **Cabeçalhos:** CSP restritiva, `X-Frame-Options: DENY`, `nosniff`, `no-referrer`; requisições `cross-site` e corpos acima de 1 MB são recusados; `/docs` e `/openapi.json` ficam desligados.

## API

| Método | Rota | Para quê |
|---|---|---|
| GET | `/api/health` | estado e versão |
| GET | `/api/hub/providers` · `/api/hub/local-tools` | catálogo de IAs e CLIs detectados |
| POST | `/api/hub/testar` | testa a conexão com a IA |
| POST | `/api/analisar-intencao` | sugere a categoria a partir da ideia |
| POST | `/api/revisar-pedido` · `/api/gerar-prompt` | revisão e geração do prompt |
| GET/PUT | `/api/contexto` | lê e salva o contexto fixo |
| POST | `/api/enviar-prompt` | envia o prompt pronto à IA ativa e devolve a resposta |
| POST | `/api/abrir-terminal` | abre o Terminal (macOS) numa pasta do usuário com a IA local iniciada |
| GET/DELETE | `/api/historico` · `/api/historico/{id}` | listar, buscar e apagar |

O contrato com o frontend é protegido por testes (`backend/tests/test_api_contract.py`): mudar o formato de uma resposta sem atualizar a interface faz a suíte falhar.

## Solução de problemas

- **"Ambiente Python não encontrado" ao abrir o app** — rode `make setup`.
- **"Interface ainda não compilada"** — rode `make build`.
- **Teste de conexão com Claude (Local) falha** — rode `claude` no Terminal e faça login.

## Requisitos

Python 3.10+, Node 20.19+ ou 22.12+ (o `make` avisa se a versão for menor) e, para os recursos de IA local, o Claude (`claude`) ou o Antigravity/Gemini já logados no terminal.

### Sistemas suportados

| Sistema | Situação |
|---|---|
| **macOS** | Testado: tudo funciona, incluindo o app `.app` e o **Abrir no Terminal**. |
| **Linux e Windows** | **Não testado.** O backend (Python) e a interface (navegador) deveriam rodar, assim como o botão **Enviar**. O app `.app` e o **Abrir no Terminal** são só do macOS (no resto, o app recusa com uma mensagem clara). Sem `make` no Windows, rode os passos do Makefile à mão. |

Testou em Linux ou Windows? Conte numa [issue](https://github.com/Seraphim82/power-request/issues/new/choose), seja funcionou ou não. Isso ajuda muito.

## Opine e contribua

Achou um bug, tem uma ideia ou quer ajudar? Abra uma [issue](https://github.com/Seraphim82/power-request/issues/new/choose). Veja [CONTRIBUTING.md](CONTRIBUTING.md). Falhas de segurança: [SECURITY.md](SECURITY.md).

## Licença

[MIT](LICENSE).
