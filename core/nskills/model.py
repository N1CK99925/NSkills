"""Canonical capability model and filesystem loading."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import frontmatter

TYPE_DIRS = {"skill": "skills", "workflow": "workflows", "agent": "agents"}
ENTRY_FILES = {"skill": "SKILL.md", "workflow": "WORKFLOW.md", "agent": "AGENT.md"}
TYPE_ORDER = {"skill": 0, "agent": 1, "workflow": 2}


class CapabilityError(ValueError):
    pass


def tree_hash(path: Path) -> str:
    """Stable hash of a file or directory tree."""
    digest = hashlib.sha256()
    if path.is_file() or (path.is_symlink() and not path.is_dir()):
        digest.update(b"file\0")
        digest.update(path.read_bytes())
        return "sha256:" + digest.hexdigest()
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = item.relative_to(path).as_posix().encode()
        digest.update(b"path\0" + rel + b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


@dataclass
class Capability:
    id: str
    type: str
    path: Path
    body: str = ""
    body_start_line: int = 0
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def entry_file(self) -> Path:
        return self.path / ENTRY_FILES[self.type]

    @property
    def name(self) -> str:
        return str(self.meta.get("name", self.id))

    @property
    def description(self) -> str:
        return str(self.meta.get("description", ""))

    @property
    def version(self) -> str:
        return str(self.meta.get("version", ""))

    @property
    def license(self) -> str:
        return str(self.meta.get("license", ""))

    @property
    def compatibility(self) -> List[str]:
        value = self.meta.get("compatibility", [])
        return list(value) if isinstance(value, list) else []

    @property
    def tags(self) -> List[str]:
        meta = self.meta.get("metadata") or {}
        nskills = meta.get("nskills") or {} if isinstance(meta, dict) else {}
        tags = nskills.get("tags", []) if isinstance(nskills, dict) else []
        return list(tags) if isinstance(tags, list) else []

    @property
    def provenance(self) -> str:
        meta = self.meta.get("metadata") or {}
        nskills = meta.get("nskills") or {} if isinstance(meta, dict) else {}
        return str(nskills.get("provenance", "")) if isinstance(nskills, dict) else ""

    @property
    def depends(self) -> Dict[str, List[str]]:
        raw = self.meta.get("depends") or {}
        result: Dict[str, List[str]] = {"skills": [], "agents": [], "tools": []}
        if isinstance(raw, dict):
            for key in result:
                value = raw.get(key, [])
                if isinstance(value, list):
                    result[key] = [str(v) for v in value]
        if self.type == "workflow":
            for key in ("skills", "agents"):
                value = self.meta.get(key, [])
                if isinstance(value, list):
                    merged = result[key] + [str(v) for v in value]
                    result[key] = list(dict.fromkeys(merged))
        return result

    @property
    def hash(self) -> str:
        return tree_hash(self.path)

    def registry_entry(self, repo_root: Path) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "path": self.path.relative_to(repo_root).as_posix(),
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "compatibility": self.compatibility,
            "depends": self.depends,
            "provenance": self.provenance,
            "tags": self.tags,
        }


def load_capability(repo_root: Path, cap_type: str, cap_id: str) -> Capability:
    directory = Path(repo_root) / TYPE_DIRS[cap_type] / cap_id
    entry = directory / ENTRY_FILES[cap_type]
    if not entry.is_file():
        raise CapabilityError(f"{entry}: missing {ENTRY_FILES[cap_type]}")
    text = entry.read_text(encoding="utf-8")
    try:
        meta, body, start = frontmatter.split(text)
    except frontmatter.FrontmatterError as exc:
        raise CapabilityError(f"{entry}: {exc}") from exc
    return Capability(
        id=cap_id,
        type=cap_type,
        path=directory,
        body=body,
        body_start_line=start,
        meta=meta,
    )


def discover(repo_root: Path) -> Dict[str, Capability]:
    """Return every capability keyed by id. Duplicate ids are returned once.

    The validator reports duplicates; discovery keeps the first in type order so
    commands still have something usable.
    """
    repo_root = Path(repo_root)
    found: Dict[str, Capability] = {}
    for cap_type in sorted(TYPE_DIRS, key=lambda t: TYPE_ORDER[t]):
        base = repo_root / TYPE_DIRS[cap_type]
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir(), key=lambda p: p.name):
            if not child.is_dir() or child.name.startswith("."):
                continue
            try:
                cap = load_capability(repo_root, cap_type, child.name)
            except CapabilityError:
                continue
            found.setdefault(cap.id, cap)
    return found


def all_capabilities(repo_root: Path) -> List[Capability]:
    """Return every capability, including duplicate ids, in stable order."""
    repo_root = Path(repo_root)
    result: List[Capability] = []
    for cap_type in sorted(TYPE_DIRS, key=lambda t: TYPE_ORDER[t]):
        base = repo_root / TYPE_DIRS[cap_type]
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir(), key=lambda p: p.name):
            if not child.is_dir() or child.name.startswith("."):
                continue
            try:
                result.append(load_capability(repo_root, cap_type, child.name))
            except CapabilityError:
                continue
    return result


def resolve_dependencies(
    repo_root: Path, roots: List[Capability]
) -> List[Capability]:
    """Return roots plus transitive skill/agent dependencies, deterministic."""
    by_id = discover(repo_root)
    ordered: List[Capability] = []
    seen: set[str] = set()

    def visit(cap: Capability, chain: List[str]) -> None:
        if cap.id in seen:
            return
        if cap.id in chain:
            raise CapabilityError(
                "dependency cycle: " + " -> ".join(chain + [cap.id])
            )
        seen.add(cap.id)
        deps = cap.depends
        for skill_id in deps["skills"]:
            dep = by_id.get(skill_id)
            if dep is None or dep.type != "skill":
                raise CapabilityError(
                    f"{cap.id}: missing skill dependency {skill_id!r}"
                )
            visit(dep, chain + [cap.id])
        for agent_id in deps["agents"]:
            dep = by_id.get(agent_id)
            if dep is None or dep.type != "agent":
                raise CapabilityError(
                    f"{cap.id}: missing agent dependency {agent_id!r}"
                )
            visit(dep, chain + [cap.id])
        ordered.append(cap)

    for root in roots:
        visit(root, [])
    ordered.sort(key=lambda c: (TYPE_ORDER[c.type], c.id))
    return ordered


def find_optional(repo_root: Path, cap_id: str) -> Optional[Capability]:
    return discover(repo_root).get(cap_id)
