from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["high", "medium", "low", "excluded"]


class ClassifyRequest(BaseModel):
    qualified: bool = Field(..., description="Whether the system is in-scope/qualified under the AI Act")
    has_biometric: bool = Field(..., description="Whether the system uses biometric identification or categorization")
    is_critical: bool = Field(..., description="Whether the system is used for critical infrastructure or safety-critical context")
    affects_rights: bool = Field(..., description="Whether the system affects fundamental rights")


class ClassifyResponse(BaseModel):
    risk_level: RiskLevel
    reason: str

