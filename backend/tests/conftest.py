"""Isola os testes do banco real do usuário (~/.power_request/history.db)."""

import pytest

import main
from history_store import HistoryStore


@pytest.fixture(autouse=True)
def _historico_temporario(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "history_store", HistoryStore(tmp_path / "teste.db"))
