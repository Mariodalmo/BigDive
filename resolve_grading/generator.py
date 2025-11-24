from __future__ import annotations

import colorsys
from typing import Dict, Tuple, Optional, Any, List

from .models import (
    AdjustmentMap,
    FootageProfile,
    TimelineProfile,
    NodeOperation,
    ResolveNode,
    LUTMetadata,
    ColorGradingConfig,
)
from .presets import get_preset, get_preset_names


_NON_LUT_KEYS = {"film_grain", "halation", "vignette"}


def _merge_adjustments(base: AdjustmentMap, overrides: Optional[AdjustmentMap]) -> AdjustmentMap:
    if not overrides:
        return dict(base)
    merged: AdjustmentMap = {}
    for key, value in base.items():
        merged[key] = value
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_adjustments(merged[key], value)
        else:
            merged[key] = value
    return merged


def _clamp(value: float, min_v: float = 0.0, max_v: float = 1.0) -> float:
    return max(min_v, min(max_v, value))


def _apply_adjustments_to_rgb(rgb: Tuple[float, float, float], adj: AdjustmentMap) -> Tuple[float, float, float]:
    r, g, b = rgb

    exposure = float(adj.get("exposure", 0.0))
    gain = 2 ** exposure
    r *= gain
    g *= gain
    b *= gain

    temp = float(adj.get("temperature_shift", 0.0)) / 800.0
    tint = float(adj.get("tint_shift", 0.0)) / 200.0
    r = _clamp(r + temp * 0.08)
    b = _clamp(b - temp * 0.08)
    g = _clamp(g - tint * 0.05)
    r = _clamp(r + tint * 0.02)
    b = _clamp(b + tint * 0.02)

    contrast = float(adj.get("contrast", 1.0))
    pivot = float(adj.get("contrast_pivot", 0.5))
    r = (r - pivot) * contrast + pivot
    g = (g - pivot) * contrast + pivot
    b = (b - pivot) * contrast + pivot

    shadow_lift = float(adj.get("shadow_lift", 0.0))
    highlight_rolloff = float(adj.get("highlight_rolloff", 0.0))
    r = r + shadow_lift * (1.0 - r) * 0.5
    g = g + shadow_lift * (1.0 - g) * 0.5
    b = b + shadow_lift * (1.0 - b) * 0.5
    r = r - highlight_rolloff * (r ** 2)
    g = g - highlight_rolloff * (g ** 2)
    b = b - highlight_rolloff * (b ** 2)

    soft_clip = float(adj.get("soft_clip", 0.0))
    if soft_clip > 0:
        def _soft(v: float) -> float:
            if v <= 1 - soft_clip:
                return v
            return 1 - soft_clip + (1 - (1 - v) / soft_clip) ** 2 * soft_clip

        r, g, b = _soft(_clamp(r)), _soft(_clamp(g)), _soft(_clamp(b))

    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    saturation = float(adj.get("saturation", 1.0))
    if saturation <= 0:
        r = g = b = luma
    else:
        r = luma + (r - luma) * saturation
        g = luma + (g - luma) * saturation
        b = luma + (b - luma) * saturation

    split_high = adj.get("split_tone_highlights")
    split_shadow = adj.get("split_tone_shadows")
    if split_high:
        hue = float(split_high.get("hue", 40)) / 360.0
        sat = float(split_high.get("sat", 0.0))
        weight = max(0.0, (luma - 0.5) * 2.0)
        tint_rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        r = _clamp((1 - weight * sat) * r + weight * sat * tint_rgb[0])
        g = _clamp((1 - weight * sat) * g + weight * sat * tint_rgb[1])
        b = _clamp((1 - weight * sat) * b + weight * sat * tint_rgb[2])
    if split_shadow:
        hue = float(split_shadow.get("hue", 200)) / 360.0
        sat = float(split_shadow.get("sat", 0.0))
        weight = max(0.0, (0.5 - luma) * 2.0)
        tint_rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        r = _clamp((1 - weight * sat) * r + weight * sat * tint_rgb[0])
        g = _clamp((1 - weight * sat) * g + weight * sat * tint_rgb[1])
        b = _clamp((1 - weight * sat) * b + weight * sat * tint_rgb[2])

    color_warp = adj.get("color_warp", {})
    if color_warp:
        h, s, v = colorsys.rgb_to_hsv(_clamp(r), _clamp(g), _clamp(b))
        for bucket, params in color_warp.items():
            weight = _bucket_weight(bucket, r, g, b)
            if weight <= 0:
                continue
            shift = float(params.get("hue_shift", 0.0)) / 360.0
            sat_offset = float(params.get("sat", 0.0))
            h = (h + shift * weight) % 1.0
            s = _clamp(s + sat_offset * weight, 0.0, 1.0)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)

    luma_mix = adj.get("luma_mix")
    if luma_mix is not None:
        mix = float(luma_mix)
        r = luma * mix + r * (1 - mix)
        g = luma * mix + g * (1 - mix)
        b = luma * mix + b * (1 - mix)

    return _clamp(r), _clamp(g), _clamp(b)


def _bucket_weight(bucket: str, r: float, g: float, b: float) -> float:
    bucket = bucket.lower()
    if bucket == "reds":
        return r
    if bucket == "greens":
        return g
    if bucket == "blues":
        return b
    if bucket == "yellows":
        return min(r, g)
    if bucket == "cyans":
        return min(g, b)
    if bucket == "neutrals":
        return 1.0 - min(abs(r - g), abs(g - b))
    return 0.5


def _generate_cube(size: int, adjustments: AdjustmentMap, title: str) -> str:
    lines = [
        f"# {title}",
        "TITLE \"ResolveConfigBuilder\"",
        f"LUT_3D_SIZE {size}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
    ]
    for blue in range(size):
        for green in range(size):
            for red in range(size):
                rgb = (
                    red / (size - 1),
                    green / (size - 1),
                    blue / (size - 1),
                )
                rr, gg, bb = _apply_adjustments_to_rgb(rgb, adjustments)
                lines.append(f"{rr:.6f} {gg:.6f} {bb:.6f}")
    return "\n".join(lines) + "\n"


class ResolveConfigBuilder:
    def __init__(self, default_lut_size: int = 33):
        self.default_lut_size = default_lut_size

    def build(
        self,
        preset_name: str,
        footage_profile: FootageProfile,
        timeline_profile: Optional[TimelineProfile] = None,
        custom_adjustments: Optional[AdjustmentMap] = None,
        include_lut: bool = False,
        lut_size: Optional[int] = None,
        lut_title: Optional[str] = None,
    ) -> Tuple[ColorGradingConfig, Optional[str]]:
        preset = get_preset(preset_name)
        adjustments = _merge_adjustments(preset.base_adjustments, custom_adjustments)
        timeline = timeline_profile or TimelineProfile()
        nodes = self._build_node_tree(footage_profile, timeline, adjustments, preset.look_notes)
        lut_metadata = None
        lut_str = None

        if include_lut:
            lut_sz = lut_size or self.default_lut_size
            safe_adjustments = {k: v for k, v in adjustments.items() if k not in _NON_LUT_KEYS}
            title = lut_title or f"{preset.label} LUT"
            lut_str = _generate_cube(lut_sz, safe_adjustments, title)
            lut_metadata = LUTMetadata(
                title=title,
                size=lut_sz,
                file_path=None,
                applied_adjustments=safe_adjustments,
            )

        config = ColorGradingConfig(
            preset=preset.label,
            preset_description=preset.description,
            footage_profile=footage_profile,
            timeline_profile=timeline,
            nodes=nodes,
            look_notes=preset.look_notes,
            recommended_inputs=preset.recommended_inputs,
            lut_metadata=lut_metadata,
        )
        return config, lut_str

    def _build_node_tree(
        self,
        footage: FootageProfile,
        timeline: TimelineProfile,
        adjustments: AdjustmentMap,
        look_notes: List[str],
    ) -> List[ResolveNode]:
        nodes: List[ResolveNode] = []

        nodes.append(
            ResolveNode(
                name="Node 01 - CST Input",
                role="Color space transform (input)",
                operations=[
                    NodeOperation(
                        tool="Color Space Transform",
                        parameters={
                            "Input Gamma": footage.capture_gamma,
                            "Input Gamut": footage.capture_gamut,
                            "Timeline Gamma": timeline.timeline_gamma,
                            "Timeline Gamut": timeline.timeline_gamut,
                        },
                        notes="Normalizza il girato nel working space prima delle correzioni creative.",
                    )
                ],
            )
        )

        nodes.append(
            ResolveNode(
                name="Node 02 - Primaries",
                role="Bilanciamento e esposizione",
                operations=[
                    NodeOperation(
                        tool="Offset / Temperature",
                        parameters={
                            "Temp Shift (K)": adjustments.get("temperature_shift", 0),
                            "Tint Shift": adjustments.get("tint_shift", 0),
                            "Exposure Stops": adjustments.get("exposure", 0.0),
                            "Camera Offset (stops)": footage.exposure_offset,
                            "ISO Nota": footage.iso,
                            "WB Kelvin": footage.white_balance_kelvin,
                        },
                        notes="Compensa condizioni di partenza (log/Rec.709) e porta la pelle nella zona corretta.",
                    )
                ],
            )
        )

        nodes.append(
            ResolveNode(
                name="Node 03 - Contrasto",
                role="Curve e roll-off",
                operations=[
                    NodeOperation(
                        tool="Custom Curves",
                        parameters={
                            "Contrast": adjustments.get("contrast", 1.0),
                            "Pivot": adjustments.get("contrast_pivot", 0.5),
                            "Shadow Lift": adjustments.get("shadow_lift", 0.0),
                            "Highlight Rolloff": adjustments.get("highlight_rolloff", 0.0),
                            "Soft Clip": adjustments.get("soft_clip", 0.0),
                        },
                        notes="Costruisce la S-curve principale per rispettare la dinamica richiesta.",
                    ),
                    NodeOperation(
                        tool="Midtone Detail",
                        parameters={"Amount": adjustments.get("midtone_detail", 0.0)},
                        notes="Regola la percezione dei volumi senza intaccare latching dei neri.",
                    ),
                ],
            )
        )

        nodes.append(
            ResolveNode(
                name="Node 04 - Palette",
                role="Gestione cromatica",
                operations=[
                    NodeOperation(
                        tool="Hue/Sat vs Hue",
                        parameters=adjustments.get("color_warp", {}),
                        notes="Warp cromatico (verdure verso ciano, pelle neutra, etc.).",
                    ),
                    NodeOperation(
                        tool="Split Toning",
                        parameters={
                            "Highlights": adjustments.get("split_tone_highlights", {}),
                            "Shadows": adjustments.get("split_tone_shadows", {}),
                        },
                        notes="Bilancia cromaticamente alte e basse luci secondo il preset scelto.",
                    ),
                    NodeOperation(
                        tool="Saturation",
                        parameters={"Global": adjustments.get("saturation", 1.0)},
                        notes="Fine tuning della saturazione globale e dei primari.",
                    ),
                ],
            )
        )

        nodes.append(
            ResolveNode(
                name="Node 05 - Texture",
                role="Pellicola e FX",
                operations=[
                    NodeOperation(
                        tool="Film Grain / Texture",
                        parameters={
                            "Grain Amount": adjustments.get("film_grain", 0.0),
                            "Halation": adjustments.get("halation", 0.0),
                            "Vignette": adjustments.get("vignette", 0.0),
                        },
                        notes="Configura plugin Resolve FX Grain + Glow per replicare la resa analogica.",
                    )
                ],
            )
        )

        nodes.append(
            ResolveNode(
                name="Node 06 - Output",
                role="Transform finale",
                operations=[
                    NodeOperation(
                        tool="Color Space Transform",
                        parameters={
                            "Input Gamma": timeline.timeline_gamma,
                            "Input Gamut": timeline.timeline_gamut,
                            "Output Gamma": timeline.output_transform,
                            "Output Gamut": "Rec.709",
                        },
                        notes="Adatta il grading al deliverable (Rec.709, HDR, ecc.).",
                    )
                ],
            )
        )

        if look_notes:
            nodes.append(
                ResolveNode(
                    name="Node 07 - Note creative",
                    role="Annotazioni",
                    operations=[
                        NodeOperation(
                            tool="Note",
                            parameters={"Suggerimenti": look_notes},
                            notes="Promemoria operativo all'interno della timeline Resolve.",
                        )
                    ],
                    bypass=True,
                )
            )

        return nodes

    def describe_presets(self) -> List[Dict[str, Any]]:
        return [get_preset(name).to_public_dict() for name in get_preset_names()]
