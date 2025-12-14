from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from contabilita import db, reports


st.set_page_config(page_title="Contabilità semplice", layout="wide")


def euro(amount: float) -> str:
    return f"{amount:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def get_db_path() -> Path:
    base = Path(st.session_state.get("db_dir", "."))
    return base / "contabilita.sqlite3"


@st.cache_resource
def get_conn(db_path_str: str):
    conn = db.connect(db_path_str)
    db.init_db(conn)
    return conn


st.sidebar.header("Impostazioni")

with st.sidebar:
    db_dir = st.text_input("Cartella dati", value=".")
    st.session_state["db_dir"] = db_dir
    conn = get_conn(str(get_db_path()))

    company_name = db.get_setting(conn, "company_name", "")
    company_name_new = st.text_input("Nome azienda", value=company_name)
    if company_name_new != company_name:
        db.set_setting(conn, "company_name", company_name_new)

    ires = float(db.get_setting(conn, "tax_ires_rate", "0.24"))
    irap = float(db.get_setting(conn, "tax_irap_rate", "0.039"))
    ires_new = st.number_input("Aliquota IRES (stima)", min_value=0.0, max_value=1.0, value=ires, step=0.001, format="%.3f")
    irap_new = st.number_input("Aliquota IRAP (stima)", min_value=0.0, max_value=1.0, value=irap, step=0.001, format="%.3f")
    if ires_new != ires:
        db.set_setting(conn, "tax_ires_rate", str(ires_new))
    if irap_new != irap:
        db.set_setting(conn, "tax_irap_rate", str(irap_new))


st.title("Gestione contabile semplice")

pages = [
    "Inserisci movimento",
    "Movimenti (ultimi)",
    "Cash flow",
    "Conto economico",
    "Stato patrimoniale",
    "Riepilogo contabile e fiscale",
    "Piano dei conti",
]
page = st.tabs(pages)

accounts = db.list_accounts(conn)
acc_df = pd.DataFrame(accounts)
acc_label = {
    int(r["id"]): f"{r['code']} - {r['name']} ({r['kind']})" for r in accounts
}


with page[0]:
    st.subheader("Inserisci movimento (partita doppia)")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        entry_date = st.date_input("Data", value=date.today())
        doc_ref = st.text_input("Riferimento documento (facoltativo)")
    with col2:
        description = st.text_input("Descrizione", value="")
        st.caption("Suggerimento: per IVA inserisci righe su 2100 (IVA a debito) / 1200 (IVA a credito).")
    with col3:
        st.write("")
        st.write("")
        save = st.button("Salva movimento", type="primary")

    st.markdown("---")
    st.write("Righe contabili")

    if "lines" not in st.session_state:
        st.session_state["lines"] = [
            {"account_id": accounts[0]["id"], "debit": 0.0, "credit": 0.0, "note": ""},
            {"account_id": accounts[1]["id"], "debit": 0.0, "credit": 0.0, "note": ""},
        ]

    lines = st.session_state["lines"]

    def line_editor(idx: int):
        l = lines[idx]
        c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 4])
        with c1:
            l["account_id"] = st.selectbox(
                f"Conto #{idx+1}",
                options=[int(a["id"]) for a in accounts],
                format_func=lambda x: acc_label.get(int(x), str(x)),
                index=[int(a["id"]) for a in accounts].index(int(l["account_id"])) if accounts else 0,
                key=f"acc_{idx}",
            )
        with c2:
            l["debit"] = st.number_input(f"Dare #{idx+1}", min_value=0.0, value=float(l.get("debit", 0.0)), step=0.01, key=f"d_{idx}")
        with c3:
            l["credit"] = st.number_input(f"Avere #{idx+1}", min_value=0.0, value=float(l.get("credit", 0.0)), step=0.01, key=f"c_{idx}")
        with c4:
            remove = st.button("Rimuovi", key=f"rm_{idx}")
        with c5:
            l["note"] = st.text_input(f"Nota #{idx+1}", value=str(l.get("note", "")), key=f"n_{idx}")
        return remove

    to_remove = None
    for i in range(len(lines)):
        if line_editor(i):
            to_remove = i

    add_col1, add_col2 = st.columns([1, 5])
    with add_col1:
        if st.button("+ Aggiungi riga"):
            lines.append({"account_id": accounts[0]["id"], "debit": 0.0, "credit": 0.0, "note": ""})
    with add_col2:
        total_debit = sum(float(l.get("debit", 0.0)) for l in lines)
        total_credit = sum(float(l.get("credit", 0.0)) for l in lines)
        st.info(f"Totale Dare: {euro(total_debit)} | Totale Avere: {euro(total_credit)} | Differenza: {euro(total_debit-total_credit)}")

    if to_remove is not None and len(lines) > 2:
        lines.pop(to_remove)
        st.rerun()

    if save:
        try:
            payload = []
            for l in lines:
                debit_cents = int(round(float(l.get("debit", 0.0)) * 100))
                credit_cents = int(round(float(l.get("credit", 0.0)) * 100))
                payload.append(
                    {
                        "account_id": int(l["account_id"]),
                        "debit_cents": debit_cents,
                        "credit_cents": credit_cents,
                        "note": l.get("note") or None,
                    }
                )
            entry_id = db.create_entry(
                conn,
                entry_date=str(entry_date),
                description=description.strip() or "Movimento",
                doc_ref=(doc_ref.strip() or None),
                lines=payload,
            )
            st.success(f"Movimento salvato (ID {entry_id}).")
        except Exception as e:
            st.error(str(e))


with page[1]:
    st.subheader("Ultimi movimenti")
    entries = db.list_entries(conn, limit=200)
    if not entries:
        st.info("Nessun movimento registrato.")
    else:
        for e in entries:
            with st.expander(f"{e['entry_date']} — {e['description']} (ID {e['id']})"):
                st.write(f"Documento: {e['doc_ref'] or '—'}")
                lines = db.get_entry_lines(conn, int(e["id"]))
                df = pd.DataFrame(lines)
                if not df.empty:
                    df["Dare"] = df["debit_cents"].astype(int) / 100.0
                    df["Avere"] = df["credit_cents"].astype(int) / 100.0
                    st.dataframe(df[["code", "name", "kind", "Dare", "Avere", "note"]], use_container_width=True)


def period_picker(key: str):
    c1, c2 = st.columns(2)
    with c1:
        start = st.date_input("Dal", value=date(date.today().year, 1, 1), key=f"{key}_s")
    with c2:
        end = st.date_input("Al", value=date.today(), key=f"{key}_e")
    return reports.ReportPeriod(str(start), str(end))


with page[2]:
    st.subheader("Cash flow (variazione Cassa+Banca)")
    p = period_picker("cf")
    rep = reports.cash_flow(conn, p)
    st.metric("Cash flow netto", euro(rep["net_cash"]))
    st.dataframe(rep["by_date"], use_container_width=True)


with page[3]:
    st.subheader("Conto economico")
    p = period_picker("ce")
    ce = reports.income_statement(conn, p)
    c1, c2, c3 = st.columns(3)
    c1.metric("Ricavi", euro(ce["total_income"]))
    c2.metric("Costi", euro(ce["total_expenses"]))
    c3.metric("Utile/Perdita", euro(ce["net_profit"]))
    col1, col2 = st.columns(2)
    with col1:
        st.write("Ricavi")
        st.dataframe(ce["income"], use_container_width=True)
    with col2:
        st.write("Costi")
        st.dataframe(ce["expenses"], use_container_width=True)


with page[4]:
    st.subheader("Stato patrimoniale")
    as_of = st.date_input("Data di riferimento", value=date.today(), key="sp_asof")
    bs = reports.balance_sheet(conn, str(as_of))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totale Attivo", euro(bs["total_assets"]))
    c2.metric("Totale Passivo", euro(bs["total_liabilities"]))
    c3.metric("Totale Patrimonio Netto", euro(bs["total_equity"]))
    c4.metric("Squadratura", euro(bs["delta"]))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("Attivo")
        st.dataframe(bs["assets"], use_container_width=True)
    with col2:
        st.write("Passivo")
        st.dataframe(bs["liabilities"], use_container_width=True)
    with col3:
        st.write("Patrimonio netto")
        st.dataframe(bs["equity"], use_container_width=True)


with page[5]:
    st.subheader("Riepilogo contabile e fiscale")
    p = period_picker("rf")

    tb = reports.trial_balance(conn, up_to=p.end)
    st.write("Bilancino (saldo per conto)")
    st.dataframe(tb, use_container_width=True)

    st.markdown("---")
    v = reports.vat_summary(conn, p)
    c1, c2, c3 = st.columns(3)
    c1.metric("IVA a debito (periodo)", euro(v["iva_debito"]))
    c2.metric("IVA a credito (periodo)", euro(v["iva_credito"]))
    c3.metric("IVA netta (da versare se > 0)", euro(v["iva_netto"]))

    st.markdown("---")
    ires = float(db.get_setting(conn, "tax_ires_rate", "0.24"))
    irap = float(db.get_setting(conn, "tax_irap_rate", "0.039"))
    t = reports.estimated_taxes(conn, p, ires_rate=ires, irap_rate=irap)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Utile (periodo)", euro(t["profit"]))
    c2.metric("IRES stimata", euro(t["ires_estimate"]))
    c3.metric("IRAP stimata", euro(t["irap_estimate"]))
    c4.metric("Totale imposte stimate", euro(t["total_estimate"]))

    st.caption("Nota: imposte = stima semplificata su utile positivo; non sostituisce consulenza fiscale.")


with page[6]:
    st.subheader("Piano dei conti")
    st.dataframe(acc_df[["code", "name", "kind"]], use_container_width=True)

    st.caption(
        "Per adattare i conti alla tua azienda puoi estendere `contabilita/chart_of_accounts.py` "
        "oppure aggiungere conti direttamente nel DB (funzione non ancora in UI)."
    )
