# Erros conhecidos

Formato: sintoma, causa, solução e como evitar. Nunca colar aqui chave, prompt, resposta ou dado de cliente.
Os números seguem a análise de 26/11/2026 (o item 1, trabalho sem commit, foi resolvido na fase 1).

## Em aberto

### 2. Sequenciar falha com resposta longa (fase 3)
- **Sintoma:** erro ao sequenciar depois de uma resposta grande.
- **Causa:** `montar_continuacao` aceita até 12.000 caracteres por resposta anterior (até 3), mas
  o envio recusa acima de 11.000 no total (`MAX_SEND_PROMPT_CHARS`). O CLI local ainda limita a
  12.000 já com as instruções.
- **Solução:** orçamento único de tamanho que respeite os dois limites. Teste novo pela API.
- **Evitar:** testar os limites das duas pontas juntos, não cada função sozinha.

### 3. Prompt gerado pode não ser enviável (fase 3)
- **Sintoma:** o app gera o prompt e depois o Enviar recusa pelo tamanho.
- **Causa:** não há limite de quantidade de regras.
- **Solução:** mostrar o tamanho na tela e avisar antes de enviar.
- **Evitar:** todo limite de envio deve aparecer antes do clique em Enviar.

### 9. Resposta pode chegar cortada sem aviso (fase 3)
- **Sintoma:** resposta incompleta, sem mensagem.
- **Causa:** envio limitado a 4.096 tokens sem conferir o motivo da parada; no CLI, corte em
  24.000 caracteres.
- **Solução:** detectar o corte e avisar na tela.
- **Evitar:** todo corte precisa ser informado.

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

## Já resolvidos ou com solução conhecida

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
