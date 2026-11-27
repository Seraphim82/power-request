# Status do projeto

Atualizado em 27/11/2026.

## Onde parou

- **Fases 1 a 4:** concluídas. Em 27/11, o registro do Git no Mac mostrou `origin/feat/organizar-prompt`
  no mesmo commit da fase 4 (`a919e4e`), ou seja, enviadas.
- **Fase 5 (Organizar prompt):** pronta e conferida no Mac em 27/11 (ver a seção da fase). Commit `38bea67` **enviado** ao GitHub
  (branch `feat/organizar-prompt`).
- **Correção do Antigravity (item 13 do ERROS):** no Mac, `make check` passou e o Antigravity ficou
  online no app (informado pelo dono em 26/11). Aviso de ganchos, Enviar e Sequenciar conferidos
  (ver Testes).
- **`main`:** ainda sem merge (última anotação: parada no commit `b21ce46`).

## Próximo passo

1. Em chat novo, a pedido do dono (27/11): primeiro corrigir o Claude local (ver `docs/ERROS.md`),
   com teste novo e commit próprio; só depois do OK dele, a fase 7 do `docs/PLANO.md`.
2. Fase 7: confirmar o CI no Pull Request antes do merge.
3. A fase 6 ainda não foi enviada (sem push).

## Fase 6 (27/11/2026): CI e documentos, commitada (não enviada)

- `npm test` no CI; README, SECURITY e CONTRIBUTING atualizados; ajuste de uma linha no `CLAUDE.md`.
- Nenhum teste alterado.
- **Em cópia isolada em Linux** (arquivos versionados com as mudanças da fase e o
  `prompt_engine.py` do último commit): 401 testes de backend, 22 de frontend, tipos e build OK.
  Conferidos por script: links locais do README, rotas e arquivos `.py` do `backend/`.
- O restante do texto foi conferido por leitura do código, não por uso do app.
- **CI no GitHub: não confirmado** (opção A do dono: confirmar no Pull Request).
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

- A pasta `teste-trava-agy/` está fora do Git e não foi aberta. Não commitar sem revisar; decidir
  se fica, sai do projeto ou entra no `.gitignore`.
- Testes de tela (Playwright) citados em anotações antigas não estão no repositório.
- Nenhum Pull Request havia sido aberto até a última anotação (23/11); conferir no GitHub.
