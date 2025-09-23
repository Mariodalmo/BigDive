from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackIn(BaseModel):
    """Inbound payload for submitting risk classification feedback."""

    system_name: str = Field(..., min_length=1)
    original_risk: str = Field(..., min_length=1)
    corrected_risk: str = Field(..., min_length=1)
    justification: str = Field(..., min_length=1)
    reviewer: str = Field(..., min_length=1)


class FeedbackEntry(FeedbackIn):
    """Stored feedback entry including server-side metadata."""

    timestamp: datetime


class FeedbackOut(BaseModel):
    """Response wrapper returned by the API."""

    status: str
    entry: FeedbackEntry

