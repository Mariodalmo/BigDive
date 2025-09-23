from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_high_risk_escalates():
    payload = {
        "case_id": "case-1",
        "risk_level": "high",
        "justification": "Flagged by model",
        "explanation": {"reason": "sensitive content"},
    }
    resp = client.post("/human_review", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "recheck_required"
    assert "reviewer" in data and data["reviewer"]


def test_missing_explanation_escalates():
    payload = {
        "case_id": "case-2",
        "risk_level": "medium",
        "justification": "",
        # explanation intentionally omitted
    }
    resp = client.post("/human_review", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "recheck_required"


def test_normal_case_approves():
    payload = {
        "case_id": "case-3",
        "risk_level": "low",
        "justification": "Model confident",
        "explanation": {"evidence": ["source_a", "source_b"]},
    }
    resp = client.post("/human_review", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "approved"
