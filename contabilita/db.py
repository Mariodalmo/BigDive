from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .chart_of_accounts import DEFAULT_CHART


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    schema = schema_path.read_text(encoding="utf-8")
    conn.executescript(schema)
    _seed_chart_if_empty(conn)
    _seed_settings_if_missing(conn)


def _seed_chart_if_empty(conn: sqlite3.Connection) -> None:
    cur = conn.execute("SELECT COUNT(1) AS c FROM accounts")
    if int(cur.fetchone()["c"]) > 0:
        return

    conn.executemany(
        "INSERT INTO accounts(code, name, kind) VALUES (?, ?, ?)",
        [(a.code, a.name, a.kind) for a in DEFAULT_CHART],
    )
    conn.commit()


def _seed_settings_if_missing(conn: sqlite3.Connection) -> None:
    defaults = {
        "tax_ires_rate": "0.24",
        "tax_irap_rate": "0.039",
        "company_name": "",
        "currency": "EUR",
    }
    for k, v in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
            (k, v),
        )
    conn.commit()


def list_accounts(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("SELECT id, code, name, kind FROM accounts ORDER BY code"))


def get_account_id_by_code(conn: sqlite3.Connection, code: str) -> int:
    row = conn.execute("SELECT id FROM accounts WHERE code = ?", (code,)).fetchone()
    if not row:
        raise KeyError(f"Account code not found: {code}")
    return int(row["id"])


def create_entry(
    conn: sqlite3.Connection,
    entry_date: str,
    description: str,
    doc_ref: str | None,
    lines: Iterable[dict],
) -> int:
    """Create a balanced journal entry.

    lines items: {account_id:int, debit_cents:int, credit_cents:int, vat_rate?:float, vat_type?:str, note?:str}
    """
    lines = list(lines)
    total_debit = sum(int(l.get("debit_cents", 0) or 0) for l in lines)
    total_credit = sum(int(l.get("credit_cents", 0) or 0) for l in lines)
    if total_debit <= 0:
        raise ValueError("Total debit must be > 0")
    if total_debit != total_credit:
        raise ValueError(f"Entry not balanced: debit {total_debit} != credit {total_credit}")

    cur = conn.execute(
        "INSERT INTO journal_entries(entry_date, description, doc_ref) VALUES (?, ?, ?)",
        (entry_date, description, doc_ref),
    )
    entry_id = int(cur.lastrowid)

    conn.executemany(
        """
        INSERT INTO journal_lines(
            entry_id, account_id, debit_cents, credit_cents, vat_rate, vat_type, note
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                entry_id,
                int(l["account_id"]),
                int(l.get("debit_cents", 0) or 0),
                int(l.get("credit_cents", 0) or 0),
                l.get("vat_rate"),
                l.get("vat_type"),
                l.get("note"),
            )
            for l in lines
        ],
    )
    conn.commit()
    return entry_id


def list_entries(conn: sqlite3.Connection, limit: int = 200) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT id, entry_date, description, doc_ref, created_at
            FROM journal_entries
            ORDER BY entry_date DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
    )


def get_entry_lines(conn: sqlite3.Connection, entry_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT jl.id, a.code, a.name, a.kind, jl.debit_cents, jl.credit_cents, jl.vat_rate, jl.vat_type, jl.note
            FROM journal_lines jl
            JOIN accounts a ON a.id = jl.account_id
            WHERE jl.entry_id = ?
            ORDER BY jl.id ASC
            """,
            (entry_id,),
        )
    )


def get_setting(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else default


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
