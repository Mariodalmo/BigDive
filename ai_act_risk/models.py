from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


class RiskCategory(str, Enum):
    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class ImpactArea(str, Enum):
    PRIVACY = "privacy"
    NON_DISCRIMINATION = "non_discrimination"
    SAFETY = "safety"
    DIGNITY = "dignity"
    AUTONOMY = "autonomy"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"
    SECURITY = "security"


class MitigationType(str, Enum):
    TECHNICAL = "technical"
    ORGANIZATIONAL = "organizational"
    PROCEDURAL = "procedural"


@dataclass
class MitigationMeasure:
    type: MitigationType
    name: str
    description: Optional[str] = None
    references: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "references": list(self.references) if self.references else [],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MitigationMeasure":
        return MitigationMeasure(
            type=MitigationType(data.get("type", MitigationType.TECHNICAL.value)),
            name=data.get("name", ""),
            description=data.get("description"),
            references=list(data.get("references", [])),
        )


@dataclass
class AISystemDescription:
    name: str
    overview: str
    techniques: List[str]
    domain: str
    use_cases: List[str]
    inputs: List[str]
    outputs: List[str]
    human_in_the_loop: bool
    autonomous_decision_making: bool
    data_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AISystemDescription":
        return AISystemDescription(
            name=data.get("name", "Unnamed System"),
            overview=data.get("overview", ""),
            techniques=list(data.get("techniques", [])),
            domain=data.get("domain", ""),
            use_cases=list(data.get("use_cases", [])),
            inputs=list(data.get("inputs", [])),
            outputs=list(data.get("outputs", [])),
            human_in_the_loop=bool(data.get("human_in_the_loop", False)),
            autonomous_decision_making=bool(data.get("autonomous_decision_making", False)),
            data_sources=list(data.get("data_sources", [])),
        )


@dataclass
class FRIAEntry:
    area: ImpactArea
    risk_level: Literal["low", "medium", "high"]
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "area": self.area.value,
            "risk_level": self.risk_level,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "FRIAEntry":
        return FRIAEntry(
            area=ImpactArea(data.get("area", ImpactArea.PRIVACY.value)),
            risk_level=data.get("risk_level", "medium"),
            notes=data.get("notes"),
        )


@dataclass
class LifecycleRisks:
    design: List[str] = field(default_factory=list)
    training: List[str] = field(default_factory=list)
    validation: List[str] = field(default_factory=list)
    deployment: List[str] = field(default_factory=list)
    post_market: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DatasetProfile:
    representative: Optional[bool] = None
    bias_evaluated: Optional[bool] = None
    pii_present: Optional[bool] = None
    num_samples: Optional[int] = None
    domain_coverage: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "DatasetProfile":
        return DatasetProfile(
            representative=data.get("representative"),
            bias_evaluated=data.get("bias_evaluated"),
            pii_present=data.get("pii_present"),
            num_samples=data.get("num_samples"),
            domain_coverage=data.get("domain_coverage"),
        )


@dataclass
class ControlContext:
    human_oversight: Literal["none", "post_hoc", "approval", "continuous"] = "none"
    supervision_description: Optional[str] = None
    logging: bool = False
    auditability: Literal["none", "partial", "full"] = "none"
    xai_available: bool = False
    security_hardening: List[str] = field(default_factory=list)
    dataset_profile: DatasetProfile = field(default_factory=DatasetProfile)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["dataset_profile"] = self.dataset_profile.to_dict()
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ControlContext":
        return ControlContext(
            human_oversight=data.get("human_oversight", "none"),
            supervision_description=data.get("supervision_description"),
            logging=bool(data.get("logging", False)),
            auditability=data.get("auditability", "none"),
            xai_available=bool(data.get("xai_available", False)),
            security_hardening=list(data.get("security_hardening", [])),
            dataset_profile=DatasetProfile.from_dict(data.get("dataset_profile", {})),
        )


@dataclass
class AssessmentInput:
    system: AISystemDescription
    intended_purpose: str
    users: List[str]
    affected_persons: List[str]
    control_context: ControlContext = field(default_factory=ControlContext)
    fria: List[FRIAEntry] = field(default_factory=list)
    additional_controls: List[MitigationMeasure] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system": self.system.to_dict(),
            "intended_purpose": self.intended_purpose,
            "users": list(self.users),
            "affected_persons": list(self.affected_persons),
            "control_context": self.control_context.to_dict(),
            "fria": [e.to_dict() for e in self.fria],
            "additional_controls": [m.to_dict() for m in self.additional_controls],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AssessmentInput":
        return AssessmentInput(
            system=AISystemDescription.from_dict(data.get("system", {})),
            intended_purpose=data.get("intended_purpose", ""),
            users=list(data.get("users", [])),
            affected_persons=list(data.get("affected_persons", [])),
            control_context=ControlContext.from_dict(data.get("control_context", {})),
            fria=[FRIAEntry.from_dict(e) for e in data.get("fria", [])],
            additional_controls=[MitigationMeasure.from_dict(m) for m in data.get("additional_controls", [])],
        )


@dataclass
class FRIAResult:
    entries: List[FRIAEntry]
    overall_risk: Literal["low", "medium", "high"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "overall_risk": self.overall_risk,
        }


@dataclass
class AssessmentResult:
    system_identified_as_ai: bool
    category: RiskCategory
    category_reasoning: str
    fria: FRIAResult
    lifecycle_risks: LifecycleRisks
    recommended_measures: List[MitigationMeasure]
    compliance_requirements: List[str]
    registration_required: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_identified_as_ai": self.system_identified_as_ai,
            "category": self.category.value,
            "category_reasoning": self.category_reasoning,
            "fria": self.fria.to_dict(),
            "lifecycle_risks": self.lifecycle_risks.to_dict(),
            "recommended_measures": [m.to_dict() for m in self.recommended_measures],
            "compliance_requirements": list(self.compliance_requirements),
            "registration_required": self.registration_required,
            "timestamp": self.timestamp.isoformat() + "Z",
        }
