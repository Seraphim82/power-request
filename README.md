# Power Request

[![CI](https://github.com/Seraphim82/power-request/actions/workflows/ci.yml/badge.svg)](https://github.com/Seraphim82/power-request/actions/workflows/ci.yml) [![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE)

Formalizador de pedidos para IA: transforma uma ideia solta em um prompt estruturado, revisado e econômico em tokens.
Roda 100% local (FastAPI + React), com histórico em SQLite e Hub opcional para usar sua IA favorita.

## Como funciona

1. **Ideia** — você descreve o que quer; o motor identifica a categoria (bot, jogo, mobile, web, automação, geral).
2. **6 etapas guiadas** — objetivo, tecnologia, entrada, saída, regras (mínimo 1) e tratamento de erros.
3. **Revisão** — o motor local aponta lacunas e incoerências; se houver IA conectada, ela também revisa.
4. **Prompt final** — Markdown compacto, com estimativa de tokens, salvo no histórico local.
5. **Enviar** — a partir do prompt pronto, você escolhe o caminho (veja abaixo).

Também dá para começar por um texto que você já tem (veja **Já tenho um prompt**).

## Já tenho um prompt

O botão **Já tenho um prompt** separa um texto colado nos campos do formulário. A separação é feita no seu computador, sem IA, por uma [biblioteca de regras](backend/regras_prompt/README.md).

- Aceita até 8.000 caracteres e leva no máximo 50 regras.
- **A separação pode errar**, principalmente em texto corrido: confira antes de usar.
- Nada vai para o formulário até você clicar em **Usar estes campos**. Se já houver trabalho na tela, o app pede confirmação.
- Se alguma parte não couber, o app mostra o que ficou de fora. Copie antes de continuar.
- O Contexto encontrado no texto é só mostrado: não altera o seu Contexto fixo.

## Enviar o prompt para a IA

| Opção | Para quê | Como funciona |
|---|---|---|
| **Copiar Prompt** | qualquer IA | copia o texto para você colar onde quiser. |
| **Enviar para a IA** | perguntas, textos, trechos de código | o app chama a IA ativa por trás e mostra a resposta na tela (com botão de copiar). |
| **Abrir no Terminal** (macOS, só IA local) | projetos grandes, vários arquivos | abre o Terminal numa pasta sua com o Claude ou o Antigravity/Gemini já iniciado, **com todas as ferramentas**: a IA pode criar arquivos e rodar comandos. No Claude o prompt entra como pedido inicial; no Antigravity/Gemini ele é copiado e você cola com ⌘V. |
| **Abrir no ChatGPT, Claude, Gemini...** | usar a IA no navegador | abre o site e copia o prompt. No ChatGPT e no Claude, o texto pode ir já preenchido no endereço (veja abaixo). |
| **Abrir no site da IA** (experimental, macOS) | Claude e ChatGPT | o app abre o site, cola o prompt e aperta Enter (veja abaixo). |

O botão **Enviar para a IA** aceita até 11.000 caracteres, e a tela mostra o tamanho antes do envio. No máximo 2 envios rodam ao mesmo tempo. A resposta pode chegar cortada (de uma IA local, o que passa de 24.000 caracteres é descartado); quando o app identifica o corte, ele avisa.

Dentro do app (**Testar Conexão**, revisão e otimização com IA, **Enviar** e **Sequenciar**), a IA local roda numa pasta temporária vazia e com as ferramentas bloqueadas (veja **Segurança**). O **Abrir no Terminal** é o oposto: a IA começa na pasta que você escolher, com as ferramentas e as permissões do próprio programa. O app não a prende dentro dessa pasta.

Com a IA marcada como **offline**, os botões Enviar e Sequenciar ficam desativados, com o motivo e a opção de testar de novo. O Copiar Prompt continua funcionando.

### Continuar a conversa (Sequenciar)

Depois de uma resposta do **Enviar**, escreva o próximo pedido e clique em **Sequenciar**.

- O app reenvia o pedido original, o novo pedido e até as 3 últimas respostas, dentro do limite de 11.000 caracteres. As mais antigas são cortadas ou ficam de fora, com aviso.
- A IA só recebe o que foi reenviado. Em projeto grande, ela pode perder detalhes ou mudar o que não recebeu. O app não junta os arquivos das respostas.
- O Histórico guarda até 50 rodadas por pedido. Depois disso, as respostas aparecem na tela, mas **não são salvas, e o app ainda não avisa**.

### Abrir com o prompt já preenchido (ChatGPT e Claude)

Quando o endereço final tem até 8.000 caracteres, o texto pode ir dentro do link. Antes, **toda vez**, o app avisa que o site recebe o texto assim que a página abre e que ele pode ficar no histórico do navegador. As opções são **Abrir preenchido** (exige marcar que está ciente), **Só copiar e abrir** e **Cancelar**. Nos outros sites, e em textos maiores, o app só copia e abre.

### Envio automático pelo site (experimental, macOS)

Vem desmarcado. Marque **Abrir no site da IA**, escolha a IA e o navegador (Chrome ou Safari) e clique em **Enviar pelo site**. Há 3 segundos para cancelar. Depois, o app copia o prompt, abre o site, cola com ⌘V e aperta Enter. Não mexa no teclado até terminar. Não envie dados de clientes, senhas nem informações sigilosas.

- Antes de colar e antes do Enter, o app confere se o navegador está na frente e se a aba tem o endereço esperado. Se não, ele para. Isso reduz o risco, mas não elimina: sobra um instante entre conferir e teclar, e o app não sabe se o cursor está na caixa de texto.
- O envio só é dado como confirmado quando o endereço da aba vira o de uma conversa. Sem confirmação, **confira no site antes de colar de novo**.
- O prompt continua na área de transferência.
- O macOS pede duas permissões, em **Ajustes do Sistema > Privacidade e Segurança**: **Acessibilidade** (apertar as teclas) e **Automação** (controlar o navegador). O botão **Testar automação** confere o sistema, o navegador e o teclado; não testa o controle do navegador. Essas permissões valem para o programa autorizado, não só para este envio; você pode desligá-las quando não usar.
- **Claude:** testado no macOS pelo autor. **ChatGPT: ainda não validado.** Uma mudança no site pode quebrar o envio.
- Confira se os termos do serviço permitem esse tipo de automação no seu uso.

**Contexto fixo:** botão no topo para guardar preferências que valem para todos os projetos (stack padrão, idioma, estilo de código). Ele entra como `### Contexto` no início de cada prompt e na revisão pela IA, e pode ser ligado ou desligado. Fica salvo no SQLite local, então sobrevive à troca de IA e de navegador. É para preferências estáveis; o histórico de cada projeto fica com ferramentas como o ai-memory.

Montar, revisar e gerar o prompt funciona sem IA, com o motor local; o botão **Estruturar com IA**, da ideia livre, também usa só o motor local. Se a IA falhar na revisão ou na otimização, o app usa o motor local e avisa o motivo. Enviar e Sequenciar precisam de uma IA.

## Estrutura

```
backend/
  main.py                  API FastAPI + serve o frontend compilado
  prompt_engine.py         motor de regras (intenção, revisão, prompt final, Sequenciar, Organizar)
  classificador_texto.py   separa texto corrido nos campos
  regras_prompt/           biblioteca de regras usada pelo classificador (só dados)
  ai_hub.py                Hub de IAs (chaves próprias, CLIs locais, Ollama) com proteções
  agy_seguro.py            trava de ferramentas do Antigravity dentro do app
  envio_automatico.py      envio automático pelo site (macOS)
  perfis_sites.json        endereços e esperas de cada site do envio automático
  history_store.py         histórico em SQLite (~/.power_request/history.db)
  registro_local.py        log local de falhas
  desktop_app.py           sobe o servidor local e abre o navegador
  tests/                   suíte de testes (pytest)
frontend/                  React + TypeScript (Vite), com testes ao lado do código
assets/                    logo e ícone do app
docs/                      onde o projeto parou, plano e erros conhecidos
build_mac_app.sh           gera o Power Request.app (macOS)
Makefile                   atalhos: setup, test, test-front, typecheck, build, check, run, dev, app, icon
```

## Começando

```bash
make setup     # cria o venv, instala dependências do backend e do frontend
make check     # testes do backend e do frontend + tipos + build (rode antes de cada commit)
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
| Chave de API | OpenRouter, Gemini, Claude, OpenAI | por padrão a chave fica **só na memória** e some ao recarregar a página |

Se você marcar **Lembrar esta chave neste navegador**, ela é guardada no `localStorage`, **sem criptografia**. Ao usar uma IA por chave, a chave e o texto são enviados ao provedor escolhido.

**Antigravity dentro do app:** só o `agy` (o `gemini` funciona apenas no Abrir no Terminal). O **Testar Conexão** confere se um gancho que recusa ferramentas está valendo; sem isso, a IA não é usada, e a conferência é refeita quando o app reinicia ou a versão do `agy` muda. A trava não desliga ganchos globais do próprio `agy`: se existirem, o que você enviar pode ser guardado por eles, e o app pede o seu aceite.

## Segurança

- No uso normal (`make run` ou o `.app`), o servidor só atende pelo endereço `127.0.0.1` (proteção contra DNS rebinding). No `make dev` e nos testes, `localhost` também vale.
- Nas operações que não são só de leitura, o servidor compara a origem inteira (protocolo, nome e porta): no uso normal (`make run` ou o `.app`) passa só o próprio app; o Vite de desenvolvimento (porta 5173) é aceito apenas quando a API roda sem o `desktop_app.py`, como no `make dev`. Isso protege contra páginas de outras origens abertas no navegador. Não há login: um programa instalado no computador consegue chamar o servidor diretamente.
- CORS liberado apenas para o Vite em desenvolvimento, sem credenciais.
- Campos de texto passam por limite de tamanho e um filtro de injeção **básico** (não é garantia de proteção); consultas SQL são parametrizadas.
- CLIs locais só rodam da lista fixa de comandos, sem shell, com limite de entrada e de tempo.
- Chaves de API são mascaradas em mensagens de erro.
- **Claude (Local) dentro do app** (Testar Conexão, revisão, otimização, Enviar e Sequenciar): toda chamada passa por um ponto único que usa `claude -p --safe-mode --tools "" --strict-mcp-config --disallowedTools "mcp__*"`, numa pasta temporária nova e vazia, apagada ao fim (também em erro ou tempo esgotado). Pela documentação do Claude Code, isso tira as ferramentas internas e as MCP e não carrega ganchos, plugins, skills, `CLAUDE.md` nem a memória automática. Se a versão instalada recusar alguma dessas opções, o app avisa e **não** usa o Claude sem a proteção (na revisão e na otimização, cai para o motor local).
- **Limites (Claude local):** ganchos impostos por política de administrador continuam valendo; o login, o modelo e as permissões do seu Claude continuam valendo; o texto enviado pode ficar no histórico do próprio Claude Code (`~/.claude`); alguns plugins internos (`cc-plugin-*`), skills e agentes continuam carregando, mas sem nenhuma ferramenta para usar. No Mac (Claude 2.1.332), com essas opções o Claude ficou com 0 ferramentas e 0 MCP e um gancho de teste não rodou (detalhes em [docs/STATUS.md](docs/STATUS.md)).
- **Antigravity dentro do app:** pasta temporária e a trava descrita acima, que recusa as ferramentas. No máximo 2 envios simultâneos; a resposta é exibida como texto puro. No Sequenciar, as respostas anteriores vão marcadas como texto de referência, o que não garante que a IA ignore ordens escritas nelas.
- **Abrir no Terminal:** o prompt nunca vai dentro de um comando de shell; fica num arquivo temporário privado (permissão 0600) que o script lê e apaga antes de iniciar a IA. A pasta precisa estar dentro da sua pasta de usuário (a própria pasta de usuário, pastas ocultas como `.ssh`, `Library` e links para fora são recusados). Só funciona com IAs locais e só no macOS. No Claude, um prompt que começa com `-` ou que tem uma palavra só é recusado, para o texto não ser lido como opção ou comando do programa.
- **Dados no computador:** o histórico (pedidos, prompts, respostas) e o Contexto fixo ficam em `~/.power_request/history.db`. Na mesma pasta há um log curto de falhas (`power_request.log`), com data, método, rota, código e tipo do erro, sem mensagem, prompt, resposta ou chave. O log é ligado ao abrir pelo app ou por `make run`. A pasta usa permissão 700, e o banco e o log, 600. **Isso não é criptografia.**
- **Cabeçalhos:** CSP restritiva, `X-Frame-Options: DENY`, `nosniff`, `no-referrer`; requisições `cross-site` e corpos acima de 1 MB são recusados; `/docs` e `/openapi.json` ficam desligados.

## API

| Método | Rota | Para quê |
|---|---|---|
| GET | `/api/health` | estado, versão e limite do envio |
| GET | `/api/hub/providers` · `/api/hub/local-tools` | catálogo de IAs e CLIs detectados |
| POST | `/api/hub/testar` | testa a conexão com a IA |
| POST | `/api/hub/openrouter/exchange` | troca o código do login OpenRouter por uma chave (a tela atual não usa) |
| POST | `/api/analisar-intencao` | sugere a categoria a partir da ideia |
| POST | `/api/revisar-pedido` · `/api/gerar-prompt` | revisão e geração do prompt |
| POST | `/api/organizar-prompt` | separa um texto colado nos campos |
| GET/PUT | `/api/contexto` | lê e salva o contexto fixo |
| POST | `/api/enviar-prompt` | envia o prompt pronto à IA ativa e devolve a resposta |
| POST | `/api/abrir-terminal` | abre o Terminal (macOS) numa pasta do usuário com a IA local iniciada |
| POST | `/api/sequenciar` | envia a próxima rodada da conversa |
| GET | `/api/envio-automatico/perfis` | sites e navegadores do envio automático |
| POST | `/api/envio-automatico/testar` | testa o controle do teclado |
| POST | `/api/envio-automatico` | abre o site, cola e envia (macOS) |
| GET/DELETE | `/api/historico` | lista e busca (GET) ou apaga todos os pedidos e rodadas (DELETE) |
| DELETE | `/api/historico/{id}` | apaga um pedido e as rodadas dele |
| GET | `/api/historico/{id}/rodadas` | lista as rodadas guardadas |

O contrato com o frontend é protegido por testes (`backend/tests/test_api_contract.py`): mudar o formato de uma resposta sem atualizar a interface faz a suíte falhar.

## Solução de problemas

- **"Ambiente Python não encontrado" ao abrir o app** — rode `make setup`.
- **"Interface ainda não compilada"** — rode `make build`.
- **Teste de conexão com Claude (Local) falha** — rode `claude` no Terminal e faça login.
- **Envio automático bloqueado pelo macOS** — libere **Acessibilidade** ou **Automação** em Ajustes do Sistema > Privacidade e Segurança. O texto fica copiado.

## Requisitos

Python 3.10+ e Node 20.19+ ou 22.12+ para compilar (o `make` avisa se a versão for menor). Para o `make check` e o `npm test`, use **Node 22.12 ou mais novo**: os testes do frontend dependem de um recurso que o Node 20.19 não tem. Para os recursos de IA local, o Claude (`claude`) ou o Antigravity/Gemini já logados no terminal.

### Sistemas suportados

| Sistema | Situação |
|---|---|
| **macOS** | Sistema em que o app é testado, incluindo o `.app` e o **Abrir no Terminal**. Nem tudo foi validado: o envio automático no ChatGPT, por exemplo, não foi. Situação atual em [docs/STATUS.md](docs/STATUS.md). |
| **Linux e Windows** | **Não testado.** O backend (Python) e a interface (navegador) deveriam rodar, assim como o botão **Enviar**. O app `.app`, o **Abrir no Terminal** e o envio automático são só do macOS. Sem `make` no Windows, rode os passos do Makefile à mão. |

Testou em Linux ou Windows? Conte numa [issue](https://github.com/Seraphim82/power-request/issues/new/choose), seja funcionou ou não. Isso ajuda muito.

## Opine e contribua

Achou um bug, tem uma ideia ou quer ajudar? Abra uma [issue](https://github.com/Seraphim82/power-request/issues/new/choose). Veja [CONTRIBUTING.md](CONTRIBUTING.md). Falhas de segurança: [SECURITY.md](SECURITY.md).

## Licença

[MIT](LICENSE).
