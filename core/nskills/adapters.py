"""Adapter discovery from adapters/<name>/adapter.json and adapter.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Dict, List

from .adapter import Adapter


class AdapterError(ValueError):
    pass


REQUIRED_MANIFEST_KEYS = (
    "name",
    "display_name",
    "status",
    "supports",
    "preferred_mode",
)


def load_adapters(repo_root: Path) -> Dict[str, Adapter]:
    repo_root = Path(repo_root)
    base = repo_root / "adapters"
    if not base.is_dir():
        raise AdapterError(f"{base}: missing adapters directory")
    adapters: Dict[str, Adapter] = {}
    for directory in sorted(p for p in base.iterdir() if p.is_dir()):
        manifest_path = directory / "adapter.json"
        module_path = directory / "adapter.py"
        if not manifest_path.is_file() or not module_path.is_file():
            raise AdapterError(f"{directory}: needs adapter.json and adapter.py")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AdapterError(f"{manifest_path}: invalid JSON: {exc}") from exc
        for key in REQUIRED_MANIFEST_KEYS:
            if key not in manifest:
                raise AdapterError(f"{manifest_path}: missing key {key!r}")
        name = manifest["name"]
        if name != directory.name:
            raise AdapterError(
                f"{manifest_path}: name {name!r} does not match directory {directory.name!r}"
            )
        if name in adapters:
            raise AdapterError(f"{manifest_path}: duplicate adapter {name!r}")
        module_name = "nskills_adapter_" + name.replace("-", "_")
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise AdapterError(f"{module_path}: cannot load adapter module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls = _adapter_class(module)
        if cls is None:
            raise AdapterError(f"{module_path}: no Adapter subclass")
        adapters[name] = cls(repo_root, manifest)
    if not adapters:
        raise AdapterError(f"{base}: no adapters found")
    return adapters


def _adapter_class(module) -> type | None:
    for value in vars(module).values():
        if (
            isinstance(value, type)
            and issubclass(value, Adapter)
            and value is not Adapter
            and value.__module__ == module.__name__
        ):
            return value
    return None


def target_names(adapters: Dict[str, Adapter]) -> List[str]:
    return sorted(adapters)
