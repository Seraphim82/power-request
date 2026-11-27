# Segurança

O servidor do Power Request roda **só no seu computador** (`127.0.0.1`), e o projeto não tem servidores próprios.
O histórico fica em `~/.power_request/`, com acesso restrito ao seu usuário, mas **sem criptografia**.

**O texto pode sair do computador** quando você usa uma IA que não seja um modelo rodando nele:
Enviar, Sequenciar, revisão ou otimização com IA, Abrir no Terminal, envio automático e os botões
que abrem o site de uma IA. Isso inclui os programas de IA do Terminal (Claude, Antigravity),
que falam com o serviço deles.

- **Chave de API:** por padrão fica só na memória. Guardar no navegador (`localStorage`, sem criptografia) é escolha sua.
- **Link com o prompt:** no ChatGPT e no Claude, o texto pode ir no endereço. O app avisa antes, toda vez; o site o recebe ao abrir a página e ele pode ficar no histórico do navegador.
- **Envio automático (opcional, macOS):** usa as permissões de Acessibilidade e Automação do macOS. Confere a aba antes das teclas, o que reduz o risco, mas não o elimina.
- **Ganchos globais do Antigravity:** a trava de ferramentas não os desliga, e eles podem guardar o que for enviado. O app avisa e pede aceite.
- **Claude local dentro do app:** roda sem ferramentas internas nem MCP, sem ganchos e plugins do usuário e numa pasta temporária vazia, em todos os usos (Testar Conexão, revisão, otimização, Enviar e Sequenciar). Se a versão não aceitar esse modo, o app bloqueia. **Limites:** ganchos impostos por política de administrador continuam valendo, e alguns plugins internos do Claude continuam carregando, sem ferramentas (veja o README). O **Abrir no Terminal** continua com as ferramentas do próprio Claude, de propósito.

Não envie dados de clientes, senhas nem informações sigilosas.

## Como reportar uma vulnerabilidade

**Não abra uma issue pública** para falhas de segurança.
Use **Security → Report a vulnerability** neste repositório (relato privado do GitHub).
Descreva o que encontrou, como reproduzir e o impacto. Respondo assim que possível.

## O que está no escopo

- Execução de comandos ou leitura de arquivos além do esperado (Enviar, Sequenciar, revisão com IA, Testar Conexão e Abrir no Terminal)
- Envio automático: texto colado ou enviado no lugar errado
- Acesso ao servidor local por sites externos (CSRF, DNS rebinding)
- Vazamento de chaves de API ou do histórico
- Injeção em prompts que contorne os filtros do motor local (o filtro é básico: uma lista de padrões, não uma garantia de proteção)

Veja a seção **Segurança** do README para o modelo de proteção atual.
