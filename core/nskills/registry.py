"""Registry construction and loading.

The registry indexes capabilities. It never stores instruction bodies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .model import TYPE_ORDER, all_capabilities

REGISTRY_PATH = Path("registry") / "registry.json"


def build_registry(repo_root: Path) -> Dict[str, Any]:
    repo_root = Path(repo_root)
    caps = all_capabilities(repo_root)
    caps.sort(key=lambda c: (TYPE_ORDER[c.type], c.id))
    return {
        "schema_version": 1,
        "capabilities": [cap.registry_entry(repo_root) for cap in caps],
    }


def read_registry(repo_root: Path) -> Dict[str, Any]:
    path = Path(repo_root) / REGISTRY_PATH
    if not path.is_file():
        return {"schema_version": 1, "capabilities": []}
    return json.loads(path.read_text(encoding="utf-8"))


def write_registry(repo_root: Path, data: Dict[str, Any] | None = None) -> Path:
    repo_root = Path(repo_root)
    data = data if data is not None else build_registry(repo_root)
    path = repo_root / REGISTRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


def registry_by_id(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for entry in data.get("capabilities", []):
        result.setdefault(entry["id"], entry)
    return result


def search_registry(data: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    needle = query.lower().strip()
    if not needle:
        return list(data.get("capabilities", []))
    matches = []
    for entry in data.get("capabilities", []):
        haystack = " ".join(
            [
                entry.get("id", ""),
                entry.get("name", ""),
                entry.get("description", ""),
                " ".join(entry.get("tags", [])),
                entry.get("type", ""),
            ]
        ).lower()
        if needle in haystack:
            matches.append(entry)
    return matches


def capability_types(data: Dict[str, Any]) -> List[str]:
    return sorted({entry["type"] for entry in data.get("capabilities", [])})
