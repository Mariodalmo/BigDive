import json
import time
from typing import Any, Dict, Optional, Tuple

import requests
import streamlit as st


def initialize_session_state() -> None:
    if "last_results" not in st.session_state:
        st.session_state.last_results = {}
    if "is_running" not in st.session_state:
        st.session_state.is_running = False


def post_json(base_url: str, path: str, payload: Dict[str, Any], timeout_seconds: int = 45) -> Tuple[bool, Any]:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    try:
        response = requests.post(url, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return True, response.json()
        return True, {"raw": response.text}
    except requests.exceptions.RequestException as error:
        return False, str(error)


def render_header() -> None:
    st.set_page_config(page_title="AI Compliance Dashboard", layout="wide")
    st.title("AI Compliance Dashboard")
    st.caption("Interfaccia per inserimento dati e visualizzazione risultati di conformità")


def render_sidebar_inputs() -> Dict[str, Any]:
    st.sidebar.header("Impostazioni e Input")
    api_base_url = st.sidebar.text_input(
        "API Base URL",
        value="http://localhost:8000",
        help="Endpoint di base del backend (es. http://localhost:8000)",
    )
    st.sidebar.divider()

    system_name = st.sidebar.text_input("Nome sistema", placeholder="Es. SmartVision")
    description = st.sidebar.text_area(
        "Descrizione",
        placeholder="Breve descrizione del sistema e del suo scopo",
        height=140,
    )
    has_ai = st.sidebar.checkbox("Utilizza AI?", value=True)
    biometric = st.sidebar.checkbox("Usa dati biometrici?", value=False)
    critical = st.sidebar.checkbox("In ambito critico?", value=False)
    affects_rights = st.sidebar.checkbox("Incide su diritti/fondamentali?", value=False)

    st.sidebar.divider()
    feedback_url = st.sidebar.text_input(
        "Feedback URL",
        value="mailto:compliance@example.com",
        help="Collegamento per inviare feedback (mailto o form)",
    )

    return {
        "api_base_url": api_base_url,
        "payload": {
            "system_name": system_name.strip(),
            "description": description.strip(),
            "has_ai": has_ai,
            "biometric": biometric,
            "critical": critical,
            "affects_rights": affects_rights,
        },
        "feedback_url": feedback_url,
    }


def normalize_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lower_value = value.strip().lower()
        if lower_value in {"true", "yes", "1"}:
            return True
        if lower_value in {"false", "no", "0"}:
            return False
    return None


def extract_value(data: Any, *keys: str, default: Any = None) -> Any:
    if not isinstance(data, dict):
        return default
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def render_results(results: Dict[str, Any]) -> None:
    st.subheader("Risultati")

    qualified = extract_value(results, "qualify", "qualified")
    qualified = normalize_bool(qualified)
    qualified_just = extract_value(results, "qualify", "justification")

    risk_level = extract_value(results, "classify", "risk_level")
    risk_just = extract_value(results, "classify", "justification")

    explain_scores = extract_value(results, "explain", "scores", default={})
    oversight_decision = extract_value(results, "human_review", "decision")

    cols = st.columns(3)
    with cols[0]:
        qualified_text = "Sì" if qualified is True else ("No" if qualified is False else "N/D")
        st.metric("Qualificato", qualified_text)
    with cols[1]:
        st.metric("Livello di Rischio", risk_level or "N/D")
    with cols[2]:
        st.metric("Oversight", str(oversight_decision) if oversight_decision is not None else "N/D")

    if qualified_just:
        st.info(f"Giustificazione qualificazione: {qualified_just}")

    if risk_just:
        st.info(f"Giustificazione rischio: {risk_just}")

    with st.expander("Dettagli grezzi (JSON)", expanded=False):
        st.json(results)

    if explain_scores:
        st.subheader("Indicatori di spiegabilità")
        cols2 = st.columns(min(4, max(1, len(explain_scores))))
        for index, (score_name, score_value) in enumerate(explain_scores.items()):
            with cols2[index % len(cols2)]:
                st.metric(score_name, score_value)

    fria = extract_value(results, "generate_fria")
    if fria:
        st.subheader("FRIA")
        if isinstance(fria, dict):
            if "document" in fria and isinstance(fria["document"], str):
                st.download_button("Scarica FRIA", fria["document"].encode("utf-8"), file_name="fria.txt")
            st.json(fria)
        else:
            st.write(fria)


def run_workflow(api_base_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    with st.status("Esecuzione controllo di conformità...", expanded=True) as status:
        st.write("1) Verifica qualificazione (/qualify)")
        ok, data = post_json(api_base_url, "/qualify", payload)
        if not ok:
            status.update(label="Errore durante /qualify", state="error")
            st.error(f"/qualify non raggiungibile: {data}")
            return {"error": {"qualify": data}}
        results["qualify"] = data
        qualified = normalize_bool(extract_value(data, "qualified"))

        if qualified is not True:
            status.update(label="Non qualificato o qualificazione incerta", state="complete")
            return results

        st.write("2) Classificazione del rischio (/classify)")
        ok, data = post_json(api_base_url, "/classify", payload)
        if not ok:
            status.update(label="Errore durante /classify", state="error")
            st.error(f"/classify non raggiungibile: {data}")
            return results | {"error": {"classify": data}}
        results["classify"] = data

        risk_level = extract_value(data, "risk_level")
        high_risk = isinstance(risk_level, str) and risk_level.lower() in {"high", "unacceptable", "alto", "inaccettabile"}

        if high_risk:
            st.write("3) Generazione FRIA (/generate_fria)")
            ok, data = post_json(api_base_url, "/generate_fria", payload)
            if ok:
                results["generate_fria"] = data
            else:
                st.warning(f"/generate_fria non disponibile: {data}")

        st.write("4) Spiegazioni (/explain)")
        ok, data = post_json(api_base_url, "/explain", payload)
        if ok:
            results["explain"] = data
        else:
            st.warning(f"/explain non disponibile: {data}")

        st.write("5) Oversight umano (/human_review)")
        ok, data = post_json(api_base_url, "/human_review", payload)
        if ok:
            results["human_review"] = data
        else:
            st.warning(f"/human_review non disponibile: {data}")

        status.update(label="Workflow completato", state="complete")

    return results


def main() -> None:
    initialize_session_state()
    render_header()

    cfg = render_sidebar_inputs()
    api_base_url = cfg["api_base_url"]
    payload = cfg["payload"]
    feedback_url = cfg["feedback_url"]

    with st.container(border=True):
        st.subheader("Input")
        st.write(
            "Compila i campi nella sidebar e avvia il controllo completo. I risultati verranno mostrati qui."
        )
        st.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json")

        cols = st.columns([1, 1, 2])
        with cols[0]:
            run_clicked = st.button(
                "Esegui controllo di conformità", type="primary", use_container_width=True, disabled=st.session_state.is_running
            )
        with cols[1]:
            reset_clicked = st.button("Reset", use_container_width=True)
        with cols[2]:
            if feedback_url:
                st.link_button("Invia feedback", feedback_url, use_container_width=True)

    if reset_clicked:
        st.session_state.last_results = {}
        st.session_state.is_running = False
        st.toast("Stato resettato")
        st.rerun()

    if run_clicked:
        st.session_state.is_running = True
        try:
            with st.spinner("Esecuzione in corso..."):
                results = run_workflow(api_base_url, payload)
                st.session_state.last_results = results
        finally:
            st.session_state.is_running = False
            st.rerun()

    if st.session_state.last_results:
        render_results(st.session_state.last_results)


if __name__ == "__main__":
    main()