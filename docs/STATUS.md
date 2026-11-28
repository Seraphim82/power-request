# Status do projeto

Atualizado em 27/11/2026.

## Onde parou

- **Fases 1 a 7:** concluídas. **Versão 2.1.0 publicada em 27/11.**
- **Versão 2.1.1 publicada em 27/11** (corrige duas falhas altas da 2.1.0). Pull Request #3, merge
  pelo dono (`28507da`). CI e CodeQL verdes no PR e na `main` (prints do dono). A tag `v2.1.1`
  aponta para `28507da`, conferido no Mac e no GitHub. O `Power Request.app` da 2.1.1 não foi testado.
- **Alerta CodeQL #20:** analisado como falso positivo e fechado pelo dono (relato; ver ERROS).
- **Pull Request #1:** merge feito pelo dono em 27/11 (commit `31b4277`).
- **Tag `v2.1.0`:** publicada pelo dono; aponta para `31b4277`.
- **CI no GitHub:** verde. Conferido em 27/11 pela API pública do GitHub: no último commit do PR
  (`1281e5c`), `backend`, `frontend`, as três análises CodeQL e o resultado do CodeQL com sucesso;
  na `main` depois do merge (`31b4277`), `backend`, `frontend` e as três análises com sucesso.
  Isso fecha a pendência da fase 6. Os alertas do CodeQL analisados no PR estão em `docs/ERROS.md`.
- **Conferido em 27/11:** `main` local e do GitHub em `31b4277`, e a tag igual nos dois.
- **Branches:** em 27/11 o dono apagou `feat/organizar-prompt`, `feat/envio-direto-site` e
  `feat/evolucao-revisao-sequenciar-chatgpt`. Antes deste registro, só a `main` aparecia no Mac e no
  GitHub, e os commits `1281e5c`, `33654cb` e `265133b` (os últimos conhecidos de cada uma) estão
  na `main`.

## Próximo passo

1. Fase 8: plano das pendências aprovado pelo dono (PRs A, B e C). Pull Request #4 (registro da
   2.1.1) na `main` (`86b349b`). **PR A concluído:** Pull Request #5, 6 verificações verdes e sem
   alertas novos, merge pelo dono (`e82d94c`); CI #15 e CodeQL #15 verdes na `main` (prints do
   dono). No Mac, antes do merge: `make check` OK (o print mostra 22 de frontend, tipos e build; o
   total do backend foi confirmado pelo dono) e os bloqueios do nome `localhost` (400) e do prompt
   de uma palavra (403) com `make run`. O Abrir no Terminal com frase não foi repetido no Mac
   depois do PR A.
   **PR B concluído:** Pull Request #6, 6 verificações verdes e sem alertas novos, merge pelo
   dono (`76f72de`); CI #17 e CodeQL #17 verdes na `main` (prints do dono). Antes do merge, no Mac:
   `make check` (478 de backend, 22 de frontend, tipos e build), 413 no envio em partes e 422 sem o
   texto enviado (prints); o prompt apareceu no histórico (relato).
   **PR C** feito e testado só em Linux (Python 3.13): 480 testes de backend (478 anteriores,
   nenhum alterado, e 2 novos). No Mac (27/11): `make check` passou (480 de backend, 22 de
   frontend, tipos e build; print do dono) e o app abriu e gerou um prompt pelo "Já tenho um
   prompt" (relato). O `ci.yml` foi aplicado pelo dono no Terminal, por ser protegido contra
   escrita remota. **PR C concluído:** Pull Request #7, 6 verificações verdes e sem alertas novos,
   merge pelo dono (`1c2b41e`); CI #19 e CodeQL #19 verdes na `main` (prints do dono).
2. **2.1.2 publicada em 27/11** e **fase 8 concluída** (sem pendência crítica ou alta). Pull
   Request #8, 6 verificações verdes e sem alertas novos, merge pelo dono (`70642d8`); CI #21 e
   CodeQL #21 verdes na `main` (prints do dono).
   **No Mac (27/11), antes do merge:** o `Power Request.app` foi gerado com a versão 2.1.2
   (conferido no arquivo do app). O dono respondeu "tudo correto" ao roteiro (`make check`, abrir
   o app, versão no servidor, prompt no histórico e desligar) e confirmou que, no Abrir no
   Terminal, o Claude real abriu e recebeu o texto de teste. Um print posterior mostra o `make app`,
   o servidor respondendo `2.1.2` e o comando de desligar; o total de testes do backend não aparece.
   **Tag e Release:** a tag `v2.1.2` aponta para `70642d8` (conferido no Mac e no GitHub). Ela foi
   criada junto com uma Release no site do GitHub e é do tipo simples (as anteriores são anotadas);
   a descrição da Release foi corrigida pelo dono. O `.app` da 2.1.1 não foi testado.
   **Branches:** o dono apagou as seis que já estavam na `main`. Conferido no Mac e no GitHub:
   sobrou só a `main`, e o stash antigo continua guardado.
3. **Botão Fechar Power Request** (pedido do dono, fora da fase 8), na branch
   `recurso/botao-fechar`. Feito e testado só em Linux (Python 3.13): 503 testes de backend (480
   anteriores, nenhum alterado, e 23 novos), 22 de frontend, tipos e build. Num Chromium
   automatizado: Cancelar manteve o app ligado; confirmar encerrou o programa; a aba ficou aberta
   com a tela "Power Request encerrado". **No Mac, primeira versão (print do dono, 27/11):**
   `make check` passou (503 de backend, 22 de frontend, tipos e build), o `.app` foi gerado e,
   depois, o servidor não respondia mais. Depois disso o dono pediu outro visual: botão vermelho
   "Fechar" no canto superior direito e confirmação em janela (testado em Linux no mesmo
   Chromium: "Não" e Esc mantiveram o app ligado; "Sim, fechar" encerrou o programa).
   **No Mac, visual novo (27/11, relato do dono, no Safari):** a aba fechou sozinha, o teste no
   Terminal mostrou o app desligado e, ao clicar em "Não", o app continuou aberto. Outros
   navegadores não foram testados. Falta commit, Pull Request, CI e merge. O número da versão não foi
   decidido.

Testes das correções (27/11). Com o número 2.1.1, o `make check` passou no Mac (print do dono):
435 testes de backend, 22 de frontend, tipos e build. Os testes manuais abaixo são de antes da
troca do número.

- Duas falhas altas corrigidas com OK do dono (ver ERROS). No Mac (prints do dono): 435 testes de backend; no `make check`, 22 de
   frontend, tipos e build; os dois bloqueios responderam 403 e a pasta do teste não foi criada.
   O Abrir no Terminal com prompt comum abriu o
   Claude real com o texto (relato e print do dono). O histórico apareceu no app (relato do
   dono). Em cópia em Linux (Python 3.13): 435 testes de backend
   (423 antigos, nenhum alterado, e 12 novos), 22 de frontend, tipos e build OK; o servidor aberto
   pelo `desktop_app.py` recusou alterações da porta 5173; `npm audit` e `pip-audit` sem vulnerabilidades conhecidas; busca por padrões de chave e token
   no histórico do Git sem resultado. No Mac não foram feitos o teste do
   servidor pelo `desktop_app.py`, as auditorias nem a busca no histórico do Git.

- **Pull Request #2** (registro do fechamento): merge feito em 27/11 (`c13c48a`), com o CI verde no
  PR e na `main`.

## Correção do Claude local (27/11/2026): conferida no Mac, commit `3f32023`, na `main`

- Todo uso do Claude (Local) dentro do app (Testar Conexão, revisão, otimização, Enviar e
  Sequenciar) passa por um ponto único: `-p --safe-mode --tools "" --strict-mcp-config
  --disallowedTools "mcp__*"`, pasta temporária nova e vazia, apagada ao fim. Abrir no Terminal e
  Antigravity não mudaram. Versão que recusa as opções: aviso e bloqueio.
- **Documentação oficial (27/11):** `--tools ""` sozinho não afeta MCP; sem `--safe-mode`, o `-p`
  carrega ganchos, plugins, skills e `CLAUDE.md`. Ganchos de política de administrador continuam.
- **No Mac (print do dono, 27/11):** Claude Code 2.1.332; a ajuda lista `--safe-mode`, `--tools`,
  `--strict-mcp-config` e `--disallowedTools`; não existe `/Library/Application Support/ClaudeCode/`.
- **Em cópia em Linux (Python 3.13, Claude simulado):** 421 testes de backend (401 antigos mais 20
  novos) e 22 de frontend; tipos OK. 3 testes antigos ajustados com autorização do dono (ver ERROS).
- **No Mac (prints do dono, 27/11):** `make check` passou (421 de backend, 22 de frontend, tipos e
  build). `teste-claude-protegido/prova.sh`, fora do app, com os mesmos argumentos e dados falsos:
  - sem proteção: 157 ferramentas (129 MCP), conectores do claude.ai (Gmail, Drive, Calendar) e
    ai-memory conectados, 7 plugins, 90 skills; o gancho de teste rodou (SessionStart e
    UserPromptSubmit) e o MCP falso foi carregado;
  - com proteção: 0 ferramentas, 0 MCP, nenhum servidor MCP, gancho de teste não rodou, resposta OK.
  - **Ainda carregam com proteção:** 4 plugins `cc-plugin-*` (agents-md, telemetry, privacy,
    plugin-authoring), 20 skills e 5 agentes. Sem ferramentas, não há como acioná-los; se esses
    plugins têm ganchos próprios, **não foi testado**.
- **Pelo app no Mac (Safari, prints do dono, 27/11, dados inventados):** Testar Conexão, revisão
  (Revisor: Claude Local), otimização, Enviar e Sequenciar responderam, sem aviso de modo seguro.
  Durante o Sequenciar, `ps` mostrou o processo `claude -p --safe-mode --tools  --strict-mcp-config
  --disallowedTools mcp__*`. Um "continue" no Sequenciar deu tempo esgotado (600 s); o pedido
  "Resuma em 3 linhas" respondeu (ver ERROS). O código gerado pela IA não foi executado.

## Fase 6 (27/11/2026): CI e documentos, concluída

- `npm test` no CI; README, SECURITY e CONTRIBUTING atualizados; ajuste de uma linha no `CLAUDE.md`.
- Nenhum teste alterado.
- **Em cópia isolada em Linux** (arquivos versionados com as mudanças da fase e o
  `prompt_engine.py` do último commit): 401 testes de backend, 22 de frontend, tipos e build OK.
  Conferidos por script: links locais do README, rotas e arquivos `.py` do `backend/`.
- O restante do texto foi conferido por leitura do código, não por uso do app.
- **CI no GitHub: confirmado** no Pull Request #1 (opção A do dono; ver "Onde parou").
- O `prompt_engine.py`, alterado por engano (ver `docs/ERROS.md`), foi restaurado: conferido que está
  igual ao do último commit.
- **No Mac (print do dono, 27/11):** `make check` passou: 401 testes de backend, 22 de frontend,
  checagem de tipos e build. O app não foi usado nesta conferência.

## Fase 5 (27/11/2026): conferida no Mac, commitada e enviada

- **No Mac, visto em prints do dono (dados inventados):** texto corrido de exemplo com os 6 campos
  separados; 53 regras com 50 no formulário, aviso das 3 que ficaram de fora, confirmação e
  "Continuar mesmo assim".
- **No Mac, informado pelo dono:** depois de refazer uma etapa que estava pulando, "está tudo certo".
  Não foram enviados os números do `make check` nem prints das outras partes do roteiro.
- **Sem resultado informado:** teste com pedidos novos no jeito de pessoa leiga.

- Prompt gerado pelo app volta com os campos separados. O Contexto é devolvido à parte; a frase
  fixa do Padrão e o texto automático de Erros não preenchem campos.
- Tela "Já tenho um prompt": mostra o resultado e só preenche o formulário em "Usar estes campos",
  com confirmação se já houver trabalho. **Escolha do dono (opção A):** o Contexto colado é só
  mostrado; não altera o Contexto fixo.
- **Biblioteca de regras** (`backend/regras_prompt/`, só dados) lida por
  `backend/classificador_texto.py`, que confere o formato ao carregar. Substitui a lista curta de
  palavras-pista, que também casava pedaços de palavra. Tecnologias foram para a biblioteca.
  Dobrada a pedido do dono, pensando em pessoa leiga (317 expressões, 148 tecnologias e 58
  abreviações). Em 30 frases leigas novas: original 20%, versão anterior 63%, dobrada 76%.
  Placar, limites e como ampliar: `backend/regras_prompt/README.md`.
- **Em cópia em Linux (com a biblioteca):** 401 testes de backend (330 antigos mais 71 novos) e 22 de frontend
  (17 antigos mais 5 novos), nenhum teste antigo alterado; tipos e build OK.
- **Navegador (Chromium), servidor real da cópia, dados falsos:** limite de tamanho, recusa de
  injeção, resultado some ao editar o texto, preencher, cancelar, substituir, sem erro de página;
  o Contexto fixo salvo não mudou. Depois houve dois ajustes visuais (caixa do Contexto e lista
  de perguntas), conferidos só por testes e build.
- **Aviso de corte:** o Organizar mostra o que não coube e pede confirmação; máximo de regras subiu de 20 para 50 (OK do dono);
  os outros limites não mudaram. Pior caso medido: texto colado no limite, Contexto fixo de 2.000 e
  respostas curtas nos outros campos deu até 10.655; com respostas de 500 caracteres, até 11.855
  (acima dos 11.000 do Enviar). Aviso testado
  no Chromium com servidor real da cópia e dados falsos (53 regras, campo comprido, cancelar,
  continuar, substituir, texto com HTML mostrado como texto).
- Sem teste automático da tela. A área de transferência não foi testada. `npm audit` não foi rodado.

## Fase 4 (26/11/2026): concluída, conferida no Mac, commitada e enviada

Detalhes e limites em `docs/ERROS.md`.

**Em cópia em Linux:** 330 testes de backend (288 antigos mais 42 novos) e 17 de frontend (14
antigos mais 3 novos), nenhum teste antigo alterado; tipos e build OK. Janela de aviso vista em
Chromium com servidor, área de transferência e sites **simulados**. `npm audit` não foi rodado.

**No Mac:**
- Prints do dono: `make check` passou (330 e 17, tipos e build); o AppleScript compilou para
  Safari e Chrome; "Linguagem JavaScript: Node" gerou o prompt; pasta com `drwx------`, banco e
  log com `-rw-------`; o log mostrou um `envio_nao_confirmado`, sem texto do prompt.
- Informado pelo dono, sem detalhar: janela de aviso, envio automático normal e parada ao trocar
  de aba funcionaram. O log não diz o motivo de um envio não confirmado.
- O dono não informou em qual navegador fez o envio e a troca de aba. No Chrome, só há prova de que
  o script compila.
- Envio automático com o ChatGPT segue **não validado**.

## O que o app tem hoje

- Gerar prompt, revisão (avisa Stack, Input e Output vagos), histórico e Contexto fixo.
- Hub de IAs, Enviar e Abrir no Terminal (macOS).
- Sequenciar (continuar a conversa com as respostas guardadas), dentro do limite de envio.
- Abrir a IA no navegador por link com o prompt, quando o site e o tamanho permitem.
- Envio automático (opcional, macOS): perfis do Claude e do ChatGPT.
- Organizar prompt, com a tela "Já tenho um prompt" (conferida no Mac em 27/11).

## Testes

"Copiado ✓" no Copiar Prompt (26/11/2026): em cópia em Linux, backend, 14 de frontend, checagem de
tipos e build OK. Em Chromium, com servidor e área de transferência **simulados**: confirma no botão,
volta após 2 segundos e, se a cópia falha, avisa sem dizer que copiou. Commitado a pedido do dono
antes da conferência no Mac. **Depois, no Mac:** à lista de conferência (`make check` e copiar com
confirmação), o dono respondeu "tudo certo", sem detalhar. A falha de cópia só foi simulada. Sem
teste automático da tela.

Botão vira animação e bloqueio com IA offline (26/11/2026): em cópia em Linux, os
testes do backend, 14 de frontend (12 que já existiam, nenhum alterado, mais 2 novos), checagem de
tipos e build OK. A tela compilada rodou em Chromium com **servidor simulado**: o botão usado some e
volta; o outro fica bloqueado e apagado; offline bloqueia Enviar e Sequenciar, mostra o motivo e
libera depois de Testar de novo; Copiar Prompt continua liberado. O novo teste automático cobre só a
regra de quando bloquear, não a tela. **Conferido pelo dono no Mac (Safari, com prints):** o
Enviar e o Sequenciar viram a animação; o Enviar fica apagado durante o Sequenciar; com o Ollama
offline aparecem os botões apagados, o motivo e Testar de novo, e o Copiar Prompt copia; de volta
ao Antigravity, o dono informou que tudo funcionou.

Animação de espera (26/11/2026): em cópia em Linux, os testes do backend, 12 de
frontend (10 antigos, nenhum alterado, mais 2 novos), checagem de tipos e build OK. O componente,
isolado, foi visto em um navegador de teste (Chromium): o ponto se move e fica parado com redução
de movimento. **No Mac (Safari):** os prints do dono mostram a animação dentro do app, abaixo do
Enviar e do Sequenciar, e ele aprovou ao responder à lista de conferência (movimento e sumiço no
fim), sem detalhar item por item. Depois do commit, confirmou que o `make check` passou no Mac. A redução de movimento não foi testada no Mac.

Antigravity (26/11/2026):

- **Prova da trava no Mac, com o `agy` 1.5.18 real, fora do app** (scripts de teste, dados falsos):
  um gancho `PreToolUse` em pasta temporária recusou leitura, escrita, comando, busca na web e uma
  chamada MCP. Com o gancho encerrando com erro, a leitura (único caso testado) não aconteceu.
  Sem o gancho, as quatro primeiras ações aconteceram. A chamada MCP só foi testada com ele.
- **Não testados:** navegador, mensagens, subagentes, gancho travado por tempo ou sem resposta.
- **Código novo:** em cópia em Linux, com `agy` simulado: 288 testes de backend (265 antigos,
  nenhum alterado, mais 23 novos), 10 de frontend, checagem de tipos e build OK.
- **No Mac (informado pelo dono):** `make check` passou; depois, com `make run`, o Antigravity
  ficou online.
- **Uso real no Mac, com o Antigravity (26/11, relato e print do dono):** com o aviso desmarcado,
  o envio foi recusado; marcado, foi liberado. Enviar e Sequenciar responderam, até a 4ª rodada.
  Apareceram os avisos de resposta cortada, de rodadas antigas de fora e de rodada enviada sem o
  meio. O código gerado pela IA não foi executado.
- **Não conferidos no Mac com o Antigravity:** revisão e otimização com IA, e o bloqueio por
  ferramenta sem a recusa (só em teste simulado).

Fase 3 (26/11/2026), em **cópia do projeto em Linux**, com IA simulada: 265 testes de backend
(239 antigos, nenhum alterado, mais 26 novos) e 10 de frontend (7 antigos mais 3 novos),
checagem de tipos e build OK. A tela nova **não foi vista no navegador**.

Uso real no Mac, com Claude (Local), em 26/11 (prints do dono): contador de tamanho; Sequenciar
até 3 rodadas sem erro de tamanho; aviso de resposta enviada sem o meio; aviso de rodada antiga de
fora; aviso de resposta que chegou cortada. **Não conferidos no Mac:** Enviar bloqueado acima do
limite, aviso ao reabrir pelo histórico e provedores por API. O código gerado pela IA no teste não
foi executado. **`make check` no Mac: passou** (informado pelo dono em 26/11).

Ajuste de tela deixado para depois pelo dono (ver `docs/ERROS.md`).

Última conferência no Mac (26/11/2026, antes da fase 3): 239 de backend e 7 de frontend, checagem
de tipos e build OK, `npm audit` sem vulnerabilidades. Vite 8.3.8.
O aviso do npm sobre o script de instalação do `fsevents` não impediu nada; ele não foi aprovado.

## Validado e não validado

| Item | Situação |
|---|---|
| Envio automático com Claude (Chrome e Safari) | validado pelo dono no Mac (19/11) |
| Envio automático com ChatGPT | **não validado** |
| Tela do Sequenciar com IA real | **não testada** |
| Linux e Windows (app no uso real) | **não testado** |

## Pendências soltas

- `teste-trava-agy/` e `teste-claude-protegido/` (provas feitas no Mac): por decisão do dono
  (27/11), ficam no Mac e entraram no `.gitignore`.
- Testes de tela (Playwright) citados em anotações antigas não estão no repositório.
