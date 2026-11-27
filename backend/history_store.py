"""Armazenamento local em SQLite para o histórico de pedidos do Power Request."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HistoryStoreError(Exception):
    """Erro de validação ou operação no histórico local."""


def _restringir(caminho: Path, modo: int) -> None:
    """Deixa o acesso só para o dono. Se o sistema não permitir, o app continua funcionando."""
    try:
        os.chmod(caminho, modo)
    except OSError:
        pass


class HistoryStore:
    """Persiste e consulta pedidos gerados localmente em SQLite com queries parametrizadas."""

    MAX_LIMIT = 100
    MAX_SEARCH_LEN = 200

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            base_dir = Path.home() / ".power_request"
            base_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            _restringir(base_dir, 0o700)
            self.db_path = base_dir / "history.db"
        else:
            self.db_path = Path(db_path)
            pasta = self.db_path.parent
            pasta_nova = not pasta.exists()
            pasta.mkdir(mode=0o700, parents=True, exist_ok=True)
            if pasta_nova:  # pasta que já existia e foi escolhida por quem chamou não é alterada
                _restringir(pasta, 0o700)
        self._criar_arquivo_privado()
        self._init_db()

    def _criar_arquivo_privado(self) -> None:
        """O banco nasce com 600; um banco antigo, mais aberto, é ajustado."""
        try:
            os.close(os.open(self.db_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
        except OSError:
            pass  # já existe (ou não pôde ser criado: o SQLite dirá o motivo)
        _restringir(self.db_path, 0o600)

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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rodadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id INTEGER NOT NULL,
                    ordem INTEGER NOT NULL,
                    pedido_texto TEXT NOT NULL,
                    resposta TEXT NOT NULL,
                    origem TEXT NOT NULL,
                    criado_em TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL
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
            conn.execute("DELETE FROM rodadas WHERE pedido_id = ?", (pedido_id,))
            cursor = conn.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
            return cursor.rowcount > 0

    def limpar_historico(self) -> int:
        with self._connect() as conn:
            conn.execute("DELETE FROM rodadas")
            cursor = conn.execute("DELETE FROM pedidos")
            return int(cursor.rowcount)

    # ---------- Sequenciar: respostas guardadas por pedido ----------
    MAX_RODADAS_POR_PEDIDO = 50

    def reiniciar_rodadas(self, pedido_id: int) -> None:
        """Apaga as rodadas de um pedido (um novo envio do prompt original recomeça a sequência)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM rodadas WHERE pedido_id = ?", (pedido_id,))

    def salvar_rodada(
        self, pedido_id: int, pedido_texto: str, resposta: str, origem: str
    ) -> dict[str, Any] | None:
        """Guarda uma rodada (pedido + resposta da IA). Devolve None se o pedido não existe
        ou se a sequência já atingiu o limite."""
        if pedido_id <= 0 or not resposta or not resposta.strip():
            return None
        agora = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            if conn.execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is None:
                return None
            ultima = conn.execute(
                "SELECT COALESCE(MAX(ordem), 0) AS m FROM rodadas WHERE pedido_id = ?", (pedido_id,)
            ).fetchone()["m"]
            if ultima >= self.MAX_RODADAS_POR_PEDIDO:
                return None
            cursor = conn.execute(
                "INSERT INTO rodadas (pedido_id, ordem, pedido_texto, resposta, origem, criado_em) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (pedido_id, ultima + 1, (pedido_texto or "").strip(), resposta.strip(),
                 (origem or "IA").strip()[:120], agora),
            )
            row = conn.execute("SELECT * FROM rodadas WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)

    def listar_rodadas(self, pedido_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM rodadas WHERE pedido_id = ? ORDER BY ordem ASC", (pedido_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def obter_config(self, chave: str, padrao: str = "") -> str:
        """Lê uma configuração de texto salva localmente (ex: contexto fixo)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT valor FROM configuracoes WHERE chave = ?", (chave,)
            ).fetchone()
        return str(row["valor"]) if row else padrao

    def salvar_config(self, chave: str, valor: str) -> None:
        """Grava (ou substitui) uma configuração de texto."""
        if not chave or len(chave) > 60:
            raise HistoryStoreError("Nome de configuração inválido.")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO configuracoes (chave, valor) VALUES (?, ?) "
                "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
                (chave, valor),
            )
