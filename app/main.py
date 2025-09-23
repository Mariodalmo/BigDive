from fastapi import FastAPI

from .orchestrator import decide_next
from .schemas import OrchestrateRequest, OrchestrateResponse


app = FastAPI(title="Orchestration Manager")


@app.post("/orchestrate", response_model=OrchestrateResponse)
def orchestrate(request: OrchestrateRequest) -> OrchestrateResponse:
    return decide_next(request)


@app.get("/")
def root():
    return {"service": "orchestration-manager", "status": "ok"}

