from fastapi.testclient import TestClient
import os

from app.main import app


client = TestClient(app)


def test_generate_fria_returns_file_or_fallback(tmp_path):
    payload = {
        "system_name": "Test System",
        "risk_level": "medium",
        "justification": "Valutazione iniziale basata su metriche interne.",
        "fairness_notes": "Mitigazioni pianificate.",
        "explainability_notes": "Report SHAP disponibile.",
        "oversight_notes": "Controlli umani periodici.",
    }

    response = client.post("/generate_fria", json=payload)
    assert response.status_code in (200, 206)

    if response.status_code == 200:
        # FileResponse streaming: ensure file exists from Content-Disposition filename
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment; filename=" in content_disp.lower()
        # Also verify that at least one PDF file exists under outputs/
        outputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
        if os.path.exists(outputs_dir):
            assert any(name.endswith(".pdf") for name in os.listdir(outputs_dir))
    else:
        data = response.json()
        assert data["message"].startswith("PDF generation failed")
        assert os.path.exists(data["path"])  # HTML fallback path

