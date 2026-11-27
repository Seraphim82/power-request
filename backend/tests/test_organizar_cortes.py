"""O Organizar nunca corta texto sem avisar (textos inventados)."""

import pytest

from ai_hub import MAX_SEND_PROMPT_CHARS
from prompt_engine import PowerRequestEngine

LIMITE = PowerRequestEngine.MAX_FIELD_LENGTH
MAXIMO = PowerRequestEngine.MAX_REGRAS_ORGANIZAR


@pytest.fixture()
def motor():
    return PowerRequestEngine()


def prompt_com_regras(regras):
    linhas = "\n".join(f"- {r}" for r in regras)
    return f"### Objetivo\nControlar emprestimos de ferramentas\n\n### Regras\n{linhas}"


def test_dentro_do_limite_nao_avisa(motor):
    r = motor.organizar_prompt(prompt_com_regras([f"Regra numero {n}" for n in range(MAXIMO)]))
    assert len(r["campos"]["regras"]) == MAXIMO
    assert r["avisos"] == []
    assert r["ficou_de_fora"] == []


def test_regras_alem_do_maximo_sao_avisadas_e_devolvidas(motor):
    regras = [f"Regra numero {n}" for n in range(MAXIMO + 3)]
    r = motor.organizar_prompt(prompt_com_regras(regras))
    assert r["campos"]["regras"] == regras[:MAXIMO]
    assert [t["texto"] for t in r["ficou_de_fora"]] == regras[MAXIMO:]
    assert any("ficaram de fora: 3" in a for a in r["avisos"])


def test_regra_repetida_nao_conta_como_cortada(motor):
    regras = [f"Regra numero {n}" for n in range(MAXIMO)] + ["Regra numero 0"]
    assert motor.organizar_prompt(prompt_com_regras(regras))["ficou_de_fora"] == []


def test_texto_corrido_tambem_avisa(motor):
    frases = " ".join(f"Nunca pode apagar o registro {n}." for n in range(MAXIMO + 2))
    r = motor.organizar_prompt(frases)
    assert len(r["campos"]["regras"]) == MAXIMO
    assert len(r["ficou_de_fora"]) == 2


def test_regra_comprida_devolve_o_final_cortado(motor):
    regra = "a" * LIMITE + "FINAL IMPORTANTE"
    r = motor.organizar_prompt(prompt_com_regras([regra]))
    assert r["campos"]["regras"] == ["a" * LIMITE]
    assert [t["texto"] for t in r["ficou_de_fora"]] == ["FINAL IMPORTANTE"]
    assert r["avisos"]


def test_duas_regras_compridas_iguais_no_comeco_nao_perdem_o_final(motor):
    regras = ["a" * LIMITE + "PRIMEIRO", "a" * LIMITE + "SEGUNDO"]
    r = motor.organizar_prompt(prompt_com_regras(regras))
    assert r["campos"]["regras"] == ["a" * LIMITE]
    assert [t["texto"] for t in r["ficou_de_fora"]] == ["PRIMEIRO", "SEGUNDO"]


def test_campo_comprido_devolve_o_final_com_nome_da_tela(motor):
    r = motor.organizar_prompt("### Entrada\n" + "b" * LIMITE + "SOBRA")
    assert r["campos"]["entrada"] == "b" * LIMITE
    assert r["ficou_de_fora"] == [
        {"campo": "entrada", "titulo": "Final do campo O que entra", "texto": "SOBRA"}
    ]
    assert any("O que entra" in a for a in r["avisos"])


@pytest.mark.parametrize("separador", ["\n- ", ";"])
def test_pior_caso_com_maximo_de_regras_cabe_no_enviar(motor, separador):
    """Texto colado no limite, 50 regras e Contexto fixo no limite ainda cabem no botão Enviar."""
    assert MAXIMO == 50
    cabecalho = "### Regras\n- "
    sobra = motor.MAX_TEXTO_ORGANIZAR - len(cabecalho) - len(separador) * (MAXIMO - 1)
    tamanho = sobra // MAXIMO
    regras = [f"{n:02d}" + "r" * (tamanho - 2) for n in range(MAXIMO)]
    colado = cabecalho + separador.join(regras)
    assert motor.MAX_TEXTO_ORGANIZAR - MAXIMO < len(colado) <= motor.MAX_TEXTO_ORGANIZAR

    organizado = motor.organizar_prompt(colado)
    assert organizado["campos"]["regras"] == regras
    assert organizado["ficou_de_fora"] == []

    # Os outros campos a pessoa completa com respostas curtas nas etapas.
    final = motor.gerar_prompt_final({
        "objetivo": "o" * 100, "stack": "s" * 50, "entrada": "e" * 100, "saida": "a" * 100,
        "regras": organizado["campos"]["regras"], "tratamento_erros": "",
        "contexto_fixo": "c" * LIMITE,
    })
    assert len(final["prompt_final"]) <= MAX_SEND_PROMPT_CHARS
