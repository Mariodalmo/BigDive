from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OrchestrationStep(str, Enum):
    use_case = "use_case"
    risk_class = "risk_class"
    fria = "fria"
    complete = "complete"


class OrchestrationStatus(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"


class OrchestrateRequest(BaseModel):
    case_id: str = Field(..., description="Unique case identifier")
    current_step: OrchestrationStep = Field(..., description="Current saga step (last processed)")
    status: OrchestrationStatus = Field(..., description="Result status of the current step")
    last_result: Optional[Dict[str, Any]] = Field(
        default=None, description="Arbitrary payload produced by the last step"
    )


class OrchestrateCommand(BaseModel):
    name: str
    params: Dict[str, Any] = Field(default_factory=dict)


class OrchestrateResponse(BaseModel):
    next_step: OrchestrationStep
    action: str = Field(
        ..., description="What the orchestrator expects next: execute, compensate, finalize"
    )
    commands: List[OrchestrateCommand] = Field(
        default_factory=list,
        description="Commands/events to emit towards downstream agents",
    )
    compensated: List[str] = Field(
        default_factory=list, description="List of compensations performed"
    )
    notes: Optional[str] = None

