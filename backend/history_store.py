"""Armazenamento local em SQLite para o histórico de pedidos do Power Request."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HistoryStoreError(Exception):
    """Erro de validação ou operação no histórico local."""


class HistoryStore:
    """Persiste e consulta pedidos gerados localmente em SQLite com queries parametrizadas."""

    MAX_LIMIT = 100
    MAX_SEARCH_LEN = 200

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            base_dir = Path.home() / ".power_request"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "history.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    criado_em TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    objetivo TEXT NOT NULL,
                    stack TEXT NOT NULL,
                    entrada TEXT NOT NULL,
                    saida TEXT NOT NULL,
                    regras_json TEXT NOT NULL,
                    tratamento_erros TEXT NOT NULL,
                    prompt_final TEXT NOT NULL,
                    tokens_estimados INTEGER NOT NULL,
                    gerado_por TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        try:
            regras = json.loads(row["regras_json"])
            if not isinstance(regras, list):
                regras = []
        except json.JSONDecodeError:
            regras = []

        return {
            "id": int(row["id"]),
            "criado_em": str(row["criado_em"]),
            "categoria": str(row["categoria"]),
            "objetivo": str(row["objetivo"]),
            "stack": str(row["stack"]),
            "entrada": str(row["entrada"]),
            "saida": str(row["saida"]),
            "regras": regras,
            "tratamento_erros": str(row["tratamento_erros"]),
            "prompt_final": str(row["prompt_final"]),
            "tokens_estimados": int(row["tokens_estimados"]),
            "gerado_por": str(row["gerado_por"]),
        }

    def salvar_pedido(
        self,
        *,
        categoria: str,
        objetivo: str,
        stack: str,
        entrada: str,
        saida: str,
        regras: list[str],
        tratamento_erros: str,
        prompt_final: str,
        tokens_estimados: int,
        gerado_por: str,
    ) -> dict[str, Any]:
        """Grava um pedido finalizado no banco local e retorna o registro salvo."""
        if not prompt_final or not prompt_final.strip():
            raise HistoryStoreError("Não é possível salvar um prompt vazio no histórico.")

        agora = datetime.now(timezone.utc).isoformat()
        cat_limpa = (categoria or "geral").strip()[:40] or "geral"
        regras_json = json.dumps(list(regras), ensure_ascii=False)
        tokens_safe = max(1, int(tokens_estimados))

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO pedidos (
                    criado_em, categoria, objetivo, stack, entrada, saida,
                    regras_json, tratamento_erros, prompt_final, tokens_estimados, gerado_por
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agora,
                    cat_limpa,
                    objetivo.strip(),
                    stack.strip(),
                    entrada.strip(),
                    saida.strip(),
                    regras_json,
                    tratamento_erros.strip(),
                    prompt_final.strip(),
                    tokens_safe,
                    (gerado_por or "Motor Local").strip()[:120],
                ),
            )
            novo_id = int(cursor.lastrowid)
            row = conn.execute("SELECT * FROM pedidos WHERE id = ?", (novo_id,)).fetchone()

        return self._row_to_dict(row)

    def listar_pedidos(self, busca: str = "", limite: int = 30) -> list[dict[str, Any]]:
        """Lista os pedidos mais recentes com busca opcional segura contra SQL injection."""
        limite_seguro = max(1, min(int(limite), self.MAX_LIMIT))
        termo = (busca or "").strip()[: self.MAX_SEARCH_LEN]

        with self._connect() as conn:
            if termo:
                like = f"%{termo}%"
                rows = conn.execute(
                    """
                    SELECT * FROM pedidos
                    WHERE objetivo LIKE ?
                       OR stack LIKE ?
                       OR categoria LIKE ?
                       OR prompt_final LIKE ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (like, like, like, like, limite_seguro),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM pedidos ORDER BY id DESC LIMIT ?",
                    (limite_seguro,),
                ).fetchall()

        return [self._row_to_dict(r) for r in rows]

    def obter_pedido(self, pedido_id: int) -> dict[str, Any] | None:
        if pedido_id <= 0:
            return None
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def remover_pedido(self, pedido_id: int) -> bool:
        if pedido_id <= 0:
            return False
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
            return cursor.rowcount > 0

    def limpar_historico(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM pedidos")
            return int(cursor.rowcount)
