# Histórico de versões

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); números de versão
seguem [SemVer](https://semver.org/lang/pt-BR/). Só o macOS foi testado.

## [Não lançado]

### Adicionado
- Botão vermelho **Fechar**, no canto superior direito, com janela de confirmação, para desligar o app sem usar o Terminal. Não
  fecha enquanto o Enviar ou o Sequenciar estiverem esperando resposta.

## [2.1.2] - 2026-11-27

### Segurança
- No uso normal, o app só atende por `127.0.0.1` (`localhost` é recusado).
- O Abrir no Terminal recusa, no Claude, prompt de uma palavra só.
- O limite de 1 MB vale também para pedidos enviados em partes.
- O endereço do Ollama aceita só `localhost` ou `127.0.0.1` com porta, sem usuário, caminho ou
  consulta.
- A chave de API não é repetida quando há redirecionamento.
- Erros de formato (422) não devolvem mais o que foi enviado.
- O texto apagado do histórico é sobrescrito no banco; Limpar tudo também compacta o arquivo.
- As ações do CI ficam presas a um commit exato.

### Removido
- A rota do login OpenRouter, que a tela não usava. A conexão por chave de API não muda.

## [2.1.1] - 2026-11-27

### Segurança
- Corrige duas falhas presentes na 2.1.0: no uso normal, o app não confia mais na porta 5173 de
  desenvolvimento; e o Abrir no Terminal recusa, no Claude, prompt que começa com "-".

## [2.1.0] - 2026-11-27

### Adicionado
- **Enviar pelo navegador:** link que abre ChatGPT ou Claude com o prompt preenchido, com janela de
  aviso toda vez e a opção "Só copiar e abrir".
- **Envio automático pelo site da IA** (opcional, macOS): abre o site, cola e envia. Perfis do Claude
  (validado no Mac) e do ChatGPT (ainda não validado).
- **Sequenciar:** continuar a conversa com as respostas guardadas no histórico.
- **Revisão mais esperta:** avisa Stack, Input e Output vagos.
- **Organizar prompt** e a tela "Já tenho um prompt", com a biblioteca de regras
  (`backend/regras_prompt/`) para texto corrido; avisa o que ficou de fora.
- Animação de espera no Enviar e no Sequenciar; o botão usado vira a animação.
- Tamanho do prompt mostrado antes do envio e aviso de resposta cortada.
- Log local de falhas, sem prompt, resposta ou chave (`~/.power_request/power_request.log`).
- Memória do projeto para quem continuar o trabalho (`CLAUDE.md`, `docs/`).

### Alterado
- Enviar e Sequenciar ficam desativados com a IA offline, com o motivo e "Testar de novo".
- Confirmação "Copiado ✓" no próprio botão Copiar Prompt.
- O CI também roda os testes do frontend.

### Segurança
- **Claude (Local) dentro do app** (Testar Conexão, revisão, otimização, Enviar e Sequenciar):
  sempre com `--safe-mode`, sem ferramentas internas nem MCP, numa pasta temporária vazia.
  Versão que não aceita esse modo é bloqueada.
- **Antigravity dentro do app:** trava que recusa ferramentas, provada no Testar Conexão; aviso e
  aceite quando há ganchos globais. O Gemini CLI fica só no Abrir no Terminal.
- O servidor compara a origem inteira (protocolo, nome e porta).
- O envio automático confere a aba antes de colar e de enviar.
- Revisão e otimização com IA: o motivo da falha passa pelo filtro de mensagens (sem caminhos de pasta).
- Pasta de dados com permissão 700; banco e log com 600 (não é criptografia).
- Filtro anti-injeção deixou de bloquear texto comum como "Linguagem JavaScript: Node".

### Corrigido
- Antigravity aparecia offline.
- Sequenciar falhava com resposta longa ou depois de 30 rodadas.
- Organizar bagunçava o prompt gerado pelo próprio app.
- Aviso falso de "o navegador bloqueou a nova aba".

### Limites conhecidos
Lista completa em [docs/ERROS.md](docs/ERROS.md). Os principais:
- Ganchos de política de administrador e alguns plugins internos do Claude continuam carregando.
- Ganchos globais do Antigravity ficam fora da trava (o app avisa).
- Sequenciar com "continue" pode estourar os 10 minutos no Claude local.
- Organizar ainda erra com jeitos de falar novos.
- Linux e Windows não testados.

## [2.0.0]
Versão publicada antes deste histórico (até o commit `b21ce46`), sem registro detalhado.

[2.1.2]: https://github.com/Seraphim82/power-request/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/Seraphim82/power-request/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/Seraphim82/power-request/compare/b21ce46...v2.1.0
