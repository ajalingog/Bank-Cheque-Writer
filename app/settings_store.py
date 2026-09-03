"""Local settings: last bank, paper mode, and per printer+bank calibration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.paths import user_data_dir

SETTINGS_PATH = user_data_dir() / "settings.json"

DEFAULTS: dict[str, Any] = {
    "bank_id": "landbank",
    "cheque_type": "personal",
    "pad_symbols": True,
    "paper_mode": "a4",
    "feed": "top_first",
    "printer_name": "",
    "calibrations": {},
}


def _key(printer_name: str, bank_id: str, cheque_type: str = "personal") -> str:
    printer = printer_name.strip() or "default"
    return f"{printer}|{bank_id}|{cheque_type}"


def load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return dict(DEFAULTS)
    try:
        with SETTINGS_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULTS)
    merged = dict(DEFAULTS)
    merged.update(data)
    if not isinstance(merged.get("calibrations"), dict):
        merged["calibrations"] = {}
    return merged


def save_settings(data: dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def get_calibration(settings: dict[str, Any], printer_name: str, bank_id: str, cheque_type: str = "personal") -> dict[str, float]:
    stored = settings.get("calibrations", {}).get(_key(printer_name, bank_id, cheque_type), {})
    return {
        "offset_x_mm": float(stored.get("offset_x_mm", 0.0)),
        "offset_y_mm": float(stored.get("offset_y_mm", 0.0)),
        "stub_width_mm": float(stored.get("stub_width_mm", 0.0)),
    }


def set_calibration(
    settings: dict[str, Any],
    printer_name: str,
    bank_id: str,
    offset_x_mm: float,
    offset_y_mm: float,
    stub_width_mm: float,
    cheque_type: str = "personal",
) -> None:
    settings.setdefault("calibrations", {})
    settings["calibrations"][_key(printer_name, bank_id, cheque_type)] = {
        "offset_x_mm": round(offset_x_mm, 1),
        "offset_y_mm": round(offset_y_mm, 1),
        "stub_width_mm": round(stub_width_mm, 1),
    }
