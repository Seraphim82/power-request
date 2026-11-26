# Status do projeto

Atualizado em 26/11/2026.

## Onde parou

- **Fase 1 (salvar):** concluída. Branch `feat/organizar-prompt` enviada ao GitHub
  (commits `265133b` e `cc7b0a4`).
- **Fase 2 (memória do projeto):** documentos criados (`CLAUDE.md` e `docs/`).
  Conferir no `git log` e no `git status` se já foram commitados e enviados.
- **`main`:** ainda sem merge (parada no commit `b21ce46`).

## Próximo passo

**Fase 3 (envio)**, em um chat novo. Antes de codar, confirmar a escolha pendente do Sequenciar
(ver `docs/PLANO.md`).

## O que o app tem hoje

- Gerar prompt, revisão (avisa Stack, Input e Output vagos), histórico e Contexto fixo.
- Hub de IAs, Enviar e Abrir no Terminal (macOS).
- Sequenciar (continuar a conversa com as respostas guardadas). Falha com resposta longa.
- Abrir a IA no navegador por link com o prompt, quando o site e o tamanho permitem.
- Envio automático (opcional, macOS): perfis do Claude e do ChatGPT.
- Organizar prompt: só no backend, ainda sem tela e com defeito conhecido.

## Testes

Última conferência no Mac (26/11/2026, depois do `npm ci`): 239 testes de backend e 7 de frontend,
checagem de tipos e build OK, `npm audit` sem vulnerabilidades. Vite 8.3.8.
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
