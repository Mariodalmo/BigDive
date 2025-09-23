from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


app = FastAPI(title="Human Oversight Simulator")


class HumanReviewRequest(BaseModel):
    case_id: str = Field(..., description="Unique identifier for the case under review")
    risk_level: str = Field(..., description="Risk level classification for the case")
    justification: Optional[str] = Field(None, description="Short justification for the classification")
    explanation: Optional[Dict[str, Any]] = Field(
        default=None, description="Detailed explanation payload, arbitrary key-value structure"
    )


class HumanReviewResponse(BaseModel):
    decision: str
    reviewer: str
    comments: str


def should_escalate(risk_level: str, explanation: Optional[Dict[str, Any]]) -> bool:
    if risk_level.lower() == "high":
        return True
    if not explanation:
        return True
    if isinstance(explanation, dict) and len(explanation) == 0:
        return True
    return False


@app.post("/human_review", response_model=HumanReviewResponse)
def human_review(payload: HumanReviewRequest) -> HumanReviewResponse:
    try:
        escalate = should_escalate(payload.risk_level, payload.explanation)
        if escalate:
            decision = "recheck_required"
            reviewer = "senior_reviewer_bot"
            comments = (
                "Escalated due to high risk level or missing/empty explanation; human recheck required."
            )
        else:
            decision = "approved"
            reviewer = "auto_reviewer_bot"
            comments = "Approved by simulated oversight based on provided explanation and risk level."
        return HumanReviewResponse(decision=decision, reviewer=reviewer, comments=comments)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

