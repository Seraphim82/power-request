# Como opinar e contribuir

Obrigado por ajudar! Todo tipo de retorno vale: bug, ideia, dúvida de uso.

- **Achou um problema ou tem uma ideia?** Abra uma [issue](../../issues/new/choose).
- **Quer mexer no código?** Abra uma issue antes para combinarmos o rumo e depois um Pull Request.
- **Falha de segurança?** Não use issue pública: veja [SECURITY.md](SECURITY.md).

## Rodando localmente

```bash
make setup   # instala backend e frontend (precisa de Python 3.10+ e Node 22.12+ para o make check)
make check   # testes do backend e do frontend + typecheck + build
make run     # abre em http://127.0.0.1:8765
```

## Regras do projeto

- `make check` precisa passar antes de qualquer Pull Request.
- **Não altere testes existentes só para fazê-los passar.** Se um teste está errado, explique por quê no PR.
- Mudanças de segurança (filtros, Origin/Host, execução de CLI, envio automático) precisam de teste novo.
- Texto da interface em português do Brasil.
