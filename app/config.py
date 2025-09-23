import os
from functools import lru_cache
from typing import Any, Dict

import yaml


DEFAULT_MANIFEST_PATH = "/workspace/manifest.yaml"


@lru_cache(maxsize=1)
def load_manifest() -> Dict[str, Any]:
    manifest_path = os.environ.get("RISK_AGENT_MANIFEST", DEFAULT_MANIFEST_PATH)
    with open(manifest_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_ruleset_path() -> str:
    manifest = load_manifest()
    ruleset_path = manifest.get("ruleset_path")
    if not ruleset_path:
        raise RuntimeError("ruleset_path missing in manifest.yaml")
    return ruleset_path


def get_ground_truth_path() -> str:
    manifest = load_manifest()
    return manifest.get("ground_truth_store", "")

