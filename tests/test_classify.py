from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_biometric_high():
    payload = {
        "qualified": True,
        "has_biometric": True,
        "is_critical": False,
        "affects_rights": False,
    }
    res = client.post("/classify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "high"


def test_unqualified_excluded():
    payload = {
        "qualified": False,
        "has_biometric": False,
        "is_critical": False,
        "affects_rights": False,
    }
    res = client.post("/classify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "excluded"


def test_affects_rights_medium():
    payload = {
        "qualified": True,
        "has_biometric": False,
        "is_critical": False,
        "affects_rights": True,
    }
    res = client.post("/classify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "medium"


def test_default_low():
    payload = {
        "qualified": True,
        "has_biometric": False,
        "is_critical": False,
        "affects_rights": False,
    }
    res = client.post("/classify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "low"


def test_missing_field_returns_422():
    payload = {
        # missing 'qualified'
        "has_biometric": False,
        "is_critical": False,
        "affects_rights": False,
    }
    res = client.post("/classify", json=payload)
    assert res.status_code == 422
    detail = res.json().get("detail", [])
    # Ensure the error mentions 'qualified' missing
    assert any("qualified" in str(err.get("loc", [])) for err in detail)

