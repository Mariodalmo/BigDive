from fastapi import FastAPI

from .models import ClassifyRequest, ClassifyResponse
from .rules import classify_request, warmup_rules


app = FastAPI(title="Risk Classifier Agent", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    # Preload and validate rules on startup
    warmup_rules()


@app.post("/classify", response_model=ClassifyResponse)
def classify(payload: ClassifyRequest) -> ClassifyResponse:
    result = classify_request(payload)
    return ClassifyResponse(**result)

