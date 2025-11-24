from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .generator import ResolveConfigBuilder
from .models import FootageProfile, TimelineProfile, AdjustmentMap


def _parse_custom_overrides(values: Optional[List[str]]) -> AdjustmentMap:
    overrides: AdjustmentMap = {}
    if not values:
        return overrides
    for item in values:
        key, eq, raw = item.partition("=")
        if not eq:
            raise ValueError(f"Parametro custom non valido: '{item}'. Usa la sintassi chiave=valore.")
        key = key.strip()
        value = _auto_cast(raw.strip())
        target = overrides
        parts = key.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return overrides


def _auto_cast(value: str) -> Any:
    try:
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _footage_from_args(args: argparse.Namespace) -> FootageProfile:
    if args.footage_json:
        data = json.loads(Path(args.footage_json).read_text(encoding="utf-8"))
        return FootageProfile(**data)
    return FootageProfile(
        capture_gamma=args.capture_gamma,
        capture_gamut=args.capture_gamut,
        camera=args.camera,
        white_balance_kelvin=args.white_balance,
        iso=args.iso,
        exposure_offset=args.exposure_offset,
        lighting_notes=args.lighting,
        shooting_conditions=args.shooting,
    )


def _timeline_from_args(args: argparse.Namespace) -> TimelineProfile:
    return TimelineProfile(
        timeline_gamma=args.timeline_gamma,
        timeline_gamut=args.timeline_gamut,
        output_transform=args.output_transform,
        render_resolution=args.render_resolution,
        frame_rate=args.frame_rate,
    )


def _write_output(data: Dict[str, Any], output_path: Optional[str]) -> None:
    serialized = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path:
        Path(output_path).write_text(serialized, encoding="utf-8")
    else:
        print(serialized)


def build_parser(preset_keys: List[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generatore di configurazioni DaVinci Resolve e LUT per look cinematografici."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-presets", help="Elenca i preset disponibili")
    list_parser.add_argument("--format", choices=("json", "table"), default="table")

    gen_parser = subparsers.add_parser("generate", help="Crea configurazione e opzionalmente una LUT")
    gen_parser.add_argument(
        "--preset",
        required=True,
        choices=preset_keys,
        help=f"Preset da applicare ({', '.join(preset_keys)})",
    )
    gen_parser.add_argument("--capture-gamma", default="ARRI LogC3")
    gen_parser.add_argument("--capture-gamut", default="ARRI Wide Gamut 3")
    gen_parser.add_argument("--camera")
    gen_parser.add_argument("--white-balance", type=int)
    gen_parser.add_argument("--iso", type=int)
    gen_parser.add_argument("--exposure-offset", type=float, default=0.0)
    gen_parser.add_argument("--lighting")
    gen_parser.add_argument("--shooting")

    gen_parser.add_argument("--timeline-gamma", default="DaVinci Intermediate")
    gen_parser.add_argument("--timeline-gamut", default="DaVinci Wide Gamut")
    gen_parser.add_argument("--output-transform", default="Rec.709 Gamma 2.4")
    gen_parser.add_argument("--render-resolution", default="3840x2160")
    gen_parser.add_argument("--frame-rate", default="24")

    gen_parser.add_argument("--footage-json", help="Percorso a JSON con FootageProfile personalizzato")
    gen_parser.add_argument("--custom", action="append", help="Override parametri (es: split_tone_highlights.hue=60)")
    gen_parser.add_argument("--output-json", help="File JSON da salvare (stdout se omesso)")
    gen_parser.add_argument("--lut-path", help="Percorso file .cube da generare")
    gen_parser.add_argument("--lut-size", type=int, help="Dimensione LUT (default 33)")
    gen_parser.add_argument("--include-lut", action="store_true", help="Forza la generazione della LUT anche senza percorso")

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    builder = ResolveConfigBuilder()
    presets = builder.describe_presets()
    preset_keys = [p["key"] for p in presets]
    parser = build_parser(preset_keys)
    args = parser.parse_args(argv)

    if args.command == "list-presets":
        if args.format == "json":
            print(json.dumps(presets, indent=2, ensure_ascii=False))
            return
        for preset in presets:
            print(f"- {preset['key']}: {preset['label']}")
            print(f"  Input consigliati: {', '.join(preset['recommended_inputs'])}")
            print(f"  {preset['description']}")
        return

    if args.command == "generate":
        try:
            custom = _parse_custom_overrides(args.custom)
        except ValueError as exc:
            parser.error(str(exc))
        footage = _footage_from_args(args)
        timeline = _timeline_from_args(args)
        include_lut = args.include_lut or bool(args.lut_path)
        config, lut_str = builder.build(
            preset_name=args.preset,
            footage_profile=footage,
            timeline_profile=timeline,
            custom_adjustments=custom,
            include_lut=include_lut,
            lut_size=args.lut_size,
        )

        if args.lut_path and lut_str:
            Path(args.lut_path).write_text(lut_str, encoding="utf-8")
            if config.lut_metadata:
                config.lut_metadata.file_path = str(Path(args.lut_path).resolve())

        output_payload = config.to_dict()
        if lut_str and not args.lut_path:
            output_payload["lut_inline"] = lut_str

        _write_output(output_payload, args.output_json)


if __name__ == "__main__":
    main()
