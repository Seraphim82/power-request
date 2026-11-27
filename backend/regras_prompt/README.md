# Biblioteca de regras do Organizar prompt

Quando o texto colado não tem títulos, o app separa as frases usando estes arquivos. Não usa IA e
não envia o texto para fora. Ela reconhece formas de falar; **não entende o sentido da frase**.

## Arquivos

| Arquivo | O que reconhece |
|---|---|
| `objetivo.json` | a frase que diz o que a pessoa quer construir |
| `entrada.json` | dados que alguém digita, envia ou que o programa lê |
| `saida.json` | o que o programa mostra, gera ou entrega |
| `regras.json` | limites, proibições, obrigações, regras do negócio e preferências |
| `tratamento_erros.json` | o que fazer quando algo falha, falta ou vem errado |
| `tecnologias.json` | nomes de tecnologias e outras formas de escrevê-los |
| `abreviacoes.json` | "vc", "pq", "qdo" e erros comuns; vale só para reconhecer, não altera o texto |

## Como a frase é decidida

1. Pista forte de **objetivo**: é o objetivo.
2. Pista forte de **erro**: é tratamento de erros.
3. Entre regras, entrada e saída vence a maior nota (forte = 3, fraca = 1; contam até 2 de cada).
   No empate: regras, depois entrada, depois saída. Nota mínima: 2.
4. Sem certeza, a frase **fica no Objetivo** para a pessoa conferir. Nada é descartado.

`excecoes` apagam, só para aquele campo, o trecho que engana (ex.: "erros de produção").

## Como escrever uma expressão

Sempre em minúsculas, **sem acento e sem pontuação**. Só valem palavras inteiras.

| Escrita | Significado |
|---|---|
| `nao pode` | essas palavras, nesta ordem |
| `{so\|apenas}` | uma das opções (pode ter chaves dentro de chaves) |
| `cadastr*` | palavra que começa assim |
| `se ..4 faltar` | até 4 palavras no meio (máximo 12, e 3 intervalos por expressão) |
| `^se` | só no começo da frase |
| `#` | um número |

Expressão regular comum não é aceita. Formato errado impede o app de abrir (e o teste acusa).

## Como melhorar

1. Achou uma frase no campo errado? Reescreva com **dados inventados** (o repositório é público)
   e coloque em um arquivo de `backend/tests/corpus/`.
2. Ajuste a regra pensando na **forma de falar**, não só naquela frase.
3. Rode `make check`: os exemplos antigos não podem piorar.
4. Placar honesto só com frases que ninguém usou para ajustar a regra.

## Tamanho (depois de dobrar, 27/11/2026)

317 expressões de campo (eram 157), 148 tecnologias (eram 74) e 58 abreviações ou erros de
digitação. Nas 250 frases de exemplo, 169 das 284 pistas fortes e fracas foram acionadas;
**115 nunca foram exercitadas** por um exemplo.

## Placar de 27/11/2026 (frases no campo certo, medido em teste)

Referência: `leigo_novo`, 30 frases no jeito de uma pessoa leiga, escritas **depois** de congelar a
biblioteca dobrada. Na época da medição, as três versões nunca as tinham visto.

| Versão | `leigo_novo` |
|---|---|
| App original | 20% |
| Primeira biblioteca ampliada (157 expressões) | 63% |
| Dobrada | 76% |

- Somando `leigo_novo` e 10 frases em que a pessoa só conta a própria história (40 frases):
  campo certo 15, 26 e 30; **campo errado** 1, 3 e 3; as demais ficaram no Objetivo.
- Três narrativas viravam Regra. Foram corrigidas depois; `armadilhas_leigas` não é mais inédito.
- `desafio` (24 frases, outro estilo): 16% no original, 45% antes, 54% agora. **Não vale mais como
  prova:** as falhas dele já eram conhecidas quando a biblioteca foi dobrada.
- `ajuste`, `solto`, `ineditos` e `leigo` foram vistos no ajuste: não medem generalização.
- Todos os exemplos foram escritos pela IA que montou a biblioteca. Frases de pessoas de verdade
  medem melhor. Os próximos ajustes pedem um grupo inédito novo.
