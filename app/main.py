from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .pdf_utils import generate_pdf_from_html


class FRIARequest(BaseModel):
    system_name: str = Field(..., description="Nome del sistema")
    risk_level: str = Field(..., description="Livello di rischio")
    justification: str = Field(..., description="Giustificazione del livello di rischio")
    fairness_notes: Optional[str] = Field("", description="Note sulla fairness")
    explainability_notes: Optional[str] = Field("", description="Note sulla explainability")
    oversight_notes: Optional[str] = Field("", description="Note sulla supervisione")


def get_templates_env() -> Environment:
    templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
    loader = FileSystemLoader(templates_dir)
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


app = FastAPI(title="FRIA Generator Agent")


@app.post("/generate_fria")
def generate_fria(request: FRIARequest):
    env = get_templates_env()
    try:
        template = env.get_template("fria_report.html")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template loading failed: {e}")

    rendered_html = template.render(
        system_name=request.system_name,
        risk_level=request.risk_level,
        justification=request.justification,
        fairness_notes=request.fairness_notes or "",
        explainability_notes=request.explainability_notes or "",
        oversight_notes=request.oversight_notes or "",
        generated_at=datetime.utcnow().isoformat() + "Z",
    )

    outputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
    os.makedirs(outputs_dir, exist_ok=True)
    safe_name = "_".join(request.system_name.split())
    output_pdf_path = os.path.join(
        outputs_dir,
        f"FRIA_{safe_name}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.pdf",
    )

    success, output_path, attempts_log = generate_pdf_from_html(rendered_html, output_pdf_path)

    if not success:
        # Fallback: return JSON with path to HTML partial report and attempts log
        return JSONResponse(
            status_code=206,
            content={
                "message": "PDF generation failed, returned HTML fallback",
                "path": output_path,
                "attempts": attempts_log,
            },
        )

    # On success, stream the generated PDF
    filename = os.path.basename(output_path)
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return FileResponse(output_path, media_type="application/pdf", headers=headers)


@app.get("/health")
def health():
    return {"status": "ok"}

