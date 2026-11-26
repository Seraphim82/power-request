# Status do projeto

Atualizado em 26/11/2026.

## Onde parou

- **Fases 1 e 2:** concluídas. A fase 2 está no commit local `a90d94c`, **não enviado**.
- **Fase 3 (envio):** concluída e commitada (`ba6310d`) na branch `feat/organizar-prompt`, não enviada.
  Sequenciar com orçamento único de tamanho, contador de caracteres e aviso de resposta cortada.
  Escolha confirmada pelo dono em 26/11: faltando espaço, cortar primeiro as respostas mais antigas.
- **Correção do Antigravity (item 13 do ERROS):** commitada em 26/11, não enviada. No Mac:
  `make check` passou e o Antigravity ficou online no app (informado pelo dono). Enviar, aviso de
  ganchos e Sequenciar com ele **ainda não conferidos**.
- **`main`:** ainda sem merge (parada no commit `b21ce46`).

## Próximo passo

1. Conferir no app, no Mac, com o Antigravity: aviso de ganchos, Enviar e Sequenciar.
2. Botão Enviar apagado com a IA offline (ver `docs/PLANO.md`).
3. **Fase 4 (segurança)**, em outro chat. Antes, confirmar a escolha pendente do `?q=`.
4. Push só depois da fase 4 (o repositório é público e os documentos citam falhas abertas).

## O que o app tem hoje

- Gerar prompt, revisão (avisa Stack, Input e Output vagos), histórico e Contexto fixo.
- Hub de IAs, Enviar e Abrir no Terminal (macOS).
- Sequenciar (continuar a conversa com as respostas guardadas), dentro do limite de envio.
- Abrir a IA no navegador por link com o prompt, quando o site e o tamanho permitem.
- Envio automático (opcional, macOS): perfis do Claude e do ChatGPT.
- Organizar prompt: só no backend, ainda sem tela e com defeito conhecido.

## Testes

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
- **Falta no Mac:** aceite do aviso, Enviar e Sequenciar com o Antigravity.

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

- Testes de tela (Playwright) citados em anotações antigas não estão no repositório.
- Nenhum Pull Request havia sido aberto até a última anotação (23/11); conferir no GitHub.
