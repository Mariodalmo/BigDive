from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_success_flow():
    case_id = "CASE-123"

    # 1) Ask to execute use_case when pending
    r = client.post(
        "/orchestrate",
        json={
            "case_id": case_id,
            "current_step": "use_case",
            "status": "pending",
            "last_result": None,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == "execute"
    assert body["next_step"] == "use_case"
    assert body["commands"][0]["name"] == "run_use_case"

    # 2) After use_case success -> risk_class execution requested
    r = client.post(
        "/orchestrate",
        json={
            "case_id": case_id,
            "current_step": "use_case",
            "status": "success",
            "last_result": {"use_case": "approved"},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == "execute"
    assert body["next_step"] == "risk_class"
    assert body["commands"][0]["name"] == "run_risk_classifier"

    # 3) After risk_class success -> FRIA execution requested
    r = client.post(
        "/orchestrate",
        json={
            "case_id": case_id,
            "current_step": "risk_class",
            "status": "success",
            "last_result": {"risk": "low"},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == "execute"
    assert body["next_step"] == "fria"
    assert body["commands"][0]["name"] == "run_fria"

    # 4) FRIA success -> finalize
    r = client.post(
        "/orchestrate",
        json={
            "case_id": case_id,
            "current_step": "fria",
            "status": "success",
            "last_result": {"fria": "ok"},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == "finalize"
    assert body["next_step"] == "complete"
    assert body["commands"][0]["name"] == "emit_case_completed"


def test_failure_with_compensation_on_risk_class():
    case_id = "CASE-FAIL-RISK"

    # use_case succeeded first
    r = client.post(
        "/orchestrate",
        json={
            "case_id": case_id,
            "current_step": "use_case",
            "status": "success",
            "last_result": {"use_case": "approved"},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["next_step"] == "risk_class"
    assert body["action"] == "execute"

    # risk_class failed -> compensation should occur on use_case and finalize
    r = client.post(
        "/orchestrate",
        json={
            "case_id": case_id,
            "current_step": "risk_class",
            "status": "failed",
            "last_result": {"error": "timeout"},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == "finalize"
    assert body["next_step"] == "complete"
    command_names = [c["name"] for c in body["commands"]]
    assert "compensate_use_case" in command_names
    assert "emit_case_failed" in command_names
    assert body["compensated"] == ["use_case"]

