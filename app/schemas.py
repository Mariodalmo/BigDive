from typing import List, Literal

from pydantic import BaseModel, HttpUrl, field_validator
from datetime import datetime


# Allowed document types for basic validation
DocumentType = Literal["law", "regulation", "directive", "guideline", "other"]


class DocumentIn(BaseModel):
    title: str
    url: HttpUrl
    type: DocumentType

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be empty")
        return cleaned


class DocumentStored(BaseModel):
    id: str
    title: str
    url: HttpUrl
    type: DocumentType
    status: Literal["pending", "processed"]
    created_at: datetime
    updated_at: datetime


class UpdateKnowledgeRequest(BaseModel):
    documents: List[DocumentIn]


class UpdateKnowledgeResponse(BaseModel):
    count: int
    documents: List[DocumentStored]

