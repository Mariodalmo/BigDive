import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

from app.models import FeedbackIn, FeedbackEntry, FeedbackOut
from app.storage import GroundTruthStore


def create_app(store_path: Optional[str] = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    resolved_path = store_path or os.getenv("GROUND_TRUTH_PATH", str(Path("data") / "ground_truth.json"))
    store = GroundTruthStore(Path(resolved_path))

    app = FastAPI(
        title="Classification Feedback Agent",
        description="Raccoglie feedback correttivo sui livelli di rischio assegnati.",
        version="0.1.0",
    )

    @app.on_event("startup")
    async def _startup() -> None:  # noqa: D401
        # Ensure the store file exists before handling requests
        store.ensure_initialized()

    @app.post("/submit_feedback", response_model=FeedbackOut)
    async def submit_feedback(payload: FeedbackIn) -> FeedbackOut:
        entry = FeedbackEntry(**payload.model_dump(), timestamp=datetime.utcnow())
        stored = store.append(entry.model_dump())
        return FeedbackOut(status="ok", entry=FeedbackEntry(**stored))

    return app


app = create_app()

