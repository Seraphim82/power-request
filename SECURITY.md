# Segurança

O Power Request roda **só no seu computador** (`127.0.0.1`) e não envia nada para servidores do projeto.
Suas chaves de API ficam apenas no navegador (`localStorage`) e o histórico fica em `~/.power_request/`.

## Como reportar uma vulnerabilidade

**Não abra uma issue pública** para falhas de segurança.
Use **Security → Report a vulnerability** neste repositório (relato privado do GitHub).
Descreva o que encontrou, como reproduzir e o impacto. Respondo assim que possível.

## O que está no escopo

- Execução de comandos ou leitura de arquivos além do esperado (Enviar e Abrir no Terminal)
- Acesso ao servidor local por sites externos (CSRF, DNS rebinding)
- Vazamento de chaves de API ou do histórico
- Injeção em prompts que contorne os filtros do motor local (o filtro é básico: uma lista de padrões, não uma garantia de proteção)

Veja a seção **Segurança** do README para o modelo de proteção atual.
