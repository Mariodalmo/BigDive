from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import sqlite3


Kind = Literal["ASSET", "LIABILITY", "EQUITY", "INCOME", "EXPENSE"]


@dataclass(frozen=True)
class ReportPeriod:
    start: str  # yyyy-mm-dd
    end: str    # yyyy-mm-dd inclusive


def _load_lines(conn: sqlite3.Connection) -> pd.DataFrame:
    q = """
    SELECT
      je.id AS entry_id,
      je.entry_date,
      je.description,
      je.doc_ref,
      a.code AS account_code,
      a.name AS account_name,
      a.kind AS account_kind,
      jl.debit_cents,
      jl.credit_cents,
      jl.vat_rate,
      jl.vat_type
    FROM journal_lines jl
    JOIN journal_entries je ON je.id = jl.entry_id
    JOIN accounts a ON a.id = jl.account_id
    """
    df = pd.read_sql_query(q, conn)
    if df.empty:
        return df
    df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
    df["debit"] = df["debit_cents"].astype(int) / 100.0
    df["credit"] = df["credit_cents"].astype(int) / 100.0
    df["signed"] = df["debit"] - df["credit"]
    return df


def trial_balance(conn: sqlite3.Connection, up_to: str | None = None) -> pd.DataFrame:
    df = _load_lines(conn)
    if df.empty:
        return pd.DataFrame(columns=["account_code", "account_name", "account_kind", "debit", "credit", "balance"])\
            .astype({"debit": float, "credit": float, "balance": float})

    if up_to:
        cutoff = pd.to_datetime(up_to).date()
        df = df[df["entry_date"] <= cutoff]

    g = df.groupby(["account_code", "account_name", "account_kind"], as_index=False).agg(
        debit=("debit", "sum"),
        credit=("credit", "sum"),
        balance=("signed", "sum"),
    )
    return g.sort_values(["account_code"]).reset_index(drop=True)


def income_statement(conn: sqlite3.Connection, period: ReportPeriod) -> dict:
    df = _load_lines(conn)
    if df.empty:
        return {
            "period": period,
            "income": pd.DataFrame(columns=["account_code", "account_name", "amount"]).astype({"amount": float}),
            "expenses": pd.DataFrame(columns=["account_code", "account_name", "amount"]).astype({"amount": float}),
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_profit": 0.0,
        }

    start = pd.to_datetime(period.start).date()
    end = pd.to_datetime(period.end).date()
    df = df[(df["entry_date"] >= start) & (df["entry_date"] <= end)]

    income = df[df["account_kind"] == "INCOME"].copy()
    expenses = df[df["account_kind"] == "EXPENSE"].copy()

    # Per conti ricavo: saldo positivo = credit - debit
    income["amount"] = (income["credit"] - income["debit"]).astype(float)
    expenses["amount"] = (expenses["debit"] - expenses["credit"]).astype(float)

    inc = income.groupby(["account_code", "account_name"], as_index=False)["amount"].sum()
    exp = expenses.groupby(["account_code", "account_name"], as_index=False)["amount"].sum()

    total_income = float(inc["amount"].sum()) if not inc.empty else 0.0
    total_expenses = float(exp["amount"].sum()) if not exp.empty else 0.0

    return {
        "period": period,
        "income": inc.sort_values("account_code").reset_index(drop=True),
        "expenses": exp.sort_values("account_code").reset_index(drop=True),
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": total_income - total_expenses,
    }


def balance_sheet(conn: sqlite3.Connection, as_of: str) -> dict:
    tb = trial_balance(conn, up_to=as_of)
    if tb.empty:
        return {
            "as_of": as_of,
            "assets": pd.DataFrame(columns=["account_code", "account_name", "amount"]).astype({"amount": float}),
            "liabilities": pd.DataFrame(columns=["account_code", "account_name", "amount"]).astype({"amount": float}),
            "equity": pd.DataFrame(columns=["account_code", "account_name", "amount"]).astype({"amount": float}),
            "total_assets": 0.0,
            "total_liabilities": 0.0,
            "total_equity": 0.0,
        }

    def to_amount(kind: Kind, balance: float) -> float:
        # balance = debit - credit
        if kind == "ASSET":
            return float(balance)
        # liabilities/equity/income normally have credit balances -> present as positive
        return float(-balance)

    tb["amount"] = tb.apply(lambda r: to_amount(r["account_kind"], float(r["balance"])), axis=1)

    assets = tb[tb["account_kind"] == "ASSET"]["account_code account_name amount".split()].copy()
    liabilities = tb[tb["account_kind"] == "LIABILITY"]["account_code account_name amount".split()].copy()
    equity = tb[tb["account_kind"] == "EQUITY"]["account_code account_name amount".split()].copy()

    # Utile/perdita d'esercizio: spesso non viene registrato a mano.
    # Per avere uno SP "completo", lo calcoliamo automaticamente come CE da inizio anno ad as_of
    # e lo mostriamo nel patrimonio netto (conto 3100).
    as_of_date = pd.to_datetime(as_of).date()
    ytd = ReportPeriod(str(date(as_of_date.year, 1, 1)), str(as_of_date))
    net_profit_ytd = float(income_statement(conn, ytd)["net_profit"])
    if abs(net_profit_ytd) >= 0.005:
        if not equity.empty and (equity["account_code"] == "3100").any():
            idx = equity.index[equity["account_code"] == "3100"][0]
            current = float(equity.loc[idx, "amount"])
            # Se il saldo 3100 è "vuoto", lo sostituiamo col calcolato; altrimenti lo affianchiamo.
            if abs(current) < 0.005:
                equity.loc[idx, "amount"] = net_profit_ytd
                equity.loc[idx, "account_name"] = "Utile (perdita) d'esercizio (calcolato)"
            else:
                equity = pd.concat(
                    [
                        equity,
                        pd.DataFrame(
                            [
                                {
                                    "account_code": "3100*",
                                    "account_name": "Utile (perdita) d'esercizio (calcolato)",
                                    "amount": net_profit_ytd,
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )
        else:
            equity = pd.concat(
                [
                    equity,
                    pd.DataFrame(
                        [
                            {
                                "account_code": "3100",
                                "account_name": "Utile (perdita) d'esercizio (calcolato)",
                                "amount": net_profit_ytd,
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )

    total_assets = float(assets["amount"].sum()) if not assets.empty else 0.0
    total_liabilities = float(liabilities["amount"].sum()) if not liabilities.empty else 0.0
    total_equity = float(equity["amount"].sum()) if not equity.empty else 0.0

    return {
        "as_of": as_of,
        "assets": assets.sort_values("account_code").reset_index(drop=True),
        "liabilities": liabilities.sort_values("account_code").reset_index(drop=True),
        "equity": equity.sort_values("account_code").reset_index(drop=True),
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "delta": total_assets - (total_liabilities + total_equity),
    }


def cash_flow(conn: sqlite3.Connection, period: ReportPeriod) -> dict:
    df = _load_lines(conn)
    if df.empty:
        return {
            "period": period,
            "by_date": pd.DataFrame(columns=["entry_date", "delta_cash"]).astype({"delta_cash": float}),
            "net_cash": 0.0,
        }

    start = pd.to_datetime(period.start).date()
    end = pd.to_datetime(period.end).date()
    dfp = df[(df["entry_date"] >= start) & (df["entry_date"] <= end)]

    cash_codes = {"1000", "1010"}
    cash = dfp[dfp["account_code"].isin(cash_codes)].copy()
    cash["delta_cash"] = cash["debit"] - cash["credit"]

    by_date = cash.groupby("entry_date", as_index=False)["delta_cash"].sum().sort_values("entry_date")
    net_cash = float(by_date["delta_cash"].sum()) if not by_date.empty else 0.0
    return {"period": period, "by_date": by_date.reset_index(drop=True), "net_cash": net_cash}


def vat_summary(conn: sqlite3.Connection, period: ReportPeriod) -> dict:
    """Riepilogo IVA basato sui conti 2100 (IVA a debito) e 1200 (IVA a credito)."""
    df = _load_lines(conn)
    if df.empty:
        return {
            "period": period,
            "iva_debito": 0.0,
            "iva_credito": 0.0,
            "iva_netto": 0.0,
        }

    start = pd.to_datetime(period.start).date()
    end = pd.to_datetime(period.end).date()
    dfp = df[(df["entry_date"] >= start) & (df["entry_date"] <= end)]

    iva_debito = dfp[dfp["account_code"] == "2100"]
    iva_credito = dfp[dfp["account_code"] == "1200"]

    # 2100 è passivo: incremento tipico a credito
    iva_debito_amt = float((iva_debito["credit"] - iva_debito["debit"]).sum()) if not iva_debito.empty else 0.0
    # 1200 è attivo: incremento tipico a dare
    iva_credito_amt = float((iva_credito["debit"] - iva_credito["credit"]).sum()) if not iva_credito.empty else 0.0

    return {
        "period": period,
        "iva_debito": iva_debito_amt,
        "iva_credito": iva_credito_amt,
        "iva_netto": iva_debito_amt - iva_credito_amt,
    }


def estimated_taxes(conn: sqlite3.Connection, period: ReportPeriod, ires_rate: float, irap_rate: float) -> dict:
    ce = income_statement(conn, period)
    profit = float(ce["net_profit"])
    base = max(0.0, profit)
    return {
        "period": period,
        "profit": profit,
        "ires_rate": float(ires_rate),
        "irap_rate": float(irap_rate),
        "ires_estimate": base * float(ires_rate),
        "irap_estimate": base * float(irap_rate),
        "total_estimate": base * (float(ires_rate) + float(irap_rate)),
    }
