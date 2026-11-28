# Erros conhecidos

Formato: sintoma, causa, solução e como evitar. Nunca colar aqui chave, prompt, resposta ou dado de cliente.
Os números seguem a análise de 26/11/2026 (o item 1, trabalho sem commit, foi resolvido na fase 1).

## Corrigido na fase 8 (27/11): gravidade ALTA, testado em Linux e conferido no Mac em parte

**No Mac (prints do dono, 27/11):** 435 testes de backend passaram; no app, `curl` com origem
`localhost:5173` recebeu 403 (rota que não altera dados) e o prompt `-teste` no Abrir no Terminal
recebeu 403, sem criar a pasta. Leitura (CORS) e demais ações: só nos testes automáticos. Uso
normal: o Abrir no Terminal com prompt comum abriu o Claude real com o texto (relato e print do
dono). O histórico apareceu no app (relato do dono).

Atinge a versão 2.1.0; corrigido na 2.1.1, publicada em 27/11. As duas falhas se somavam: uma página na porta 5173 podia abrir o
Terminal com uma opção do Claude escolhida por ela. Reproduzido com Claude e envio falsos. Não foi
testado se o Claude real executaria um comando por essas opções.

### O app em uso normal confiava na porta 5173 (desenvolvimento)
- **Causa:** as origens do Vite valiam sempre; dava para ler o histórico, alterar e apagar dados e
  chamar o envio automático e o Abrir no Terminal.
- **Solução:** o `desktop_app.py` (`make run` e `.app`) desliga essas origens, nas alterações e na
  leitura (CORS). No `make dev` continuam valendo.
- **Limite:** quem subir a API sem o `desktop_app.py` continua aceitando a porta 5173.

### Abrir no Terminal: prompt começando com "-" virava opção do Claude
- **Causa:** o prompt é passado como argumento, sem separação.
- **Solução:** prompt que começa com "-" é recusado (403) antes de criar pasta ou arquivo. Um `--`
  mudaria a linha que um teste antigo exige.
- **Evitar:** teste novo em `backend/tests/test_fase8_seguranca.py`.

### Teste que troca valor do `app.state` (aprendido ao criar os testes da fase 8)
- Com pytest 9.2, `monkeypatch.setattr` em `app.state` apaga o valor ao desfazer. Usar
  `monkeypatch.setitem(main.app.state._state, ...)`.
- `test_script_gerado_entrega_prompt_intacto_e_apaga_temporarios` falha se sobrarem pastas
  `power-request-term-*` de execuções anteriores na pasta temporária (visto em Linux).

## Corrigido na fase 8, PR A (27/11): gravidade baixa, testado em Linux e conferido no Mac em parte

- **No Mac:** os bloqueios do nome `localhost` (400) e do prompt de uma palavra (403) funcionaram
  com `make run` (prints do dono). O bloqueio de `testserver` e das alterações: só testes automáticos.

- **`localhost` em IPv6:** no uso normal só valem o endereço e a origem `127.0.0.1`. O risco não foi
  reproduzido; o app já recusava alterações marcadas pelo navegador como de outro site. É proteção extra.
- **Nome `testserver`:** recusado no uso normal; continua valendo nos testes e no `make dev`.
- **Prompt de uma palavra no Abrir no Terminal:** recusado no Claude. Não foi testado se o Claude
  real trataria a palavra como subcomando.
- Teste novo: `backend/tests/test_fase8_acesso.py`.
- **Código de acesso nas rotas (decidido com o OK do dono no plano):** não criar agora. Um programa
  no computador poderia pedir a mesma página e pegar o código. Segue como limite conhecido.

## Corrigido na fase 8, PR B (27/11): gravidade baixa, testado em Linux e conferido no Mac em parte

- **No Mac (27/11):** `make check` passou, e com `make run` o envio de 1,2 MB em partes recebeu 413
  e o erro 422 não devolveu o texto enviado (prints do dono). O prompt apareceu no histórico
  (relato do dono). Ollama, chave em redirecionamento e histórico apagado: no Mac, só pelos testes
  automáticos.

- **Limite de 1 MB:** agora conta o corpo recebido, em partes ou não (`backend/limite_corpo.py`).
- **Endereço do Ollama:** só `http(s)://localhost` ou `127.0.0.1`, com porta opcional. Quem usava
  caminho ou consulta no endereço precisa tirar.
- **Chave em redirecionamento:** o cabeçalho da chave não é repetido (testado entre dois servidores
  falsos em `127.0.0.1`, nunca com provedor real ou chave real).
- **Erro 422:** devolve só tipo, campo e mensagem.
- **Histórico apagado:** `secure_delete` em toda conexão e `VACUUM` no Limpar tudo. O teste procura
  um texto fictício nos arquivos do banco. Sobras de exclusões feitas antes saem no Limpar tudo.
  **Limites:** não alcança backups nem garante remoção física no disco; se o `VACUUM` falhar, a
  exclusão vale e o app não avisa.
- Teste novo: `backend/tests/test_fase8_dados_rede.py` (30 casos; 21 falham sem a correção).
- **Limite que continua:** um programa local que responda no endereço do Ollama ainda pode
  redirecionar o pedido (pela regra do `urllib`, sem o corpo). Não foi testado nem corrigido.

## Em aberto

### Fase 8, revisão de segurança (27/11): itens de gravidade baixa
Conferidos sobre o código da `main` (`c13c48a`), em cópia em Linux, com dados e programas falsos.
Estes itens não foram corrigidos.
- **Sem senha nas rotas** (limite do desenho, aceito): ver a decisão no registro do PR A.
- **CI** (visto no código): ações fixadas por versão (`@v4`, `@v5`), não pelo commit.
- **Login OpenRouter:** a tela não chama a rota. Não vi a rota guardar a chave; ela a devolve a
  quem chamou. Recomendação: remover a rota e a linha do README, mantendo a função e seus testes
  (nenhum teste que encontrei chama a rota). Chave de API do OpenRouter não muda.

### CodeQL revisto na fase 8 (27/11)
- **#13:** confirmo falso positivo pelo código: o log recebe método, modelo da rota, código e o
  status do envio, e filtra os caracteres.
- **#19:** confirmo que é só em teste; em produção o host é comparado por inteiro.
- **#14 a #18:** os dois textos passam por `mensagem_publica`; o teste da correção passa.
- **#20 "Information exposure through an exception" (Medium):** apareceu no painel depois da
  revisão (print do dono: 1 aberto e 19 fechados); detectado primeiro em `31b4277`. O caminho começa
  no erro da IA em `/api/revisar-pedido`, que passa por `mensagem_publica`, e o alerta aponta para
  `/api/analisar-intencao`. As rotas só compartilham `_run_domain_action`, que devolve o resultado
  da ação sem guardar estado. Falso positivo pelo código; vistos só os passos 1 e 2 dos 15.
  **Limite:** o filtro remove caminhos e limita o tamanho; não procura chaves ou outros segredos.
  Fechado pelo dono em 27/11 (relato; não conferido por mim no painel).

### Claude local usa ferramentas no Testar Conexão, na revisão e na otimização (SEGURANÇA, achado na fase 6)
- **Causa (visto no código, não reproduzido):** `testar_conexao`, `revisar_com_ia` e `otimizar_prompt_com_ia`
  chamavam `call_llm` sem `cli_args` e sem `cwd`: rodava `claude -p` sem `--tools ""` e fora da pasta
  temporária. Só o Enviar e o Sequenciar usavam o modo sem ferramentas.
- **Achado junto (documentação oficial, 27/11):** `--tools ""` não afeta ferramentas MCP, e `claude -p`
  carrega ganchos, plugins, skills e `CLAUDE.md`. Valia também para o Enviar e o Sequenciar.
- **Correção (27/11, no código):** ponto único em `_call_local_cli` (`backend/ai_hub.py`): todo uso do
  Claude dentro do app roda com `CLAUDE_ARGS_PROTEGIDOS` (`-p --safe-mode --tools "" --strict-mcp-config
  --disallowedTools "mcp__*"`), `CLAUDE_CODE_SAFE_MODE=1` e pasta temporária nova, apagada ao fim. Quem
  chama não muda argumentos nem pasta. Opção recusada pela versão instalada: aviso e bloqueio, sem
  nova tentativa sem proteção. Abrir no Terminal não mudou.
- **Testes:** `backend/tests/test_claude_protegido.py` (20 novos). Com autorização do dono (27/11), 3
  testes antigos tiveram só a conferência do comando e da pasta ajustada para exigir a proteção:
  `test_cli_local_passa_ataque_shell_apenas_por_stdin_com_shell_false`,
  `test_cli_recebe_timeout_longo_e_pasta_temporaria` e
  `test_chamadas_antigas_continuam_sem_cwd_e_com_timeout_curto` (o nome ficou antigo).
- **Limites:** ganchos de política de administrador continuam valendo (documentação); o texto pode
  ficar no histórico do Claude Code (`~/.claude`), anotado no PLANO (`--no-session-persistence`).
- **Situação:** testado em cópia em Linux com o Claude simulado. **No Mac (27/11, Claude 2.1.332,
  fora do app, mesmos argumentos):** com proteção, 0 ferramentas, 0 MCP e o gancho de teste não
  rodou; sem proteção, 157 ferramentas (129 MCP, incluindo Gmail e Drive) e o gancho rodou.
  `make check` passou. **Pelo app:** os cinco usos responderam, e o `ps` mostrou o Claude com as
  opções de proteção (detalhes no `docs/STATUS.md`).
- **Limite novo (visto no Mac):** com `--safe-mode`, 4 plugins `cc-plugin-*`, 20 skills e 5 agentes
  ainda carregam. Sem ferramentas não são acionáveis; ganchos próprios desses plugins não testados.

### Sequenciar com "continue" estoura o tempo com o Claude local (visto no Mac em 27/11, sem fase)
- **Sintoma:** depois de uma resposta com código, "continue" deu "Tempo esgotado (600s)". O app
  avisou e liberou o botão; logo depois, "Resuma em 3 linhas o que já foi feito" respondeu.
- **Causa provável:** sem ferramentas, o Claude escreve todo o código como texto; um "continue"
  pede uma resposta longa. Não medido se o modo seguro deixa a resposta mais lenta.
- **A avaliar:** orientar a pedir partes menores ou usar Abrir no Terminal; avaliar outro limite de tempo.

### Testes do backend dependem da versão do Python (achado em 27/11, sem fase definida)
- **Sintoma (cópia em Linux):** com Python 3.10, 8 testes falham quando a suíte roda inteira e
  passam isolados (igual antes e depois da correção do Claude local); com 3.13, todos passam. No Mac (3.15) e no CI (3.12), passam.
- **Causa provável:** `test_api_contract.py` troca métodos do objeto `main.ai_hub` com `monkeypatch`;
  ao desfazer, o método fica gravado no objeto e esconde trocas feitas depois na classe.
- **A avaliar:** declarar a versão mínima do Python ou ajustar esses testes com o OK do dono.

### Script temporário antigo executado por engano (incidente na fase 6, 27/11)
- **O que houve:** a gravação de `/tmp/ed.py` falhou (já existia um arquivo de outra sessão), e o
  comando seguinte executou o antigo. Ele inseriu trechos repetidos em `backend/prompt_engine.py`
  e parou em erro. Pelo `git status`, nenhum outro arquivo do projeto mudou.
- **Situação:** resolvido em 27/11. A restauração pela IA foi bloqueada pela trava de segurança da
  ferramenta; depois do passo a passo dado ao dono, o arquivo ficou igual ao do último commit
  (assinatura do Git conferida).
- **Evitar:** não usar arquivo de nome fixo em `/tmp`; só executar depois de a gravação dar certo.

### Login OpenRouter sem uso na tela (achado na fase 6, sem fase definida)
- **Visto no código:** existe a rota `/api/hub/openrouter/exchange`, mas o `App.tsx` não a chama.
- **A avaliar:** criar o botão ou remover a rota.

### Mensagem de permissão de Automação com caminho suspeito (achado na fase 6, sem fase definida)
- **Visto no código:** `MSG_SEM_AUTOMACAO` cita "System & App Protection Override > Terminal".
  O esperado é Privacidade e Segurança > Automação. Ela também cita só o Terminal.
- **Não conferido no Mac.**

### Testes do frontend não rodam no Node 20 (achado na fase 6)
- **Causa (código e documentação do Node, não testado):** `--experimental-strip-types` surgiu no
  Node 22.6; o `package.json` e o `Makefile` ainda aceitam 20.19.
- **Feito:** README e CONTRIBUTING pedem 22.12+ para o `make check`.
- **A avaliar:** ajustar a conferência de versão do `Makefile`.

### Botão "Estruturar com IA" não usa IA (achado na fase 6, sem fase definida)
- **Visto no código:** ele chama `/api/analisar-intencao`, que usa só o motor local.
- **A avaliar:** trocar o texto do botão.

### Resposta acima de 24.000 caracteres: o excedente se perde (sem fase definida)
- **Visto no Mac (26/11):** com Claude (Local) e com Antigravity, o aviso de resposta cortada apareceu.
- **Causa (código):** o app descarta o que passa de 24.000; isso também não vai para o histórico.
- **A avaliar:** orientar a usar Abrir no Terminal quando o projeto for grande.

### Sequenciar perde contexto em projeto grande (limitação conhecida)
- **Visto no Mac (26/11):** na 3ª rodada, uma rodada ficou de fora e a outra foi sem o meio.
- **Efeito:** a IA pode reescrever ou mudar o que não recebeu. O app não junta os arquivos das
  respostas.
- **A avaliar:** explicar isso na tela e no README. Ver a ideia da conversa na pasta do projeto,
  no `docs/PLANO.md`.

### Aviso do envio anterior fica na tela durante o Sequenciar (adiado pelo dono)
- **Sintoma:** enquanto o novo pedido roda, o rodapé ainda descreve o envio anterior.
- **Solução:** limpar o aviso ao iniciar o envio.

### Ganchos globais do Antigravity ficam fora da trava (limitação conhecida)
- **Sintoma possível:** um programa de memória ligado ao `agy` pode guardar o que o app envia.
- **Causa:** ganchos globais rodam independentemente do gancho da pasta temporária.
- **O que o app faz:** detecta ganchos globais e de plugins, avisa e exige aceite para enviar,
  revisar e otimizar. **O aviso não impede a gravação.** Não enviar dados de cliente.
- **Não confirmado:** se algum pedido chegou a ser gravado.

### Organizar ainda erra bastante com jeito de falar novo (melhorado na fase 5, segue aberto)
- **Sintoma (cópia em Linux, dados falsos):** em 30 frases leigas novas, com a biblioteca dobrada e
  congelada, 76% foram para o campo certo (original, 20%). Falharam Entrada, Regras de negócio e Erros.
- **Narrativa pessoal:** já virou Regra por engano; três tipos corrigidos, podem existir outros.
- **Causa:** a biblioteca reconhece formas de falar; não entende o sentido.
- **Já feito:** biblioteca `backend/regras_prompt/`, palavras inteiras, prioridades e exceções.
- **A fazer:** ampliar com frases de outras pessoas; avaliar a IA ativa como opção, com aviso.
- **Limite:** texto ditado sem pontuação não é dividido em frases.

### Organizar recusa prompt grande do próprio app (achado na fase 5, sem fase definida)
- **Sintoma (medido em teste):** com Contexto de 2.000 e quatro campos de 1.500 caracteres, o
  prompt gerado teve 8.948; o Organizar aceita 8.000. A tela mostra o contador e não envia.
- **A avaliar:** aumentar o limite (a rota aceita até 20.000), com teste novo.


### Histórico para de guardar após 50 rodadas, sem aviso (sem fase definida)
- **Sintoma (visto no código):** a partir da 51ª, a resposta aparece na tela, mas não é salva.
- **Causa:** `salvar_rodada` devolve vazio no limite e a rota não avisa.
- **Solução:** avisar na tela.

## Corrigido na fase 7 (27/11): alertas do CodeQL no Pull Request #1

### Motivo do erro da IA ia para a tela sem filtro (CodeQL #14 a #18)
- **Causa:** na revisão e na otimização com IA, quando a IA falhava, o texto do erro entrava em
  `dica_extra` e `aviso` sem passar por `mensagem_publica` (podia mostrar caminho de pasta).
- **Solução:** os dois textos passam por `mensagem_publica`. Teste novo:
  `backend/tests/test_erro_ia_filtrado.py` (falha sem a correção, conferido em cópia em Linux).
- **Limite:** o CodeQL pode continuar apontando, porque não reconhece o filtro; aí o alerta é
  dispensado com justificativa. Os 5 alertas vêm da mesma origem, porque as rotas usam a mesma
  função auxiliar (`_run_domain_action`).

### Alertas dispensados por análise (falso positivo ou só em teste)
- **#13 "Clear-text logging" (High):** o caminho do CodeQL começa na rota de login do OpenRouter
  e chega ao log do envio automático pela função auxiliar comum. Na prática o log grava só o
  status fixo do envio. A rota do OpenRouter segue sem uso na tela (item já anotado acima).
- **#19 "Incomplete URL substring sanitization" (High, teste):** só no teste; o código de
  produção compara o host inteiro (`envio_automatico._host_ok`).
- **Check "Code scanning results / CodeQL" com "1 configuration not found":** não obrigatório;
  causa não confirmada.

## Corrigido na fase 6 (27/11)

### 10. CI não rodava os testes do frontend
- **Solução:** `npm test` no job do frontend.
- **Confirmado no GitHub (27/11):** `frontend` verde no Pull Request #1 e na `main` após o merge.

### 11. README e SECURITY desatualizados
- **Solução:** atualizados a partir do código (chave de API, Sequenciar, link com o prompt, envio
  automático, Já tenho um prompt, segurança, estrutura e rotas).
- **Evitar:** atualizar a documentação na mesma fase da mudança.

## Corrigido na fase 5 (27/11): testado em Linux e conferido no Mac pelo dono

### Organizar cortava regras sem aviso
- **Sintoma:** acima de 20 regras (limite da época) o excedente sumia; regra acima de 2.000 caracteres era cortada.
- **Causa:** o corte não gerava aviso.
- **Solução:** o máximo subiu para 50 regras (os outros limites não mudaram). A tela avisa, mostra o que ficou de fora (inclusive o final de
  campo cortado) e pede confirmação antes de preencher o formulário.
- **Limite:** a lista some quando o painel fecha; a pessoa precisa copiar antes.
- **Evitar:** `backend/tests/test_organizar_cortes.py`.

### 8. Organizar prompt bagunçava o prompt do próprio app
- **Sintoma:** o Contexto entrava no Objetivo (e linhas dele iam para Stack e Regras), a frase do
  Padrão virava regra, uma regra com `;` virava duas e o texto automático de Erros voltava como
  resposta da pessoa.
- **Causa:** o texto do próprio app era lido como texto qualquer.
- **Solução:** o formato do app é reconhecido e lido por seção; o Contexto sai à parte.
- **Limites:** a leitura exata vale para o prompt sem edição. Se for editado, o Contexto continua
  separado quando vier no começo e antes de `### Objetivo`, mas o resto usa a leitura comum. Um
  Padrão escrito pela pessoa vai para Regras.
- **Evitar:** teste de ida e volta (`backend/tests/test_organizar_ida_e_volta.py`).

## Corrigidos na fase 4 (26/11): testados em Linux e conferidos no Mac

O que foi e o que não foi conferido no Mac está no `docs/STATUS.md`.

### 4. Conferência de origem do servidor incompleta
- **Causa:** a origem era conferida pelo nome, sem a porta.
- **Solução:** compara a origem inteira: a do próprio app (porta em uso) e as duas do Vite.
- **Efeito:** se o Vite subir em outra porta (ex.: 5174), as alterações são recusadas.
- **Evitar:** comparar a origem completa.

### 5. Envio automático não conferia a aba
- **Solução:** o script confere, antes do ⌘V e antes do Enter, se o navegador está na frente e se a
  aba tem o endereço do perfil (aceita `?` ou `#` no fim). Se não, para e deixa o texto copiado.
- **Limites:** sobra um instante entre conferir e teclar; não sabe se o cursor está na caixa de
  texto. No Mac, compilou para Safari e Chrome; envio e parada conferidos pelo dono.

### 6. Privacidade no link com `?q=`
- **Solução (escolha do dono):** janela de aviso **toda vez** que o prompt iria no endereço, com
  ciência obrigatória para "Abrir preenchido", e as opções "Só copiar e abrir" e "Cancelar".
- **Limites:** não impede dado de cliente no site. O envio automático tem aviso próprio.

### 7. Filtro anti-injeção bloqueava texto comum
- **Solução:** "Linguagem JavaScript: Node" passa; `javascript:` seguido de código continua
  bloqueado. README e SECURITY chamam o filtro de básico.
- **Limites:** continua uma lista de padrões, que não pega toda injeção. "JavaScript:Node", sem
  espaço, ainda é bloqueado.

### 12. Sem registro de erros
- **Solução:** `~/.power_request/power_request.log` (cerca de 100 KB, mais uma cópia), com data,
  método, rota, código e tipo. Sem mensagem, prompt, resposta ou chave.
- **Limite:** só é ligado ao abrir pelo app ou `make run` (não no `make dev`). Falha antes do
  servidor subir não é registrada.

### Permissões do banco
- **Solução:** 700 na pasta e 600 no banco e no log, inclusive nos antigos. Não é criptografia.

### Aviso falso de "o navegador bloqueou a nova aba" (achado na fase 4)
- **Causa:** com `noopener`, `window.open` devolve vazio mesmo quando a aba abre (confirmado em
  Chromium). O app tratava isso como bloqueio.
- **Solução:** a tela não afirma mais isso; diz o que fazer se a aba não abrir. Corrigido junto
  porque a mensagem fazia parte do fluxo novo do item 6.
- **Evitar:** não usar o retorno de `window.open` com `noopener`.

## Já resolvidos ou com solução conhecida

Os quatro primeiros são da fase 3 (26/11): testados com IA simulada, falta conferir no Mac.

### 2. Sequenciar falhava com resposta longa
- **Solução:** orçamento único em `montar_continuacao`, com o limite do envio. Corta as respostas
  antigas primeiro; se a mais recente não couber, mantém o começo e o fim.
- **Evitar:** testar os limites das duas pontas juntos.

### Sequenciar falhava depois de 30 rodadas
- **Causa:** a tela reenviava todas as rodadas e o servidor aceita no máximo 30.
- **Solução:** a tela reenvia só as 3 últimas e informa quantas são anteriores.

### 3. Prompt gerado podia não ser enviável
- **Solução:** a tela mostra o tamanho e desativa o Enviar acima do limite (`limite_envio`).
- **Evitar:** todo limite aparece antes do clique.

### 9. Resposta podia chegar cortada sem aviso
- **Solução:** conferir o motivo da parada na API e o corte de 24.000 do CLI; aviso na tela e marca
  no histórico.
- **Limite:** se o próprio programa de IA local encurtar a resposta, o app pode não saber.

### 13. Antigravity aparece offline (resolvido, conferido no Mac em 26/11)
- **Sintoma:** o teste de conexão do Antigravity (Local) falha, mesmo com o `agy` funcionando.
- **Causa (confirmada no Mac, agy 1.5.18):** o app chamava `agy -p` e mandava o texto pela entrada
  padrão; o `agy` responde `flag needs an argument: -p`.
- **Risco que motivou a trava:** no Mac testado, sem o gancho, o `agy` criou arquivo e executou
  comando sem pedir aprovação, mesmo informando `request-review`.
- **Solução:** `backend/agy_seguro.py`: `stream-json` pela entrada padrão, gancho `PreToolUse` que
  recusa tudo, prova no Testar Conexão e bloqueio se aparecer ferramenta sem a recusa.
- **Limites:** o bloqueio por detecção não desfaz a ação e some ao reiniciar o app (a prova é
  exigida de novo). Se o `agy` deixar de carregar o gancho sem mudar de versão, e depois da
  prova, a detecção só age quando uma ferramenta já tiver aparecido. `gemini` não é usado no app.
- **Evitar:** não usar CLI com ferramentas sem provar a trava no programa real.

### Confirmação do Copiar Prompt ficava fora da vista (corrigido em 26/11, aprovado pelo dono no Mac)
- **Sintoma:** o prompt era copiado, mas parecia que não havia confirmação.
- **Causa:** a mensagem aparecia no fim do quadro, longe do botão.
- **Solução:** o próprio botão mostra "Copiado ✓" por 2 segundos; se a cópia falhar, o aviso
  aparece logo abaixo dele.

### Mensagens de erro podiam expor detalhes internos
- **Solução:** filtro central `mensagem_publica` (commit `c619eb4`).
- **Evitar:** erro novo para a tela passa pelo filtro.

### Chave de API guardada no navegador sem pedir
- **Solução:** fica só na memória; salvar é opt-in (commit `d21a715`).

### Vulnerabilidades apontadas pelo `npm audit`
- **Solução:** atualização do Vite (commit `5701a50`). Depois de trocar de branch com dependências
  novas, rodar `cd frontend && npm ci`.

### "Ambiente Python não encontrado" ao abrir o app
- **Solução:** `make setup`.

### "Interface ainda não compilada"
- **Solução:** `make build`.

### Teste de conexão com Claude (Local) falha
- **Solução:** rodar `claude` no Terminal e fazer login.

### Envio automático bloqueado pelo macOS
- **Sintoma:** o app avisa que o macOS bloqueou o teclado ou o controle do navegador.
- **Causa:** falta permissão de Acessibilidade ou de Automação.
- **Solução:** liberar em Ajustes do Sistema > Privacidade e Segurança, conforme a mensagem do
  app, e usar **Testar automação** (confere o teclado; não testa o controle do navegador).
  O texto fica copiado: dá para colar à mão.
