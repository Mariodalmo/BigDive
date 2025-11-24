from __future__ import annotations

from typing import Dict, List

from .models import PresetDefinition


def _note(text: str) -> str:
    return text.strip()


PRESETS: Dict[str, PresetDefinition] = {}


def _register(preset: PresetDefinition) -> None:
    PRESETS[preset.key] = preset


_register(
    PresetDefinition(
        key="cinema_orientale",
        label="Cinema orientale romantico",
        description=(
            "Pelle ambrata, verdi virati verso il ciano e roll-off morbido sulle alte luci. "
            "Ideale per drammi romantici e scene al tramonto."
        ),
        base_adjustments={
            "contrast": 1.08,
            "contrast_pivot": 0.43,
            "saturation": 1.12,
            "temperature_shift": 180,
            "tint_shift": -4,
            "shadow_lift": 0.018,
            "highlight_rolloff": 0.12,
            "midtone_detail": -0.2,
            "exposure": 0.15,
            "split_tone_highlights": {"hue": 35, "sat": 0.08},
            "split_tone_shadows": {"hue": 205, "sat": 0.21},
            "color_warp": {
                "greens": {"hue_shift": -6, "sat": -0.05},
                "reds": {"hue_shift": 2, "sat": 0.03},
                "blues": {"hue_shift": 4, "sat": 0.02},
            },
            "film_grain": 0.35,
            "halation": 0.22,
            "vignette": 0.08,
            "soft_clip": 0.01,
        },
        look_notes=[
            _note("Bilanciamento caldo sulle alte luci per valorizzare le carnagioni mediterranee."),
            _note("Virata dei verdi verso il ciano con saturazione controllata per la vegetazione."),
            _note("Inserire alone diffuso sulle luci puntiformi per evocare la fotografia su pellicola."),
        ],
        recommended_inputs=["ARRI LogC4", "Sony S-Log3", "Blackmagic Film Gen5"],
    )
)

_register(
    PresetDefinition(
        key="wes_anderson",
        label="Pastello simmetrico (Wes Anderson)",
        description=(
            "Palette pastello ad alto micro-contrasto, neri profondi ma puliti e tonalità della pelle neutre. "
            "Pensato per commedie visive molto stilizzate."
        ),
        base_adjustments={
            "contrast": 1.1,
            "contrast_pivot": 0.5,
            "saturation": 1.2,
            "temperature_shift": 60,
            "tint_shift": 3,
            "shadow_lift": 0.01,
            "highlight_rolloff": 0.05,
            "midtone_detail": 0.25,
            "exposure": -0.05,
            "split_tone_highlights": {"hue": 45, "sat": 0.05},
            "split_tone_shadows": {"hue": 220, "sat": 0.18},
            "color_warp": {
                "yellows": {"hue_shift": -4, "sat": 0.09},
                "reds": {"hue_shift": 4, "sat": 0.04},
                "blues": {"hue_shift": -3, "sat": -0.02},
            },
            "film_grain": 0.18,
            "halation": 0.12,
            "vignette": 0.04,
            "soft_clip": 0.006,
        },
        look_notes=[
            _note("Palette pastello con particolare cura alla separazione dei toni primari."),
            _note("Micro-contrasto elevato per enfatizzare scenografie e costumi simmetrici."),
            _note("LUT finale deve mantenere neri puliti per non perdere i dettagli architettonici."),
        ],
        recommended_inputs=["ARRI LogC3", "RED IPP2 Log3G10", "Panasonic V-Log"],
    )
)

_register(
    PresetDefinition(
        key="bw",
        label="B&W analogico",
        description=(
            "Conversione in bianco e nero con separazione ortocromatica, grana marcata e forte struttura dei mezzitoni."
        ),
        base_adjustments={
            "contrast": 1.18,
            "contrast_pivot": 0.48,
            "saturation": 0.0,
            "shadow_lift": -0.02,
            "highlight_rolloff": 0.16,
            "midtone_detail": 0.35,
            "exposure": 0.1,
            "film_grain": 0.55,
            "halation": 0.05,
            "vignette": 0.12,
            "luma_mix": 0.85,
            "soft_clip": 0.02,
        },
        look_notes=[
            _note("Utilizzare mixer dei canali per controllare la luminanza su pelle e cielo."),
            _note("Grana 35mm evidente, con lieve pulizia sul rumore cromatico."),
            _note("Curve a S pronunciata e roll-off morbido per evitare clipping."),
        ],
        recommended_inputs=["BMD Film Gen5", "RED IPP2 Log3G10", "Rec.709 gamma 2.4"],
    )
)

_register(
    PresetDefinition(
        key="kubrick",
        label="Precisione fredda (Kubrick)",
        description=(
            "Toni freddi, saturazione moderata e forte controllo su luci e simmetrie. "
            "Ideale per thriller psicologici e scenografie geometriche."
        ),
        base_adjustments={
            "contrast": 1.06,
            "contrast_pivot": 0.52,
            "saturation": 0.95,
            "temperature_shift": -120,
            "tint_shift": 2,
            "shadow_lift": -0.012,
            "highlight_rolloff": 0.08,
            "midtone_detail": 0.18,
            "exposure": -0.07,
            "split_tone_highlights": {"hue": 80, "sat": 0.03},
            "split_tone_shadows": {"hue": 210, "sat": 0.22},
            "color_warp": {
                "cyans": {"hue_shift": 5, "sat": 0.1},
                "reds": {"hue_shift": -6, "sat": -0.05},
            },
            "film_grain": 0.22,
            "halation": 0.08,
            "vignette": 0.06,
            "soft_clip": 0.009,
        },
        look_notes=[
            _note("Bilanciamento freddo ma con pelle neutra tramite node di compensazione."),
            _note("Curve controllate per evitare bloom indesiderato sulle luci speculari."),
            _note("Ridurre saturazione globale e aumentare dettaglio dei mezzitoni."),
        ],
        recommended_inputs=["ARRI LogC3", "Sony S-Log3", "Canon C-Log2"],
    )
)

_register(
    PresetDefinition(
        key="fellini",
        label="Neorealismo Fellini",
        description=(
            "Look italiano d'epoca con mezzitoni morbidi, saturazione contenuta e leggere deviazioni "
            "verso il seppia sulle alte luci."
        ),
        base_adjustments={
            "contrast": 1.02,
            "contrast_pivot": 0.46,
            "saturation": 0.9,
            "temperature_shift": 90,
            "tint_shift": -6,
            "shadow_lift": 0.035,
            "highlight_rolloff": 0.18,
            "midtone_detail": -0.15,
            "exposure": 0.05,
            "split_tone_highlights": {"hue": 28, "sat": 0.12},
            "split_tone_shadows": {"hue": 210, "sat": 0.08},
            "color_warp": {
                "neutrals": {"hue_shift": 2, "sat": -0.03},
                "blues": {"hue_shift": -5, "sat": -0.06},
            },
            "film_grain": 0.4,
            "halation": 0.18,
            "vignette": 0.15,
            "soft_clip": 0.015,
        },
        look_notes=[
            _note("Riprodurre leggero bagliore sulle finestre attraverso un node Glow o OFX."),
            _note("Ridurre saturazione globale, mantenendo separate le tonalità della pelle."),
            _note("Applicare vignettatura organica per concentrare lo sguardo al centro dell'inquadratura."),
        ],
        recommended_inputs=["Rec.709 gamma 2.4", "ARRI LogC4", "Fuji F-Log2"],
    )
)


def get_preset(name: str) -> PresetDefinition:
    try:
        return PRESETS[name]
    except KeyError as exc:
        raise KeyError(f"Preset '{name}' non trovato. Presets disponibili: {', '.join(PRESETS)}") from exc


def get_preset_names() -> List[str]:
    return list(PRESETS.keys())
