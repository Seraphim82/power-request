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

## [ ] Correção do Antigravity (item 13), em chat próprio
- **Ordem:** depois do commit da fase 3; sugestão: antes da fase 4. *A confirmar com o dono.*
- **Tarefas:** primeiro provar no Mac, com arquivo de teste sem valor, que a trava bloqueia as
  ferramentas; usar `stream-json` pela entrada padrão (prompt fora dos argumentos); pasta
  temporária também no teste de conexão e na revisão; recusar a resposta se aparecer uso de
  ferramenta (só detecta, não impede); manter o caminho do `gemini` separado; testes novos.
- **Mensagem de erro:** trocar o texto técnico (visto no app: erro código 2) por um aviso em
  português que diga o que fazer.
- **Pronto quando:** conecta e envia, com o bloqueio comprovado. Se não der para bloquear, o Enviar
  fica desativado para o Antigravity.

## [ ] Enviar apagado com IA offline (sugestão do dono, 26/11)
Sugestão de encaixe: junto da correção do Antigravity.
- **Tarefas:** desativar Enviar e Sequenciar só quando o estado for `offline` (não em
  `desconhecido` nem `verificando`, a decidir no plano); explicar o motivo em português simples,
  com opção de testar de novo; manter Copiar Prompt; teste novo.
- **Pronto quando:** com a IA offline não dá para enviar, e a pessoa sabe o que fazer.

## [ ] Fase 4: segurança (itens 4 a 7 e 12, e permissões do banco)
- **Objetivo:** fechar as brechas conhecidas.
- **Tarefas:** origem exata; conferir a aba antes das teclas; aviso de privacidade; corrigir o
  falso positivo do filtro; log local sem dados sensíveis; permissões 700 e 600; testes novos.
- **Pronto quando:** outra porta é recusada e as teclas não vão para outro site.
- **Confirmar antes:** proposta de manter o `?q=` como padrão, com aviso e a opção "só copiar e
  abrir". *Ainda sem OK.*

## [ ] Fase 5: Organizar prompt (item 8 e a tela)
- **Objetivo:** terminar a função.
- **Tarefas:** reconhecer Contexto e Padrão à parte; depois criar a tela.
- **Pronto quando:** gerar e organizar devolve os campos sem misturar.

## [ ] Fase 6: CI e documentos (itens 10 e 11)
- **Objetivo:** verificação e documentação fiéis ao app.
- **Tarefas:** `npm test` no CI; atualizar README e SECURITY.
- **Pronto quando:** o CI roda tudo e o README bate com o app.

## [ ] Fase 7: versão
- **Objetivo:** publicar uma versão marcada.
- **Tarefas:** Pull Request e merge, tag, `CHANGELOG.md`. Para desfazer algo publicado,
  usar `git revert`.
- **Pronto quando:** `main` atualizada e com tag.

## [ ] Fase 8: revisão de segurança
- **Objetivo:** olhar de novo, em chat novo.
- **Tarefas:** revisar o código e as proteções.
- **Pronto quando:** relatório sem pendência crítica ou alta.

## Depois da fase 4: conversa completa na pasta do projeto do cliente
Ideia do dono (26/11), a fazer em chat próprio.
- **Objetivo:** no Abrir no Terminal, a IA poder consultar respostas cortadas do Sequenciar.
- **Como:** o app salva a conversa em um arquivo na pasta escolhida e o pedido aponta para ele.
- **Cuidados:** só a pedido da pessoa; permissão 600; não sobrescrever arquivo alheio; não seguir
  atalho (link simbólico); impedir que vá para o Git; tratar o conteúdo como dado, não instrução;
  recusar a pasta do próprio repositório. Teste novo.
- **Fora:** liberar ferramentas ou arquivos no botão Enviar.

## Ajustes anotados, ainda sem fase (encaixar quando o dono decidir)
- Limpar o aviso do envio anterior ao iniciar um novo Sequenciar.
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
