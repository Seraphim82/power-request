"""Revisão: avisa quando Stack, Input ou Output estão vagos (testes novos, não alteram os antigos)."""

import pytest
from prompt_engine import PowerRequestEngine


def _payload() -> dict:
    return {
        "objetivo": "Criar API para extrair dados de contratos imobiliários em PDF",
        "stack": "Python, FastAPI, PyPDF2",
        "entrada": "Arquivo PDF de até 10 páginas enviado via upload",
        "saida": "JSON estruturado com valor, matrícula e comprador",
        "regras": ["Formatar valores em R$ 0.000,00", "Ignorar páginas em branco"],
        "tratamento_erros": "Se o PDF estiver corrompido, retornar HTTP 422.",
    }


@pytest.mark.parametrize("stack", ["web", "App", "sistema.", "Celular", "qualquer coisa"])
def test_stack_generica_gera_pendencia(stack):
    p = _payload()
    p["stack"] = stack
    rev = PowerRequestEngine().revisar_pedido(p)
    assert rev["aprovado"] is False
    assert any(x.startswith("Stack genérica") for x in rev["pendencias"])


@pytest.mark.parametrize("stack", ["Flutter (Dart)", "Python + FastAPI + SQLite", "Node.js"])
def test_stack_com_tecnologia_nao_gera_pendencia(stack):
    p = _payload()
    p["stack"] = stack
    rev = PowerRequestEngine().revisar_pedido(p)
    assert not any(x.startswith("Stack genérica") for x in rev["pendencias"])


@pytest.mark.parametrize("saida", ["resultado", "tela", "JSON", "Uma lista", "dados dados dados"])
def test_output_vago_gera_pendencia(saida):
    p = _payload()
    p["saida"] = saida
    rev = PowerRequestEngine().revisar_pedido(p)
    assert any(x.startswith("Output vago") for x in rev["pendencias"])
    assert rev["score_qualidade"] == 85


def test_input_vago_gera_pendencia():
    p = _payload()
    p["entrada"] = "dados"
    rev = PowerRequestEngine().revisar_pedido(p)
    assert any(x.startswith("Input vago") for x in rev["pendencias"])


def test_input_e_output_especificos_passam():
    rev = PowerRequestEngine().revisar_pedido(_payload())
    assert rev["aprovado"] is True and rev["score_qualidade"] == 100


def test_varias_pendencias_somam_mas_score_tem_piso_de_40():
    p = _payload()
    p.update(stack="web", entrada="dados", saida="tela", regras=["x"], tratamento_erros="")
    rev = PowerRequestEngine().revisar_pedido(p)
    assert len(rev["pendencias"]) >= 5
    assert rev["score_qualidade"] == 40
