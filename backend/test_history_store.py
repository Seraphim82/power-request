"""Testes severos de persistência, busca, integridade e proteção contra SQL Injection."""

import pytest

from history_store import HistoryStore, HistoryStoreError


def _salvar_exemplo(store: HistoryStore, **overrides) -> dict:
    dados = {
        "categoria": "bots",
        "objetivo": "Criar mini bot de WhatsApp para responder dúvidas frequentes",
        "stack": "Python + WhatsApp Cloud API",
        "entrada": "Menu numerado",
        "saida": "Resposta automática no chat",
        "regras": ["Oferecer opção de humano", "Ignorar grupos"],
        "tratamento_erros": "Mostrar menu novamente",
        "prompt_final": "### Objetivo\nCriar mini bot de WhatsApp...",
        "tokens_estimados": 95,
        "gerado_por": "Claude",
    }
    dados.update(overrides)
    return store.salvar_pedido(**dados)


def test_historico_salva_e_lista_do_mais_recente_ao_mais_antigo(tmp_path):
    store = HistoryStore(tmp_path / "hist.db")
    p1 = _salvar_exemplo(store, objetivo="Primeiro pedido")
    p2 = _salvar_exemplo(store, categoria="jogos", objetivo="Jogo de Damas animado")

    lista = store.listar_pedidos()
    assert len(lista) == 2
    assert lista[0]["id"] == p2["id"]
    assert lista[1]["id"] == p1["id"]
    assert lista[1]["regras"] == ["Oferecer opção de humano", "Ignorar grupos"]


def test_historico_busca_por_termo_em_objetivo_e_stack(tmp_path):
    store = HistoryStore(tmp_path / "hist.db")
    _salvar_exemplo(store, categoria="bots", objetivo="Bot de WhatsApp", stack="Python")
    _salvar_exemplo(store, categoria="jogos", objetivo="Jogo de Damas", stack="Godot 4")

    res = store.listar_pedidos(busca="Godot")
    assert len(res) == 1
    assert res[0]["categoria"] == "jogos"


def test_historico_bloqueia_sql_injection_na_busca_e_nos_campos(tmp_path):
    store = HistoryStore(tmp_path / "hist.db")
    _salvar_exemplo(store)

    ataque = "'; DROP TABLE pedidos; --"
    assert store.listar_pedidos(busca=ataque) == []
    assert len(store.listar_pedidos()) == 1

    salvo = _salvar_exemplo(store, objetivo=ataque, regras=[ataque])
    assert salvo["objetivo"] == ataque
    assert len(store.listar_pedidos()) == 2


def test_historico_rejeita_prompt_vazio(tmp_path):
    store = HistoryStore(tmp_path / "hist.db")
    with pytest.raises(HistoryStoreError):
        _salvar_exemplo(store, prompt_final="   ")


def test_historico_limita_quantidade_solicitada(tmp_path):
    store = HistoryStore(tmp_path / "hist.db")
    for i in range(3):
        _salvar_exemplo(store, objetivo=f"Pedido {i}")

    assert len(store.listar_pedidos(limite=99999)) == 3
    assert len(store.listar_pedidos(limite=-10)) == 1


def test_historico_remove_item_e_trata_ids_invalidos(tmp_path):
    store = HistoryStore(tmp_path / "hist.db")
    item = _salvar_exemplo(store)

    assert store.remover_pedido(-1) is False
    assert store.remover_pedido(99999) is False
    assert store.remover_pedido(item["id"]) is True
    assert store.obter_pedido(item["id"]) is None


def test_historico_limpa_todos_os_registros(tmp_path):
    store = HistoryStore(tmp_path / "hist.db")
    _salvar_exemplo(store, objetivo="Pedido A")
    _salvar_exemplo(store, objetivo="Pedido B")

    removidos = store.limpar_historico()
    assert removidos == 2
    assert store.listar_pedidos() == []


def test_historico_obtem_item_individual_com_acentuacao(tmp_path):
    store = HistoryStore(tmp_path / "hist.db")
    item = _salvar_exemplo(store, objetivo="Automação de avaliação imobiliária com cálculo de ITBI")
    buscado = store.obter_pedido(item["id"])
    assert buscado is not None
    assert buscado["objetivo"] == "Automação de avaliação imobiliária com cálculo de ITBI"
