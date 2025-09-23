from fastapi import FastAPI

from .schemas import (
    UpdateKnowledgeRequest,
    UpdateKnowledgeResponse,
)
from .storage import add_documents, list_documents


app = FastAPI(title="Regulation Watchdog Agent")


@app.post("/update_knowledge", response_model=UpdateKnowledgeResponse)
def update_knowledge(payload: UpdateKnowledgeRequest) -> UpdateKnowledgeResponse:
    stored = add_documents(payload.documents)
    return UpdateKnowledgeResponse(count=len(stored), documents=stored)


@app.get("/knowledge")
def get_knowledge():
    docs = list_documents()
    return {"count": len(docs), "documents": docs}

