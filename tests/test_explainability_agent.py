import json

from fastapi.testclient import TestClient

from explainability_agent.main import app


client = TestClient(app)


def test_multiple_features_contribute():
    payload = {
        "classification": "HIGH",
        "risk_score": 0.9,
        "features": {
            "amount": 3000,
            "num_prior_incidents": 2,
            "velocity": 1.0,
        },
    }
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    impact = data["impact_scores"]
    assert set(impact.keys()) == {"amount", "num_prior_incidents", "velocity"}
    # impacts sum to ~1.0
    assert abs(sum(impact.values()) - 1.0) < 1e-6
    assert "Top contributors" in data["summary"]


def test_missing_features_and_null_values():
    # Missing features entirely
    response = client.post("/explain", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["impact_scores"] == {}
    assert "No significant contributing features" in data["summary"]

    # Null and non-numeric values should be ignored and fall back to default
    response = client.post(
        "/explain",
        json={
            "features": {"amount": None, "flag": True, "desc": "abc", "zero": 0},
            "classification": "LOW",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["impact_scores"] == {}
    assert "No significant contributing features" in data["summary"]


def test_direct_features_payload_without_wrapper():
    # Direct mapping should be accepted as features
    response = client.post(
        "/explain",
        json={"f1": 1.0, "f2": -3.0, "f3": 2.0, "zero": 0},
    )
    assert response.status_code == 200
    data = response.json()
    impact = data["impact_scores"]
    assert set(impact.keys()) == {"f1", "f2", "f3"}
    assert abs(sum(impact.values()) - 1.0) < 1e-6
    # ensure ranking makes sense: |f2|=3 is top
    top_feature = list(impact.keys())[0]
    assert top_feature == "f2"

