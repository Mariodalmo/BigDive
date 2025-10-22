from __future__ import annotations

from typing import List
from datetime import datetime

from .models import AssessmentInput, AssessmentResult, MitigationMeasure


def _format_measures(measures: List[MitigationMeasure]) -> str:
    if not measures:
        return "- No additional measures recommended."
    lines = []
    for m in measures:
        refs = f" (ref: {', '.join(m.references)})" if m.references else ""
        desc = f": {m.description}" if m.description else ""
        lines.append(f"- {m.type.value.upper()}: {m.name}{desc}{refs}")
    return "\n".join(lines)


class MarkdownReportGenerator:
    def generate(self, inp: AssessmentInput, res: AssessmentResult) -> str:
        sys = inp.system
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

        fria_lines = [f"- {e.area.value.replace('_', ' ').title()}: {e.risk_level}" + (f" — {e.notes}" if e.notes else "") for e in res.fria.entries]
        fria_block = "\n".join(fria_lines) if fria_lines else "- Not provided"

        lifecycle_sections = []
        if res.lifecycle_risks.design:
            lifecycle_sections.append("- Design: " + "; ".join(res.lifecycle_risks.design))
        if res.lifecycle_risks.training:
            lifecycle_sections.append("- Training: " + "; ".join(res.lifecycle_risks.training))
        if res.lifecycle_risks.validation:
            lifecycle_sections.append("- Validation: " + "; ".join(res.lifecycle_risks.validation))
        if res.lifecycle_risks.deployment:
            lifecycle_sections.append("- Deployment: " + "; ".join(res.lifecycle_risks.deployment))
        if res.lifecycle_risks.post_market:
            lifecycle_sections.append("- Post-market: " + "; ".join(res.lifecycle_risks.post_market))
        lifecycle_block = "\n".join(lifecycle_sections) if lifecycle_sections else "- Not identified"

        measures_block = _format_measures(res.recommended_measures)
        compliance_block = "\n".join(f"- {item}" for item in res.compliance_requirements) if res.compliance_requirements else "- None"

        registration_text = "Yes" if res.registration_required else "No"

        md = f"""
### AI Act Risk Assessment Report

- Generated at: {now}
- System: {sys.name}
- Identified as AI: {str(res.system_identified_as_ai)}

### 1. Identificazione del sistema di IA
{sys.overview}

- Techniques: {', '.join(sys.techniques)}
- Domain: {sys.domain}
- Use cases: {', '.join(sys.use_cases)}
- Inputs: {', '.join(sys.inputs)}
- Outputs: {', '.join(sys.outputs)}
- Human-in-the-loop: {sys.human_in_the_loop}
- Autonomous decision making: {sys.autonomous_decision_making}

### 2. Classificazione del rischio
- Category: {res.category.value.upper()}
- Reasoning: {res.category_reasoning}

### 3. Valutazione dell'impatto sui diritti fondamentali (FRIA)
- Overall: {res.fria.overall_risk.upper()}
{fria_block}

### 4. Analisi del ciclo di vita del rischio
{lifecycle_block}

### 5. Adozione di misure di mitigazione
{measures_block}

### 6. Documentazione tecnica
- Provide a Technical Documentation Pack including: system description, architecture, datasets, security measures, risk evaluation, test and validation results. (AI Act Art. 11)

### 7. Sistema di gestione del rischio continuo
- Establish continuous monitoring, anomaly detection, and periodic reviews. Configure alerts for unexpected behaviors. Document retraining and change management.

### 8. Valutazione della conformità (ex-ante)
{compliance_block}

### 9. Registrazione nel database europeo
- Required: {registration_text}

---

References: AI Act (Reg. UE 2024/1689), NIST AI RMF, ISO/IEC 23894.
""".strip()

        return md
