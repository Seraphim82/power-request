# Plano de melhorias

Origem: análise de 26/11/2026. Uma fase por chat, com teste, atualização do STATUS e commit.
Nenhum teste existente é alterado. Detalhes de cada item em `docs/ERROS.md`.

## [x] Fase 1: salvar
- **Objetivo:** proteger o trabalho.
- **Tarefas:** ajustar o `.gitignore`, commitar e enviar.
- **Pronto quando:** commit feito e branch no GitHub.

## [ ] Fase 2: memória do projeto
- **Objetivo:** um chat novo recuperar o contexto.
- **Tarefas:** criar `CLAUDE.md`, `docs/STATUS.md`, `docs/ERROS.md` e `docs/PLANO.md`.
- **Pronto quando:** um chat novo souber onde parou só lendo os arquivos, e eles estiverem
  commitados.

## [ ] Fase 3: envio (itens 2, 3 e 9)
- **Objetivo:** envio previsível.
- **Tarefas:** orçamento único no Sequenciar; mostrar o tamanho e avisar antes de enviar; detectar
  e avisar resposta cortada; testes novos.
- **Pronto quando:** resposta longa não quebra o Sequenciar e todo corte é avisado.
- **Confirmar antes:** proposta de, faltando espaço, cortar primeiro as respostas mais antigas e
  avisar na tela. *Ainda sem OK.*

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

## Depois da fase 8
- `docs/MANUTENCAO.md`, `docs/COMO-PEDIR-MUDANCAS.md`, documento curto de funcionamento (FSD)
  e `DESIGN.md`.
- Testes de tela no repositório e no CI; depois dividir o `App.tsx`.
- Fixar versões das dependências Python; verificador de código (ex.: Ruff).
- Backup e numeração de versão do banco antes de mudar tabelas.
- Conferir na documentação oficial os nomes de modelos fixos no código.
- Ideias: janela própria e instalador para quem não usa Terminal; perfil do Gemini; ctxpack no
  Sequenciar, se necessário.
