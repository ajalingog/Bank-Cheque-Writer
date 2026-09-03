"""Resolve resource and user-data paths for source runs and frozen installs."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    """Bundled read-only assets (templates, web)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


def app_dir() -> Path:
    """Directory containing the executable (or project root in source)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def user_data_dir() -> Path:
    """Writable settings location (AppData on installed Windows builds)."""
    if is_frozen():
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        path = base / "PhilippineChequeWriter"
        path.mkdir(parents=True, exist_ok=True)
        return path
    return app_dir()


def templates_dir() -> Path:
    if is_frozen():
        return resource_root() / "templates"
    return Path(__file__).resolve().parent / "templates"


def web_dir() -> Path:
    return resource_root() / "web"
