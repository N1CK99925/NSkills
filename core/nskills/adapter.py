"""Shared adapter contract and rendering helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .model import Capability, content_hash


@dataclass
class Action:
    mode: str  # symlink | copy-tree | write
    destination: Path
    source: Optional[Path] = None
    content: Optional[str] = None
    kind: str = "dir"  # dir | file

    def hash(self) -> str:
        if self.mode == "write":
            return content_hash(self.content or "")
        if self.source is None:
            raise ValueError("action has no source")
        from .model import tree_hash

        return tree_hash(self.source)


@dataclass
class AdapterContext:
    repo_root: Path
    scope: str = "global"
    project: Optional[Path] = None
    copy: bool = False


class Adapter:
    name = "base"
    display_name = "Base"
    supports_types: set[str] = set()

    def __init__(self, repo_root: Path, manifest: Dict[str, Any]):
        self.repo_root = Path(repo_root)
        self.manifest = manifest
        self.name = str(manifest.get("name", self.name))
        self.display_name = str(manifest.get("display_name", self.display_name))
        self.supports_types = {
            key
            for key, value in (manifest.get("supports") or {}).items()
            if value
        }
        self.verified_at = str(manifest.get("verified_at", ""))
        self.status = str(manifest.get("status", "unknown"))
        self.notes = list(manifest.get("notes") or [])
        self.documentation = str(manifest.get("documentation", ""))

    # -- capability support -------------------------------------------------

    def supports(self, cap_type: str) -> bool:
        return cap_type in self.supports_types

    def unsupported_reason(self, cap_type: str) -> str:
        return (
            f"{self.display_name} does not support {cap_type} installs; "
            "the adapter manifest marks it unsupported"
        )

    # -- roots --------------------------------------------------------------

    def detect(self) -> tuple[bool, str]:
        return True, "always available"

    def root(self, context: AdapterContext) -> Path:
        raise NotImplementedError

    def skill_root(self, context: AdapterContext) -> Path:
        return self.root(context) / "skills"

    # -- planning -----------------------------------------------------------

    def plan(self, cap: Capability, context: AdapterContext) -> List[Action]:
        if not self.supports(cap.type):
            raise ValueError(self.unsupported_reason(cap.type))
        if cap.type == "skill":
            return [
                self._install_tree(
                    cap.path, self.skill_root(context) / cap.id, context
                )
            ]
        if cap.type == "workflow":
            return self._plan_workflow(cap, context)
        if cap.type == "agent":
            return self._plan_agent(cap, context)
        raise ValueError(f"{self.name}: unsupported capability type {cap.type!r}")

    def _install_tree(self, source: Path, destination: Path, context: AdapterContext) -> Action:
        if context.copy:
            return Action("copy-tree", destination, source=source, kind="dir")
        return Action("symlink", destination, source=source, kind="dir")

    def _plan_workflow(self, cap: Capability, context: AdapterContext) -> List[Action]:
        wrapper_id = f"workflow-{cap.id}"
        destination = self.skill_root(context) / wrapper_id
        return [
            Action(
                "write",
                destination / "SKILL.md",
                content=render_wrapper(cap, wrapper_id, "workflow"),
                kind="file",
            )
        ]

    def _plan_agent(self, cap: Capability, context: AdapterContext) -> List[Action]:
        wrapper_id = f"agent-{cap.id}"
        destination = self.skill_root(context) / wrapper_id
        return [
            Action(
                "write",
                destination / "SKILL.md",
                content=render_wrapper(cap, wrapper_id, "agent"),
                kind="file",
            )
        ]


def render_wrapper(cap: Capability, wrapper_id: str, kind: str) -> str:
    """Render a canonical workflow or agent as an Agent Skills entry point."""
    provenance = cap.provenance or "original"
    return (
        "---\n"
        f"name: {json.dumps(wrapper_id)}\n"
        f"description: {json.dumps(cap.description)}\n"
        f"version: {json.dumps(cap.version)}\n"
        f"license: {json.dumps(cap.license)}\n"
        "metadata:\n"
        "  nskills:\n"
        f"    provenance: {json.dumps(provenance)}\n"
        f"    generated: {json.dumps(kind)}\n"
        "---\n\n"
        f"# {cap.name}\n\n"
        f"This is a generated Agent Skills entry point for the NSkills {kind} "
        f"`{cap.id}`.\n\n"
        f"Canonical source: `{kind}s/{cap.id}`.\n\n"
        f"{cap.body.strip()}\n"
    )


def home() -> Path:
    return Path(os.environ.get("HOME", str(Path.home())))


def xdg_config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", str(home() / ".config")))


def xdg_state_home() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME", str(home() / ".local" / "state")))
