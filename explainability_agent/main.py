from typing import Any, Dict, Optional, Tuple

from fastapi import FastAPI


app = FastAPI(title="Explainability Agent", version="1.0.0")


DEFAULT_NO_FEATURES_SUMMARY = (
    "No significant contributing features were identified. "
    "Provide numeric feature values to compute impact scores."
)


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float))


def parse_request_payload(raw_payload: Dict[str, Any]) -> Tuple[Dict[str, float], Optional[str], Optional[float]]:
    """
    Accepts flexible payloads:
    - {"features": {"f1": 1, ...}, "classification": "HIGH", "risk_score": 0.9}
    - {"f1": 1, "f2": 2}  (interpreted directly as features)
    Returns numeric, non-null, non-zero features only.
    """
    if not isinstance(raw_payload, dict):
        return {}, None, None

    candidate_features: Any = raw_payload.get("features", raw_payload)

    if not isinstance(candidate_features, dict):
        features: Dict[str, float] = {}
    else:
        features = {
            str(name): float(value)  # coerce to float for consistency
            for name, value in candidate_features.items()
            if _is_number(value) and float(value) != 0.0
        }

    classification = None
    if "classification" in raw_payload and raw_payload["classification"] is not None:
        classification = str(raw_payload["classification"])  # free-form label

    risk_score: Optional[float] = None
    if "risk_score" in raw_payload and _is_number(raw_payload["risk_score"]):
        risk_score = float(raw_payload["risk_score"])
    elif "risk" in raw_payload and _is_number(raw_payload["risk"]):
        risk_score = float(raw_payload["risk"])

    return features, classification, risk_score


def compute_impact_scores(features: Dict[str, float]) -> Dict[str, float]:
    """Simulate feature impacts by normalizing absolute values to sum to 1.0.
    Excludes zero and non-numeric features (already filtered in parsing).
    """
    if not features:
        return {}

    sum_abs = sum(abs(v) for v in features.values())
    if sum_abs == 0.0:
        return {}

    impact = {name: abs(value) / sum_abs for name, value in features.items()}
    return dict(sorted(impact.items(), key=lambda item: item[1], reverse=True))


def summarize_impacts(impact_scores: Dict[str, float], classification: Optional[str], risk_score: Optional[float]) -> str:
    if not impact_scores:
        return DEFAULT_NO_FEATURES_SUMMARY

    top_items = list(impact_scores.items())[:3]
    top_parts = [f"{name} ({score * 100:.1f}%)" for name, score in top_items]

    prefix_parts = []
    if classification is not None:
        prefix_parts.append(f"classification: {classification}")
    if risk_score is not None:
        prefix_parts.append(f"risk_score: {risk_score:.3f}")
    prefix = ("; ".join(prefix_parts) + ". ") if prefix_parts else ""

    return prefix + "Top contributors: " + ", ".join(top_parts)


@app.post("/explain")
async def explain(raw_body: Dict[str, Any]):
    features, classification, risk_score = parse_request_payload(raw_body)
    impact_scores = compute_impact_scores(features)
    summary = summarize_impacts(impact_scores, classification, risk_score)
    return {"impact_scores": impact_scores, "summary": summary}


@app.get("/health")
async def health():
    return {"status": "ok"}

