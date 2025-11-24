from __future__ import annotations

import json
from typing import Any, Dict, List

import streamlit as st

from resolve_grading import (
    FootageProfile,
    TimelineProfile,
    ResolveConfigBuilder,
    get_preset,
    get_preset_names,
)


st.set_page_config(page_title="Color Grading Builder", layout="wide")


def _parse_override(raw: str) -> Dict[str, Any]:
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Gli override devono essere un oggetto JSON (es. {\"contrast\": 1.05}).")
        return data
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON non valido: {exc.msg}") from exc


def _preset_options(builder: ResolveConfigBuilder) -> List[Dict[str, Any]]:
    return builder.describe_presets()


def main() -> None:
    st.title("Generatore configurazioni DaVinci Resolve")
    st.caption("Crea preset, nodi e LUT coerenti con gli stili richiesti.")

    builder = ResolveConfigBuilder()
    presets = _preset_options(builder)
    preset_map = {preset["key"]: preset for preset in presets}
    preset_keys = get_preset_names()

    with st.sidebar:
        st.header("Preset e export")
        preset_key = st.selectbox(
            "Preset Cinematografico",
            preset_keys,
            format_func=lambda key: f"{preset_map[key]['label']} ({key})",
        )
        include_lut = st.checkbox("Genera LUT .cube", value=True)
        lut_size = st.slider("Dimensione LUT", min_value=17, max_value=65, step=2, value=33)
        download_filename = st.text_input("Nome file LUT", value=f"{preset_key}.cube")

    preset_info = preset_map[preset_key]
    with st.expander("Dettagli preset selezionato", expanded=True):
        st.markdown(f"**{preset_info['label']}** — {preset_info['description']}")
        st.markdown("**Input consigliati:** " + ", ".join(preset_info["recommended_inputs"]))
        st.markdown("**Note look:**")
        for note in preset_info["look_notes"]:
            st.markdown(f"- {note}")

    cols = st.columns(2)
    with cols[0]:
        st.subheader("Profilo del girato")
        capture_gamma = st.text_input("Capture gamma", value="ARRI LogC3")
        capture_gamut = st.text_input("Capture gamut", value="ARRI Wide Gamut 3")
        camera = st.text_input("Camera / Sensore", value="ARRI Alexa")
        white_balance = st.number_input("White balance (K)", value=5600, step=100)
        iso = st.number_input("ISO", value=800, step=100)
        exposure_offset = st.number_input("Exposure offset (stop)", value=0.0, step=0.1, format="%.2f")
        lighting_notes = st.text_input("Note illuminazione", value="Golden hour, sole basso")
        shooting_conditions = st.text_area("Condizioni di ripresa", height=70, value="Esterni, filtri 1/8 Black Pro-Mist")

    with cols[1]:
        st.subheader("Timeline / Deliverable")
        timeline_gamma = st.text_input("Timeline gamma", value="DaVinci Intermediate")
        timeline_gamut = st.text_input("Timeline gamut", value="DaVinci Wide Gamut")
        output_transform = st.text_input("Output transform", value="Rec.709 Gamma 2.4")
        render_resolution = st.text_input("Render resolution", value="3840x2160")
        frame_rate = st.text_input("Frame rate", value="24")
        st.markdown("### Override preset (JSON opzionale)")
        override_raw = st.text_area(
            "JSON override",
            placeholder='{"contrast": 1.05, "split_tone_highlights": {"hue": 32}}',
            height=120,
        )

    generate = st.button("Genera configurazione", type="primary")

    if generate:
        try:
            overrides = _parse_override(override_raw)
        except ValueError as exc:
            st.error(str(exc))
            return

        footage = FootageProfile(
            capture_gamma=capture_gamma,
            capture_gamut=capture_gamut,
            camera=camera or None,
            white_balance_kelvin=int(white_balance),
            iso=int(iso),
            exposure_offset=float(exposure_offset),
            lighting_notes=lighting_notes or None,
            shooting_conditions=shooting_conditions or None,
        )
        timeline = TimelineProfile(
            timeline_gamma=timeline_gamma,
            timeline_gamut=timeline_gamut,
            output_transform=output_transform,
            render_resolution=render_resolution,
            frame_rate=frame_rate,
        )

        try:
            config, lut_str = builder.build(
                preset_name=preset_key,
                footage_profile=footage,
                timeline_profile=timeline,
                custom_adjustments=overrides,
                include_lut=include_lut,
                lut_size=lut_size,
                lut_title=get_preset(preset_key).label,
            )
        except Exception as exc:  # pragma: no cover
            st.error(f"Errore nella generazione: {exc}")
            return

        st.success("Configurazione generata con successo.")
        config_dict = config.to_dict()
        st.subheader("Configurazione JSON")
        st.json(config_dict)

        json_bytes = json.dumps(config_dict, indent=2, ensure_ascii=False).encode("utf-8")
        st.download_button(
            "Scarica JSON configurazione",
            data=json_bytes,
            file_name=f"{preset_key}_config.json",
            mime="application/json",
        )

        if include_lut and lut_str:
            st.subheader("LUT generata")
            st.code("\n".join(lut_str.splitlines()[:20]) + "\n...", language="text")
            st.download_button(
                "Scarica LUT .cube",
                data=lut_str.encode("utf-8"),
                file_name=download_filename or f"{preset_key}.cube",
                mime="text/plain",
            )


if __name__ == "__main__":
    main()
