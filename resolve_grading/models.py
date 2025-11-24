from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any


AdjustmentMap = Dict[str, Any]


@dataclass
class FootageProfile:
    capture_gamma: str
    capture_gamut: str
    camera: Optional[str] = None
    white_balance_kelvin: Optional[int] = None
    iso: Optional[int] = None
    exposure_offset: float = 0.0
    lighting_notes: Optional[str] = None
    shooting_conditions: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineProfile:
    timeline_gamma: str = "DaVinci Intermediate"
    timeline_gamut: str = "DaVinci Wide Gamut"
    output_transform: str = "Rec.709 Gamma 2.4"
    render_resolution: str = "3840x2160"
    frame_rate: str = "24"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NodeOperation:
    tool: str
    parameters: Dict[str, Any]
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "tool": self.tool,
            "parameters": self.parameters,
        }
        if self.notes:
            data["notes"] = self.notes
        return data


@dataclass
class ResolveNode:
    name: str
    role: str
    operations: List[NodeOperation]
    bypass: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "bypass": self.bypass,
            "operations": [op.to_dict() for op in self.operations],
        }


@dataclass
class LUTMetadata:
    title: str
    size: int
    file_path: Optional[str]
    applied_adjustments: AdjustmentMap

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ColorGradingConfig:
    preset: str
    preset_description: str
    footage_profile: FootageProfile
    timeline_profile: TimelineProfile
    nodes: List[ResolveNode]
    look_notes: List[str] = field(default_factory=list)
    recommended_inputs: List[str] = field(default_factory=list)
    lut_metadata: Optional[LUTMetadata] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preset": self.preset,
            "preset_description": self.preset_description,
            "footage_profile": self.footage_profile.to_dict(),
            "timeline_profile": self.timeline_profile.to_dict(),
            "nodes": [node.to_dict() for node in self.nodes],
            "look_notes": list(self.look_notes),
            "recommended_inputs": list(self.recommended_inputs),
            "lut_metadata": self.lut_metadata.to_dict() if self.lut_metadata else None,
        }


@dataclass(frozen=True)
class PresetDefinition:
    key: str
    label: str
    description: str
    base_adjustments: AdjustmentMap
    look_notes: List[str]
    recommended_inputs: List[str]

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "base_adjustments": self.base_adjustments,
            "look_notes": self.look_notes,
            "recommended_inputs": self.recommended_inputs,
        }
