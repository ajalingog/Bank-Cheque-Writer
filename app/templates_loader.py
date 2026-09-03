"""Load PCHC base layout and per-bank overlay templates."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from app.paths import templates_dir

BANKS = (
    ("landbank", "Land Bank of the Philippines"),
    ("bdo", "BDO Unibank"),
    ("bpi", "Bank of the Philippine Islands"),
    ("metrobank", "Metrobank"),
    ("pnb", "Philippine National Bank"),
    ("unionbank", "UnionBank"),
    ("securitybank", "Security Bank"),
    ("rcbc", "RCBC"),
    ("eastwest", "EastWest Bank"),
    ("chinabank", "China Bank"),
    ("dbp", "Development Bank of the Philippines"),
    ("aub", "Asia United Bank"),
    ("psbank", "PSBank"),
    ("maybank", "Maybank Philippines"),
    ("generic", "Other bank (PCHC)"),
)


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in overlay.items():
        if key in {"extends", "variants"}:
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_base() -> dict[str, Any]:
    return load_json(templates_dir() / "pchc_base.json")


def load_bank(bank_id: str, variant: str = "personal") -> dict[str, Any]:
    path = templates_dir() / f"{bank_id}.json"
    if not path.exists():
        path = templates_dir() / "generic.json"
    overlay = load_json(path)
    template = _deep_merge(load_base(), overlay)
    variant_overlay = overlay.get("variants", {}).get(variant, {})
    if variant_overlay:
        template = _deep_merge(template, variant_overlay)
    template["id"] = overlay.get("id", bank_id)
    template["variant"] = variant
    template.pop("variants", None)
    return template


def bank_choices() -> list[tuple[str, str]]:
    return list(BANKS)
