# Power Request: regras para a IA

App local (FastAPI + React/Vite), usado no macOS, que transforma uma ideia em um prompt estruturado.

## Antes de começar (ler nesta ordem)

1. `docs/STATUS.md`: onde o projeto parou.
2. `docs/PLANO.md`: qual é a fase da vez.
3. `docs/ERROS.md`: problemas conhecidos e já resolvidos.
4. `README.md`: como o app funciona (há trechos desatualizados, ver `docs/ERROS.md`).

Confira com `git status` e `git log --oneline -5` se o STATUS ainda bate com o repositório.
Se não bater, avise antes de mexer.

## Regras fixas

- **Segurança é prioridade.**
- **Nunca altere um teste existente para fazê-lo passar.** Se o teste parecer errado, pare e explique.
- Explique o plano e espere o OK antes de editar o código.
- Uma fase por chat. Não misture fases.
- Achado ou sugestão nova: anotar em `docs/ERROS.md` (falha) e `docs/PLANO.md` (ação).
  Anotar não é executar: nada é feito fora da ordem do plano.
- Mudança de segurança (filtro, Origin/Host, execução de CLI, envio automático) exige teste novo.
- Fale em português do Brasil, informal e direto. O dono não é técnico e usa o Terminal:
  dê os comandos passo a passo e diga o resultado esperado.
- Texto da interface em português do Brasil.
- Não diga que algo foi testado no Mac, ou com uma IA real, se não foi. Testes com simulação são
  simulação.

## Segurança do código

- O servidor atende só `127.0.0.1`/`localhost`.
- O prompt nunca entra em comando de shell nem em texto de script.
- CLIs locais: só os da lista fixa, sem shell.
- Chave de API fica só na memória; guardar no navegador é escolha da pessoa.
- Erros mostrados na tela passam por `mensagem_publica` (`backend/main.py`).
- Nunca registrar em log ou documento: chave, token, prompt, resposta ou dado de cliente.
- O repositório é **público**: nada pessoal ou sigiloso em arquivo versionado.

## Comandos (na raiz do projeto)

| Comando | Para quê |
|---|---|
| `make setup` | instala o backend e o frontend |
| `make check` | testes do backend e do frontend, tipos e build |
| `make run` | abre em http://127.0.0.1:8765 |
| `make app` | gera o `Power Request.app` |

## Onde está cada coisa

| Arquivo | Conteúdo |
|---|---|
| `backend/main.py` | rotas e proteções do servidor |
| `backend/prompt_engine.py` | motor local, filtro, Sequenciar e Organizar prompt |
| `backend/ai_hub.py` | provedores de IA, envio e Abrir no Terminal |
| `backend/envio_automatico.py` e `backend/perfis_sites.json` | envio automático pelo site (macOS) |
| `backend/history_store.py` | histórico em SQLite |
| `backend/tests/` | testes do backend |
| `frontend/src/App.tsx` | tela |
| `frontend/src/abrirNaIa.ts` | link que abre a IA com o prompt (teste ao lado) |

## Git

- `make check` precisa passar antes de commitar código.
- `git add` arquivo por arquivo, não `git add .`.
- Commit e push só quando o dono pedir. E-mail do commit: o `noreply` do GitHub.
- Nunca colocar token em comando, arquivo ou chat.
- Há um stash antigo (`envio-automatico-experimental`): não aplicar nem apagar sem conversar.
- Fora do Git de propósito: `Power-Request-Manual-Completo.pdf` e `compactador de prompt/`.

## Ao terminar

1. Atualizar `docs/STATUS.md` (o que foi feito, o que foi testado e onde, próximo passo).
2. Marcar em `docs/PLANO.md` o que ficou pronto.
3. Registrar em `docs/ERROS.md` erro novo ou resolvido.
4. Dar ao dono o passo a passo para conferir.

Use sempre caminhos relativos à raiz do projeto.
