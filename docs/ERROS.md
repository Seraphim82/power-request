# Erros conhecidos

Formato: sintoma, causa, solução e como evitar. Nunca colar aqui chave, prompt, resposta ou dado de cliente.
Os números seguem a análise de 26/11/2026 (o item 1, trabalho sem commit, foi resolvido na fase 1).

## Em aberto

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

### 4. Conferência de origem do servidor incompleta (fase 4)
- **Sintoma:** a proteção aceita mais origens locais do que deveria.
- **Causa:** a origem é conferida pelo nome, sem a porta.
- **Solução:** aceitar a origem exata do app e as duas do Vite. Teste novo.
- **Evitar:** comparar a origem completa.

### 5. Envio automático não confere a aba (fase 4)
- **Sintoma possível:** texto colado fora do site da IA se a aba mudar durante a espera
  (visto na leitura do código; não reproduzido no Mac).
- **Causa:** as teclas são enviadas sem conferir o endereço da aba da frente.
- **Solução:** conferir o domínio antes das teclas; se não bater, parar e deixar o texto copiado.
- **Evitar:** nunca digitar sem confirmar o destino. **Até corrigir:** não trocar de aba nem de
  janela durante o envio.

### 6. Privacidade no link com `?q=` (fase 4)
- **Sintoma:** o prompt vai dentro do endereço aberto no navegador.
- **Causa:** forma de preencher a caixa de texto do site.
- **Solução:** avisar na tela e oferecer "só copiar e abrir" (escolha pendente).
- **Evitar:** não pôr dado de cliente em prompt aberto por link.

### 7. Filtro anti-injeção é básico (fase 4)
- **Sintoma:** bloqueia texto legítimo (ex.: "Linguagem JavaScript: Node") e não pega todas as
  frases de injeção.
- **Causa:** lista de padrões fixos.
- **Solução:** corrigir o falso positivo e descrever o filtro como básico no README e no
  SECURITY. Se um teste antigo depender do comportamento atual, parar e conversar.
- **Evitar:** não tratar o filtro como garantia de proteção.

### 12. Sem registro de erros (fase 4)
- **Sintoma:** quando algo falha, não fica rastro.
- **Causa:** o backend não usa `logging`.
- **Solução:** log local curto, sem chave, prompt ou resposta.

### Permissões do banco (fase 4)
- **Sintoma:** numa cópia de teste em Linux, a pasta saiu com 755 e o arquivo com 644
  (não conferido no Mac).
- **Causa:** o app não define as permissões. O histórico não é criptografado pelo app.
- **Solução:** 700 na pasta e 600 no arquivo.

### 8. Organizar prompt bagunça o prompt do próprio app (fase 5)
- **Sintoma:** o Contexto entra no Objetivo e a seção Padrão vira regra.
- **Causa:** essas seções não são reconhecidas à parte.
- **Solução:** tratar Contexto e Padrão separados antes de criar a tela.
- **Evitar:** teste de ida e volta (gerar e depois organizar).

### 10. CI não roda os testes do frontend (fase 6)
- **Causa:** `.github/workflows/ci.yml` não chama `npm test`.
- **Solução:** acrescentar ao job do frontend.
- **Evitar:** o CI deve cobrir o mesmo que o `make check`.

### 11. README e SECURITY desatualizados (fase 6)
- **Sintoma:** dizem que a chave de API fica no `localStorage`; o padrão atual é só na memória.
  O README não explica o Sequenciar nem o envio automático.
- **Solução:** atualizar os dois, incluindo a permissão que o envio automático pede.
- **Evitar:** atualizar a documentação na mesma fase da mudança.

### Histórico para de guardar após 50 rodadas, sem aviso (sem fase definida)
- **Sintoma (visto no código):** a partir da 51ª, a resposta aparece na tela, mas não é salva.
- **Causa:** `salvar_rodada` devolve vazio no limite e a rota não avisa.
- **Solução:** avisar na tela.

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
