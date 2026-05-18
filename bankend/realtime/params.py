from __future__ import annotations

import json


def merged_params(row: dict, override: dict) -> dict:
    base = json.loads(row.get("default_params") or "{}")
    if not isinstance(base, dict):
        base = {}
    return {**base, **override}
