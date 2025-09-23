from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Mapping

import yaml

from .config import get_ruleset_path
from .models import ClassifyRequest


@dataclass(frozen=True)
class Rule:
    name: str
    when: Mapping[str, Any]
    risk: str
    reason: str


@lru_cache(maxsize=1)
def _load_rules() -> List[Rule]:
    rules_path = get_ruleset_path()
    with open(rules_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    rules_cfg = data.get("rules", [])
    rules: List[Rule] = []
    for entry in rules_cfg:
        rules.append(
            Rule(
                name=str(entry.get("name", "rule")),
                when=entry.get("when", {}) or {},
                risk=str(entry.get("risk")),
                reason=str(entry.get("reason", "")),
            )
        )
    if not rules:
        raise RuntimeError("No rules loaded from ruleset")
    return rules


def warmup_rules() -> None:
    _ = _load_rules()


def _matches(rule: Rule, facts: Mapping[str, Any]) -> bool:
    for key, expected_value in rule.when.items():
        if facts.get(key) != expected_value:
            return False
    return True


def classify_request(req: ClassifyRequest) -> Dict[str, str]:
    facts: Dict[str, Any] = req.model_dump()
    for rule in _load_rules():
        if _matches(rule, facts):
            return {"risk_level": rule.risk, "reason": rule.reason}
    # Fallback if no rule matches (should not happen if default rule exists)
    return {
        "risk_level": "low",
        "reason": "No explicit rule matched; defaulted to low risk",
    }

