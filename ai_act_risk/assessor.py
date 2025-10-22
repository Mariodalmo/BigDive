from __future__ import annotations

from typing import List, Set

from .models import (
    AssessmentInput,
    AssessmentResult,
    FRIAResult,
    LifecycleRisks,
    RiskCategory,
    MitigationMeasure,
    MitigationType,
    ImpactArea,
)


_ANNEX_III_KEYWORDS: Set[str] = {
    "recruitment",
    "hiring",
    "employment",
    "credit",
    "credit_scoring",
    "medical",
    "diagnosis",
    "education",
    "student",
    "critical_infrastructure",
    "biometric",
    "law_enforcement",
    "border",
    "migration",
    "asylum",
    "justice",
}

_UNACCEPTABLE_KEYWORDS: Set[str] = {
    "social_scoring",
    "subliminal",
    "manipulation",
}

_AI_TECH_KEYWORDS: Set[str] = {
    "ml",
    "machine learning",
    "deep learning",
    "neural",
    "transformer",
    "llm",
    "nlp",
    "bayesian",
    "expert system",
    "symbolic",
    "statistical",
}


def _text_matches_any(texts: List[str], patterns: Set[str]) -> bool:
    joined = " ".join((t or "") for t in texts).lower()
    return any(p in joined for p in patterns)


def _derive_fria_overall(entries: List) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    level = 0
    for e in entries:
        level = max(level, order.get(e.risk_level, 1))
    return {0: "low", 1: "medium", 2: "high"}[level]


def _build_lifecycle_risks(inp: AssessmentInput) -> LifecycleRisks:
    risks = LifecycleRisks()

    if not inp.control_context.dataset_profile.representative:
        risks.training.append("Dataset representativeness uncertain; potential performance disparity across subgroups.")
    if not inp.control_context.dataset_profile.bias_evaluated:
        risks.validation.append("Bias and fairness not evaluated; potential discriminatory outcomes.")
    if inp.control_context.dataset_profile.pii_present:
        risks.design.append("Personal data processed; GDPR alignment and DPIA may be required.")
    if not inp.control_context.logging:
        risks.deployment.append("Insufficient logging for traceability and incident investigation.")
    if inp.system.autonomous_decision_making and inp.control_context.human_oversight == "none":
        risks.deployment.append("Lack of human oversight for automated decisions.")
    if not inp.control_context.xai_available:
        risks.validation.append("Limited explainability impairs contestability and auditability.")

    # Always include post-market monitoring reminder
    risks.post_market.append("Model drift and data shifts may degrade performance over time.")

    return risks


def _baseline_measures(inp: AssessmentInput, category: RiskCategory) -> List[MitigationMeasure]:
    measures: List[MitigationMeasure] = []

    if not inp.control_context.dataset_profile.bias_evaluated:
        measures.append(
            MitigationMeasure(
                type=MitigationType.TECHNICAL,
                name="Conduct bias and fairness evaluation",
                description="Assess disparate impact across protected attributes; document metrics and remediation.",
                references=["AI Act Art. 10", "ISO/IEC 23894"],
            )
        )
    if not inp.control_context.dataset_profile.representative:
        measures.append(
            MitigationMeasure(
                type=MitigationType.TECHNICAL,
                name="Improve dataset representativeness",
                description="Augment datasets to cover relevant demographics and contexts; document provenance.",
                references=["AI Act Art. 10"],
            )
        )
    if not inp.control_context.logging:
        measures.append(
            MitigationMeasure(
                type=MitigationType.ORGANIZATIONAL,
                name="Enable comprehensive logging",
                description="Record key events, inputs, outputs, and overrides for traceability and audits.",
                references=["AI Act Art. 12"],
            )
        )
    if inp.system.autonomous_decision_making and inp.control_context.human_oversight in {"none", "post_hoc"}:
        measures.append(
            MitigationMeasure(
                type=MitigationType.PROCEDURAL,
                name="Introduce human-in-the-loop controls",
                description="Require human approval or continuous supervision for impactful decisions.",
                references=["AI Act Art. 14"],
            )
        )
    if not inp.control_context.xai_available:
        measures.append(
            MitigationMeasure(
                type=MitigationType.TECHNICAL,
                name="Provide explainability mechanisms",
                description="Implement model explainability and user-facing rationale for decisions.",
                references=["AI Act Recitals", "NIST AI RMF"],
            )
        )

    if category == RiskCategory.HIGH:
        measures.append(
            MitigationMeasure(
                type=MitigationType.ORGANIZATIONAL,
                name="Establish risk management system",
                description="Documented, continuous process covering identification, analysis, mitigation, and monitoring.",
                references=["AI Act Art. 9"],
            )
        )
        measures.append(
            MitigationMeasure(
                type=MitigationType.ORGANIZATIONAL,
                name="Maintain technical documentation",
                description="Comprehensive documentation of system, datasets, tests, and controls.",
                references=["AI Act Art. 11"],
            )
        )

    return measures


def _compliance_requirements(category: RiskCategory) -> List[str]:
    if category == RiskCategory.HIGH:
        return [
            "Risk management system (Art. 9)",
            "Data governance and management (Art. 10)",
            "Technical documentation (Art. 11)",
            "Record-keeping and logging (Art. 12)",
            "Transparency to users (Art. 13)",
            "Human oversight (Art. 14)",
            "Accuracy, robustness, cybersecurity (Art. 15)",
            "Quality management system (Art. 17)",
            "Conformity assessment (ex-ante)",
            "CE marking and declaration of conformity",
            "Registration in EU high-risk database",
        ]
    if category == RiskCategory.UNACCEPTABLE:
        return [
            "Prohibited practice under AI Act; system must not be placed on the market.",
        ]
    return [
        "Provide appropriate transparency",
        "Mitigate foreseeable risks and document controls",
        "Inform users about AI interaction",
    ]


class AIAssessor:
    def assess(self, inp: AssessmentInput) -> AssessmentResult:
        sys = inp.system

        identified_as_ai = _text_matches_any(sys.techniques, _AI_TECH_KEYWORDS) or _text_matches_any(
            [sys.overview] + sys.use_cases + [sys.domain], _AI_TECH_KEYWORDS
        )

        unacceptable = _text_matches_any([sys.domain] + sys.use_cases, _UNACCEPTABLE_KEYWORDS)
        if unacceptable:
            category = RiskCategory.UNACCEPTABLE
            reason = "Detected prohibited practice keywords (e.g., social scoring/manipulation)."
        else:
            high_risk = _text_matches_any([sys.domain] + sys.use_cases, _ANNEX_III_KEYWORDS)
            if high_risk:
                category = RiskCategory.HIGH
                reason = "Domain and/or use case matches Annex III high-risk areas."
            else:
                limited = sys.human_in_the_loop and not sys.autonomous_decision_making
                if limited:
                    category = RiskCategory.LIMITED
                    reason = "Human-in-the-loop with limited autonomy; lower impact surface."
                else:
                    category = RiskCategory.MINIMAL
                    reason = "No Annex III match and minimal autonomy indicated."

        fria_overall = _derive_fria_overall(inp.fria)
        lifecycle = _build_lifecycle_risks(inp)
        measures = _baseline_measures(inp, category)
        compliance = _compliance_requirements(category)
        registration = category == RiskCategory.HIGH

        fria_result = FRIAResult(entries=inp.fria, overall_risk=fria_overall)

        return AssessmentResult(
            system_identified_as_ai=identified_as_ai,
            category=category,
            category_reasoning=reason,
            fria=fria_result,
            lifecycle_risks=lifecycle,
            recommended_measures=measures + inp.additional_controls,
            compliance_requirements=compliance,
            registration_required=registration,
        )
