"""Persistent install state.

State is a JSON file. Every path an install creates is recorded with its kind and
content hash so uninstall and doctor can prove ownership.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .adapter import xdg_state_home


SCHEMA_VERSION = 1


def state_dir() -> Path:
    override = os.environ.get("NSKILLS_STATE_DIR")
    if override:
        return Path(override).expanduser()
    return xdg_state_home() / "nskills"


def state_path() -> Path:
    return state_dir() / "state.json"


def empty_state() -> Dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "installs": []}


def load_state(path: Optional[Path] = None) -> Dict[str, Any]:
    path = path or state_path()
    if not path.is_file():
        return empty_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return empty_state()
    if not isinstance(data, dict):
        return empty_state()
    data.setdefault("schema_version", SCHEMA_VERSION)
    data.setdefault("installs", [])
    return data


def save_state(data: Dict[str, Any], path: Optional[Path] = None) -> Path:
    path = path or state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def record_key(record: Dict[str, Any]) -> tuple:
    return (
        record.get("target"),
        record.get("scope"),
        str(record.get("root")),
        record.get("type"),
        record.get("id"),
    )


def find_record(
    data: Dict[str, Any],
    cap_id: str,
    target: str,
    scope: str,
    root: Path,
) -> Optional[Dict[str, Any]]:
    for record in data.get("installs", []):
        if (
            record.get("id") == cap_id
            and record.get("target") == target
            and record.get("scope") == scope
            and Path(str(record.get("root"))) == Path(root)
        ):
            return record
    return None


def remove_record(data: Dict[str, Any], record: Dict[str, Any]) -> None:
    data["installs"] = [
        item for item in data.get("installs", []) if record_key(item) != record_key(record)
    ]


def add_record(data: Dict[str, Any], record: Dict[str, Any]) -> None:
    remove_record(data, record)
    data.setdefault("installs", []).append(record)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def records_for(
    data: Dict[str, Any],
    target: Optional[str] = None,
    cap_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    result = []
    for record in data.get("installs", []):
        if target and record.get("target") != target:
            continue
        if cap_type and record.get("type") != cap_type:
            continue
        result.append(record)
    return result
