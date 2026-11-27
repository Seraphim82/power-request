"""Lê a biblioteca `regras_prompt/` e decide para qual campo vai cada frase de um texto corrido.

A biblioteca guarda só dados. Cada expressão usa uma escrita simples (veja regras_prompt/README.md),
sempre sem acento e em minúsculas. Expressão regular escrita à mão não é aceita: o arquivo é
conferido ao carregar e um formato errado interrompe o app com uma mensagem clara.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

PASTA_BIBLIOTECA = Path(__file__).resolve().parent / "regras_prompt"
CAMPOS_COM_PISTAS = ("objetivo", "entrada", "saida", "regras", "tratamento_erros")
LISTAS = ("fortes", "fracas", "excecoes")
MAX_EXPRESSAO = 1200
MAX_PALAVRAS_NO_INTERVALO = 12

PONTOS_FORTE, PONTOS_FRACA, NOTA_MINIMA = 3, 1, 2
# Empate: a primeira da lista vence.
DESEMPATE = ("regras", "entrada", "saida")

_NUMERO = r"(?:\d+\w*|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez|quinze|vinte|trinta)"
_PECA = re.compile(r"\.\.\d{1,2}|\^|\{|\}|\||#|%|[a-z0-9]+\*?| +")


class BibliotecaInvalida(ValueError):
    """Arquivo da biblioteca com formato errado."""


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento e sem pontuação (mantém números e %)."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9%#]+", " ", sem_acento).split())


def compilar(expressao: str) -> re.Pattern[str]:
    """Traduz a escrita simples da biblioteca. Compara sempre palavras inteiras."""
    if not isinstance(expressao, str) or not 0 < len(expressao) <= MAX_EXPRESSAO:
        raise BibliotecaInvalida(f"Expressão vazia, longa demais ou que não é texto: {expressao!r}")
    pecas = _PECA.findall(expressao)
    if "".join(pecas) != expressao:
        raise BibliotecaInvalida(f"Caractere não permitido em: {expressao!r}")

    inicio = pecas[0] == "^"
    if inicio:
        pecas = pecas[1:]

    # alternativas: pilha de grupos; cada grupo é uma lista de opções; cada opção, uma lista de itens
    pilha: list[list[list[str]]] = [[[]]]
    for peca in pecas:
        if peca.isspace():
            continue
        if peca == "{":
            pilha.append([[]])
        elif peca == "}":
            if len(pilha) == 1:
                raise BibliotecaInvalida(f"Chave fechada sem abrir: {expressao!r}")
            opcoes = pilha.pop()
            if not all(opcoes):
                raise BibliotecaInvalida(f"Opção vazia em: {expressao!r}")
            pilha[-1][-1].append("(?:" + "|".join(_juntar(o) for o in opcoes) + ")")
        elif peca == "|":
            if len(pilha) == 1:
                raise BibliotecaInvalida(f"'|' fora das chaves: {expressao!r}")
            pilha[-1].append([])
        elif peca == "^":
            raise BibliotecaInvalida(f"'^' só vale no começo: {expressao!r}")
        elif peca.startswith(".."):
            quantas = int(peca[2:])
            if not 1 <= quantas <= MAX_PALAVRAS_NO_INTERVALO:
                raise BibliotecaInvalida(f"Intervalo fora do limite: {expressao!r}")
            pilha[-1][-1].append(f"\x00{quantas}")
        elif peca == "#":
            pilha[-1][-1].append(_NUMERO)
        elif peca.endswith("*"):
            pilha[-1][-1].append(re.escape(peca[:-1]) + r"\w*")
        else:
            pilha[-1][-1].append(re.escape(peca))
    if len(pilha) != 1 or not pilha[0][0]:
        raise BibliotecaInvalida(f"Chaves incompletas ou expressão vazia: {expressao!r}")
    corpo = _juntar(pilha[0][0])
    if corpo.count("{0,") > 3:
        raise BibliotecaInvalida(f"Intervalos demais em: {expressao!r}")
    return re.compile((r"\A" if inicio else r"(?<!\S)") + corpo + r"(?![^\s%])")


def _juntar(itens: list[str]) -> str:
    saida = ""
    intervalo = ""
    for item in itens:
        if item.startswith("\x00"):
            intervalo = rf"(?:[^ ]+ ){{0,{item[1:]}}}"
            continue
        if saida:
            saida += " " + intervalo
        else:
            saida += intervalo
        saida += item
        intervalo = ""
    if intervalo or not saida:
        raise BibliotecaInvalida("Intervalo precisa vir antes de uma palavra.")
    return saida


def _ler_json(caminho: Path) -> dict:
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:
        raise BibliotecaInvalida(f"Não foi possível ler {caminho.name}.") from erro
    if not isinstance(dados, dict):
        raise BibliotecaInvalida(f"{caminho.name} precisa ser um objeto.")
    return dados


def carregar_pistas(pasta: Path = PASTA_BIBLIOTECA) -> dict[str, dict[str, list[re.Pattern[str]]]]:
    pistas = {}
    for campo in CAMPOS_COM_PISTAS:
        dados = _ler_json(pasta / f"{campo}.json")
        if set(dados) != {"campo", "descricao", *LISTAS} or dados["campo"] != campo:
            raise BibliotecaInvalida(f"{campo}.json: chaves ou nome do campo errados.")
        if not all(isinstance(dados[lista], list) for lista in LISTAS):
            raise BibliotecaInvalida(f"{campo}.json: fortes, fracas e excecoes precisam ser listas.")
        pistas[campo] = {lista: [compilar(e) for e in dados[lista]] for lista in LISTAS}
    return pistas


def carregar_tecnologias(pasta: Path = PASTA_BIBLIOTECA) -> list[tuple[str, list[str]]]:
    dados = _ler_json(pasta / "tecnologias.json")
    try:
        itens = [(t["nome"], list(t["apelidos"])) for t in dados["tecnologias"]]
    except (KeyError, TypeError) as erro:
        raise BibliotecaInvalida("tecnologias.json: cada item precisa de nome e apelidos.") from erro
    if not all(isinstance(x, str) and x.strip() for nome, apelidos in itens for x in (nome, *apelidos)):
        raise BibliotecaInvalida("tecnologias.json: nomes e apelidos precisam ser textos.")
    return itens


def carregar_abreviacoes(pasta: Path = PASTA_BIBLIOTECA) -> dict[str, str]:
    dados = _ler_json(pasta / "abreviacoes.json")
    trocas = dados.get("trocas")
    if not isinstance(trocas, dict) or not all(
        isinstance(v, str) and re.fullmatch(r"[a-z0-9]+", k) and re.fullmatch(r"[a-z0-9]+(?: [a-z0-9]+)*", v)
        for k, v in trocas.items()
    ):
        raise BibliotecaInvalida("abreviacoes.json: use trocas de palavra, sem acento e em minúsculas.")
    return trocas


ABREVIACOES = carregar_abreviacoes()
PISTAS = carregar_pistas()
TECNOLOGIAS = carregar_tecnologias()


def pontuar(frase: str, campo: str, pistas=PISTAS) -> int:
    # As abreviações valem só para reconhecer; a frase guardada nos campos não muda.
    palavras = normalizar(frase).replace("#", " ").split()
    texto = " ".join(ABREVIACOES.get(p, p) for p in palavras)
    # A exceção apaga só o trecho que engana; o resto da frase continua valendo.
    for excecao in pistas[campo]["excecoes"]:
        texto = " ".join(excecao.sub(" _ ", texto).split())
    fortes = sum(1 for p in pistas[campo]["fortes"] if p.search(texto))
    fracas = sum(1 for p in pistas[campo]["fracas"] if p.search(texto))
    return min(fortes, 2) * PONTOS_FORTE + min(fracas, 2) * PONTOS_FRACA


def classificar_frase(frase: str, pistas=PISTAS) -> str | None:
    """Devolve o campo da frase ou None quando não há certeza (a frase fica no Objetivo)."""
    # 1) "Quero criar um..." é o pedido em si, mesmo que cite erros, dados ou telas.
    if pontuar(frase, "objetivo", pistas) >= PONTOS_FORTE:
        return "objetivo"
    # 2) Frase que cita uma falha é tratamento de erro, mesmo que mande mostrar ou proíba algo.
    if pontuar(frase, "tratamento_erros", pistas) >= PONTOS_FORTE:
        return "tratamento_erros"
    # 3) Entre os demais, vence a maior nota; abaixo do mínimo, não arrisca.
    notas = {campo: pontuar(frase, campo, pistas) for campo in DESEMPATE}
    melhor = max(DESEMPATE, key=lambda campo: notas[campo])
    return melhor if notas[melhor] >= NOTA_MINIMA else None
