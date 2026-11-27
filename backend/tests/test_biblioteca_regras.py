"""Biblioteca de regras do Organizar (backend/regras_prompt) e o placar dos pedidos de exemplo.

Todos os pedidos de `tests/corpus/` são inventados. Cada linha é [rótulo, frase]:
O=objetivo, E=entrada, S=saída, R=regras, T=tratamento de erros.
"""

import json
import shutil
import time
from pathlib import Path

import pytest

import classificador_texto as ct
from prompt_engine import PowerRequestEngine

eng = PowerRequestEngine()
CORPUS = Path(__file__).parent / "corpus"
CAMPO = {"O": "objetivo", "E": "entrada", "S": "saida", "R": "regras", "T": "tratamento_erros"}


def placar(nome):
    certas, falhas = 0, []
    for caso in json.loads((CORPUS / f"{nome}.json").read_text(encoding="utf-8")):
        campos = eng.organizar_prompt(" ".join(f for _, f in caso["frases"]))["campos"]
        for rotulo, frase in caso["frases"]:
            # Em texto, procura o trecho; em regras (lista), procura a regra igual.
            onde = [c for c in CAMPO.values() if frase in campos[c]]
            if onde == [CAMPO[rotulo]]:
                certas += 1
            else:
                falhas.append((caso["nome"], CAMPO[rotulo], onde, frase))
    return certas, falhas


@pytest.mark.parametrize("nome", ["ajuste", "solto", "ineditos", "leigo", "armadilhas_leigas"])
def test_pedidos_usados_para_montar_a_biblioteca_nao_regridem(nome):
    assert placar(nome)[1] == []


# Pisos medidos em 27/11/2026. Não são metas: servem para a biblioteca não piorar sem ninguém ver.
@pytest.mark.parametrize("nome,minimo", [("prova", 35), ("desafio", 13), ("armadilhas", 10), ("leigo_novo", 23)])
def test_grupos_de_medicao_nao_pioram(nome, minimo):
    certas, falhas = placar(nome)
    assert certas >= minimo, falhas


@pytest.mark.parametrize("nome", ["ajuste", "prova", "solto", "ineditos", "desafio", "armadilhas", "leigo", "leigo_novo", "armadilhas_leigas"])
def test_nenhuma_frase_some_nem_duplica(nome):
    _, falhas = placar(nome)
    assert all(len(onde) == 1 for _, _, onde, _ in falhas), falhas


@pytest.mark.parametrize(
    "frase,campo",
    [
        ("A loja vende ferro e aço.", "tratamento_erros"),
        ("É importante para o bairro.", "entrada"),
        ("Quero criar um painel dos erros de produção.", "tratamento_erros"),
        ("O jogo é sobre um gato que passa de fase.", "entrada"),
    ],
)
def test_pedaco_de_palavra_e_nomes_nao_enganam(frase, campo):
    assert ct.classificar_frase(frase) != campo


def test_falha_vence_quando_a_frase_tambem_manda_mostrar():
    assert ct.classificar_frase("Se faltar o arquivo, mostrar um aviso.") == "tratamento_erros"


def test_sem_certeza_nao_arrisca():
    assert ct.classificar_frase("Meu pai tem uma padaria há vinte anos.") is None


def test_intervalo_e_inicio_de_frase():
    padrao = ct.compilar("^{o|a} ..2 {digita|informa}")
    assert padrao.search(ct.normalizar("A moça do balcão informa")) is None
    assert padrao.search(ct.normalizar("O cliente informa o nome"))
    assert padrao.search(ct.normalizar("Depois o cliente informa")) is None


@pytest.mark.parametrize(
    "ruim",
    ["(a+)+$", "nome.*", "Maiúscula", "{aberta", "fechada}", "a|b", "{a|}", "..3", "palavra ..3", "a ..99 b", "a ^b",
     "a ..2 b ..2 c ..2 d ..2 e", "", "a" * (ct.MAX_EXPRESSAO + 1), 7],
)
def test_expressao_fora_do_formato_e_recusada(ruim):
    with pytest.raises(ct.BibliotecaInvalida):
        ct.compilar(ruim)


@pytest.mark.parametrize("conteudo", ["isto não é json", "[]", '{"campo": "entrada"}'])
def test_arquivo_estragado_e_recusado(tmp_path, conteudo):
    pasta = tmp_path / "lib"
    shutil.copytree(ct.PASTA_BIBLIOTECA, pasta)
    (pasta / "entrada.json").write_text(conteudo, encoding="utf-8")
    with pytest.raises(ct.BibliotecaInvalida):
        ct.carregar_pistas(pasta)


def test_pasta_da_biblioteca_guarda_so_dados():
    assert {a.suffix for a in ct.PASTA_BIBLIOTECA.iterdir()} == {".json", ".md"}


def test_apelido_de_tecnologia_vira_nome_oficial():
    assert eng._detectar_tecnologias("Quero usar nodejs com postgres") == ["Node.js", "PostgreSQL"]


@pytest.mark.parametrize("pedaco", ["se ", "o usuario pode vai deve mostra ", "quando caso nao se "])
def test_texto_grande_e_repetitivo_responde_rapido(pedaco):
    texto = (pedaco * 8000)[: eng.MAX_TEXTO_ORGANIZAR - 10]
    inicio = time.perf_counter()
    eng.organizar_prompt(texto)
    assert time.perf_counter() - inicio < 3


@pytest.mark.parametrize(
    "curto,completo",
    [("n pode vender fiado", "não pode vender fiado"), ("dps quero ver qto vendi", "depois quero ver quanto vendi")],
)
def test_abreviacao_e_reconhecida_como_a_frase_completa(curto, completo):
    assert ct.classificar_frase(curto) == ct.classificar_frase(completo) is not None


def test_abreviacao_nao_altera_o_texto_da_pessoa():
    r = eng.organizar_prompt("qro um app p minha lojinha. n pode vender fiado.")
    assert r["campos"]["regras"] == ["n pode vender fiado."]
    assert r["campos"]["objetivo"] == "qro um app p minha lojinha."


def test_abreviacao_fora_do_formato_e_recusada(tmp_path):
    (tmp_path / "abreviacoes.json").write_text('{"trocas": {"a.*": "b"}}', encoding="utf-8")
    with pytest.raises(ct.BibliotecaInvalida):
        ct.carregar_abreviacoes(tmp_path)
