import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.main import create_app


def _make_app_with_temp_store(tmp_dir_path: str) -> TestClient:
    store_path = str(Path(tmp_dir_path) / "ground_truth.json")
    os.environ["GROUND_TRUTH_PATH"] = store_path
    app = create_app()
    return TestClient(app)


def test_submit_feedback_success_and_store_increment() -> None:
    with TemporaryDirectory() as tmp_dir:
        client = _make_app_with_temp_store(tmp_dir)

        payload = {
            "system_name": "fraud_scanner",
            "original_risk": "MEDIUM",
            "corrected_risk": "HIGH",
            "justification": "Threshold too low detected by human review",
            "reviewer": "Alice Rossi",
        }

        response = client.post("/submit_feedback", json=payload)
        assert response.status_code == 200, response.text

        data = response.json()
        assert data["status"] == "ok"
        assert data["entry"]["system_name"] == payload["system_name"]
        assert data["entry"]["corrected_risk"] == payload["corrected_risk"]
        assert data["entry"]["reviewer"] == payload["reviewer"]
        assert "timestamp" in data["entry"]

        # Store should contain exactly one entry
        store_path = Path(os.environ["GROUND_TRUTH_PATH"])
        content = json.loads(store_path.read_text(encoding="utf-8"))
        assert isinstance(content, list)
        assert len(content) == 1

        # Submit a second feedback and ensure the store increments
        payload["corrected_risk"] = "LOW"
        response2 = client.post("/submit_feedback", json=payload)
        assert response2.status_code == 200, response2.text

        content2 = json.loads(store_path.read_text(encoding="utf-8"))
        assert len(content2) == 2


def test_submit_feedback_missing_reviewer_is_invalid() -> None:
    with TemporaryDirectory() as tmp_dir:
        client = _make_app_with_temp_store(tmp_dir)

        payload = {
            "system_name": "fraud_scanner",
            "original_risk": "MEDIUM",
            "corrected_risk": "HIGH",
            "justification": "Threshold too low detected by human review",
            # Missing reviewer
        }

        response = client.post("/submit_feedback", json=payload)
        assert response.status_code == 422

