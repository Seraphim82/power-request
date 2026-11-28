# Plano de melhorias

Origem: análise de 26/11/2026. Uma fase por chat, com teste, atualização do STATUS e commit.
Nenhum teste existente é alterado. Detalhes de cada item em `docs/ERROS.md`.

## [x] Fase 1: salvar
- **Objetivo:** proteger o trabalho.
- **Tarefas:** ajustar o `.gitignore`, commitar e enviar.
- **Pronto quando:** commit feito e branch no GitHub.

## [x] Fase 2: memória do projeto
- **Objetivo:** um chat novo recuperar o contexto.
- **Tarefas:** criar `CLAUDE.md`, `docs/STATUS.md`, `docs/ERROS.md` e `docs/PLANO.md`.
- **Pronto quando:** um chat novo souber onde parou só lendo os arquivos, e eles estiverem
  commitados.

## [x] Fase 3: envio (itens 2, 3 e 9)
- **Objetivo:** envio previsível.
- **Tarefas:** orçamento único no Sequenciar; mostrar o tamanho e avisar antes de enviar; detectar
  e avisar resposta cortada; testes novos.
- **Pronto quando:** resposta longa não quebra o Sequenciar e todo corte é avisado.
- **Decidido (26/11):** faltando espaço, cortar primeiro as respostas mais antigas e avisar na tela.

## [x] Correção do Antigravity (item 13), em chat próprio
- [x] Provar no Mac, com dados falsos, que a trava recusa ferramentas.
- [x] `stream-json` pela entrada padrão; pasta temporária com a trava em todo uso dentro do app;
  prova no Testar Conexão (refeita se a versão mudar ou o app reiniciar); descarte e bloqueio se
  aparecer ferramenta sem a recusa (só detecta); `gemini` fora do app; aviso em português;
  aceite quando há ganchos globais (escolha do dono: avisar e liberar); testes novos.
- [x] Conferir no Mac: `make check` e conexão online no app.
- [x] Conferir no Mac: aviso de ganchos, Enviar e Sequenciar com o Antigravity.
- **Pronto quando:** conecta e envia no Mac, com o bloqueio comprovado.

## [x] Enviar apagado com IA offline (sugestão do dono, 26/11)
Encaixe (26/11): depois de validar a correção do Antigravity no Mac.
Feito em 26/11 no mesmo chat, por escolha do dono. **Conferido pelo dono no Mac.**
- **Tarefas:** desativar Enviar e Sequenciar só quando o estado for `offline` (não em
  `desconhecido` nem `verificando`, decidido em 26/11); explicar o motivo em português simples,
  com opção de testar de novo; manter Copiar Prompt; teste novo.
- **Pronto quando:** com a IA offline não dá para enviar, e a pessoa sabe o que fazer.

## [x] Animação de espera no Enviar e no Sequenciar (sugestão do dono, 26/11)
Feita em 26/11 no mesmo chat do Antigravity, por escolha do dono. **Aprovada pelo dono no Mac.**
- **Motivo:** durante a espera pela resposta, a tela parece parada.
- **Tarefas:** desenho de um prompt, uma linha com um ponto de luz indo até um computador (como um
  ping), perto do botão usado; texto de espera com o tempo decorrido; sumir quando chegar a
  resposta ou o erro; só SVG e CSS, sem biblioteca nova; parar o movimento quando o sistema pedir
  menos animação; não sugerir porcentagem nem progresso real.
- **Pronto quando:** nas duas esperas dá para ver que o pedido está em andamento.

## [x] Botão vira a animação durante a espera (sugestão do dono, 26/11)
Feito em 26/11 junto com o item acima. **Conferido pelo dono no Mac.**
- **Motivo:** evitar clique por engano enquanto a IA responde.
- **Tarefas:** a animação ocupa o lugar do botão usado; o outro fica bloqueado e apagado; o botão
  volta com a resposta ou o erro.
- **Pronto quando:** durante a espera não há botão para clicar de novo no lugar usado.

## [x] Fase 4: segurança (itens 4 a 7 e 12, e permissões do banco)
Implementada e conferida no Mac em 26/11 (alcance no `docs/STATUS.md`).
- **Objetivo:** fechar as brechas conhecidas.
- **Tarefas:** origem exata; conferir a aba antes das teclas; aviso de privacidade; corrigir o
  falso positivo do filtro; log local sem dados sensíveis; permissões 700 e 600; testes novos.
- **Pronto quando:** outra porta é recusada e as teclas não vão para outro site.
- **Decidido (26/11):** manter o `?q=` com janela de aviso toda vez, ciência obrigatória e a opção
  "só copiar e abrir".
- [x] Código e testes novos.
- [x] Conferir no Mac.

## [x] Fase 5: Organizar prompt (item 8 e a tela)
- **Objetivo:** terminar a função.
- **Tarefas:** reconhecer Contexto e Padrão à parte; depois criar a tela.
- **Pronto quando:** gerar e organizar devolve os campos sem misturar.
- **Decidido (27/11):** o Contexto colado é só mostrado; não altera o Contexto fixo (opção A).
- [x] Código, tela e testes novos (em cópia em Linux).
- [x] Biblioteca de regras para texto corrido, em `backend/regras_prompt/` (pedido do dono, 27/11,
  antes dos próximos testes).
- [x] Avisar na tela o que for cortado no Organizar (pedido do dono, 27/11; em cópia em Linux).
- [x] Máximo de regras do Organizar de 20 para 50, sem mexer nos outros limites (OK do dono, 27/11).
- [x] Conferir no Mac (27/11: prints e informação do dono; detalhes no `docs/STATUS.md`).

## [x] Fase 6: CI e documentos (itens 10 e 11)
- **Objetivo:** verificação e documentação fiéis ao app.
- **Tarefas:** `npm test` no CI; atualizar README e SECURITY.
- **Pronto quando:** o CI roda tudo e o README bate com o app.
- **Decidido (27/11):** opção A: sem mudar quando o CI dispara; a confirmação no GitHub vem com o
  Pull Request da fase 7, antes do merge.
- [x] `npm test` no CI.
- [x] README, SECURITY e CONTRIBUTING.
- [x] Confirmar o CI no GitHub (no Pull Request #1, 27/11).

## [x] Correção do Claude local (antes da fase 7, pedido do dono em 27/11)
- **Objetivo:** todo uso do Claude (Local) dentro do app sem ferramentas e em pasta temporária vazia.
- **Decidido (27/11):** opção B: proteção num ponto único, com `--safe-mode`, `--tools ""`,
  `--strict-mcp-config` e `--disallowedTools "mcp__*"`; versão sem essas opções é bloqueada;
  3 testes antigos ajustados com autorização do dono (lista no `docs/ERROS.md`).
- [x] Código e testes novos (em cópia em Linux, Claude simulado).
- [x] Conferir no Mac: `make check` e prova com o Claude real, fora do app (dados falsos, 27/11).
- [x] Conferir no Mac: os cinco usos pelo app com o Claude real (27/11, prints do dono).
- [x] Commit próprio, a pedido do dono (`3f32023`).
- **Pronto quando:** a prova no Mac mostrar que gancho e ferramentas não rodam pelo app.

## [x] Fase 7: versão
- **Decidido (27/11):** versão 2.1.0 (funções novas sem quebrar o que existia); merge por
  "Create a merge commit"; tag só depois do merge.
- [x] Versão 2.1.0 no código e `CHANGELOG.md`.
- [x] Pull Request #1, CI verde (backend e frontend), merge pelo dono (`31b4277`), tag `v2.1.0` (27/11).
- **Objetivo:** publicar uma versão marcada.
- **Tarefas:** Pull Request e merge, tag, `CHANGELOG.md`. Para desfazer algo publicado,
  usar `git revert`.
- **Pronto quando:** `main` atualizada e com tag.

## [x] Fase 8: revisão de segurança
- **Objetivo:** olhar de novo, em chat novo.
- **Tarefas:** revisar o código e as proteções.
- **Pronto quando:** relatório sem pendência crítica ou alta.
- [x] Revisão do código e provas em cópia em Linux (27/11).
- [x] Falhas altas (porta 5173 e prompt com "-"): corrigidas com teste novo, com OK do dono; em
  cópia em Linux.
- [x] Conferir os dois bloqueios no Mac (27/11, prints do dono).
- [x] Confirmar no Mac o Abrir no Terminal com prompt comum (27/11, Claude real; dono).
- [x] Confirmar no Mac que o histórico aparece no app (27/11, relato do dono).
- [x] PR A, código e teste novo (27/11, em cópia em Linux): só `127.0.0.1` no uso normal
  (`localhost` e `testserver` recusados) e prompt de uma palavra recusado no Claude.
- [x] PR A: conferir no Mac (27/11, `make check` e dois bloqueios; dono).
- [x] PR A: Pull Request #5, 6 verificações verdes, merge (`e82d94c`) pelo dono (27/11).
- [x] Decidido pelo dono (27/11): versão 2.1.1, porque a 2.1.0 publicada tem as falhas. Número
  atualizado no código e no `CHANGELOG.md`.
- [x] Commit, Pull Request #3, CI, merge (`28507da`) e tag `v2.1.1` (27/11).
- [x] Alerta CodeQL #20: analisado como falso positivo; fechado pelo dono (27/11).
- [x] Código de acesso nas rotas: avaliado; não criar agora (OK do dono no plano, 27/11).
- [x] PR B (dados e rede), código e teste novo (27/11, em cópia em Linux): limite do corpo,
  endereço do Ollama, chave em redirecionamento, erro 422 e histórico apagado.
- [x] PR B: conferir no Mac (27/11, `make check`, 413 e 422; histórico por relato do dono).
- [x] PR B: Pull Request #6, 6 verificações verdes, sem alertas novos, merge (`76f72de`) (27/11).
- [x] PR C (limpeza), código e teste novo (27/11, em cópia em Linux): rota do OpenRouter removida
  e ações do CI presas a um commit.
- [x] PR C: conferir no Mac (27/11, `make check`; uso do app por relato do dono).
- [x] PR C: Pull Request #7, 6 verificações verdes, sem alertas novos, merge (`1c2b41e`) (27/11).
- [x] Decidido pelo dono (27/11): versão 2.1.2. Número atualizado no código e no `CHANGELOG.md`.
- [x] Gerar e testar o `.app` da 2.1.2 e repetir o Abrir no Terminal com frase (27/11, relato do
  dono).
- [x] Conferências no Mac (27/11). O que ficou só em teste automático está em `docs/ERROS.md`.
- [x] Fechamento: commit, Pull Request #8, merge (`70642d8`), tag `v2.1.2` e branches já na
  `main` apagadas pelo dono (27/11).

## Pedido do dono (27/11): botão Fechar Power Request
Para desligar o app sem usar o Terminal. Plano aprovado pelo dono.
- [x] Botão com confirmação, rota `POST /api/encerrar` e testes novos (em cópia em Linux).
- [x] Ajuste pedido pelo dono: botão vermelho "Fechar" no canto superior direito e confirmação em
  janela (em cópia em Linux).
- [x] Proteções: origem obrigatória e conferida, confirmação no pedido, não fecha durante Enviar ou
  Sequenciar, sem comando de Terminal. No `make dev` o botão não aparece.
- [x] Conferir no Mac (27/11, relato do dono): no Safari a aba fecha sozinha; "Não" mantém o app
  aberto.
- [ ] Commit, Pull Request e merge; decidir o número da versão.

## Depois da fase 4: conversa completa na pasta do projeto do cliente
Ideia do dono (26/11), a fazer em chat próprio.
- **Objetivo:** no Abrir no Terminal, a IA poder consultar respostas cortadas do Sequenciar.
- **Como:** o app salva a conversa em um arquivo na pasta escolhida e o pedido aponta para ele.
- **Cuidados:** só a pedido da pessoa; permissão 600; não sobrescrever arquivo alheio; não seguir
  atalho (link simbólico); impedir que vá para o Git; tratar o conteúdo como dado, não instrução;
  recusar a pasta do próprio repositório. Teste novo.
- **Fora:** liberar ferramentas ou arquivos no botão Enviar.

## Ajustes anotados, ainda sem fase (encaixar quando o dono decidir)
- Privacidade: avaliar `--no-session-persistence` no Claude local dentro do app, para o texto não
  ficar no histórico do Claude Code (achado em 27/11).
- Sequenciar com "continue" estoura 600 s no Claude local (ver ERROS): orientar ou ajustar o tempo.
- Testes: versão mínima do Python, ou ajustar o `monkeypatch` do `test_api_contract.py` (ver ERROS).
- CI: avaliar o Dependabot para avisar quando houver versão nova das ações presas a um commit.
- Conferir no Mac e corrigir a mensagem de permissão de Automação.
- Alinhar a conferência de versão do Node (`Makefile`) com o que os testes exigem.
- Trocar o texto do botão "Estruturar com IA" ou ligá-lo à IA.
- No log, separar o motivo do envio automático não confirmado (aba errada, aba mudou ou falta de
  confirmação): hoje os três saem como `envio_nao_confirmado`.
- Avaliar `--settings` do `agy` (visto na ajuda do 1.5.18, não testado) como segunda trava.
- Investigar se dá para tirar os pedidos do app da captura de ganchos globais de memória.
- Testar a trava com navegador, mensagens, subagentes e gancho travado por tempo.
- Limpar o aviso do envio anterior ao iniciar um novo Sequenciar.
- Biblioteca: nova rodada com frases do dono e de quem testar (escrever antes um grupo
  inédito; há 115 pistas sem exemplo que as exercite); avaliar a IA ativa como opção; dividir texto ditado sem pontuação.
- Organizar: revisar o limite de 8.000 caracteres (prompt grande do próprio app pode passar).
- Avisar quando o histórico parar de guardar (50 rodadas).
- Orientar sobre projeto grande: resposta acima de 24.000 e perda de contexto no Sequenciar.

## Depois da fase 8
- `docs/MANUTENCAO.md`, `docs/COMO-PEDIR-MUDANCAS.md`, documento curto de funcionamento (FSD)
  e `DESIGN.md`.
- Testes de tela no repositório e no CI; depois dividir o `App.tsx`.
- Fixar versões das dependências Python; verificador de código (ex.: Ruff).
- Backup e numeração de versão do banco antes de mudar tabelas.
- Conferir na documentação oficial os nomes de modelos fixos no código.
- Ideias: janela própria e instalador para quem não usa Terminal; perfil do Gemini; ctxpack no
  Sequenciar, se necessário.
