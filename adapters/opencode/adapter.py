"""OpenCode adapter.

Verified against the OpenCode V2 documentation on 2026-11-03:
skills are directories under a `skills` root, agents are markdown files under
`agents`, and commands are markdown files under `commands`.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import List

from nskills.adapter import Action, Adapter, AdapterContext, render_wrapper, xdg_config_home


class OpenCodeAdapter(Adapter):
    def detect(self) -> tuple[bool, str]:
        config = xdg_config_home() / "opencode"
        binary = shutil.which("opencode")
        if binary:
            return True, f"opencode on PATH: {binary}"
        if config.is_dir():
            return True, f"config directory exists: {config}"
        return False, "opencode not found and no config directory"

    def root(self, context: AdapterContext) -> Path:
        if context.scope == "project":
            if context.project is None:
                raise ValueError("project scope requires a project directory")
            return Path(context.project) / ".opencode"
        return xdg_config_home() / "opencode"

    def _plan_workflow(self, cap, context: AdapterContext) -> List[Action]:
        wrapper_id = f"workflow-{cap.id}"
        root = self.root(context)
        return [
            Action(
                "write",
                root / "skills" / wrapper_id / "SKILL.md",
                content=render_wrapper(cap, wrapper_id, "workflow"),
                kind="file",
            ),
            Action(
                "write",
                root / "commands" / f"{cap.id}.md",
                content=render_command(cap, wrapper_id),
                kind="file",
            ),
        ]

    def _plan_agent(self, cap, context: AdapterContext) -> List[Action]:
        destination = self.root(context) / "agents" / f"{cap.id}.md"
        return [Action("write", destination, content=render_agent(cap), kind="file")]


def render_agent(cap) -> str:
    tools = set(cap.meta.get("tools") or [])
    mode = str(cap.meta.get("mode") or "subagent")
    lines = [
        "---",
        f"description: {json.dumps(cap.description)}",
        f"mode: {mode}",
    ]
    permissions = []
    if "edit" not in tools:
        permissions.append(("edit", "*", "deny"))
    if "shell" not in tools:
        permissions.append(("shell", "*", "deny"))
    if permissions:
        lines.append("permissions:")
        for action, resource, effect in permissions:
            lines.append(f"  - action: {action}")
            lines.append(f"    resource: {json.dumps(resource)}")
            lines.append(f"    effect: {effect}")
    lines.append("---")
    lines.append("")
    lines.append(cap.body.strip())
    lines.append("")
    return "\n".join(lines)


def render_command(cap, wrapper_id: str) -> str:
    return (
        "---\n"
        f"description: {json.dumps(cap.description)}\n"
        "---\n\n"
        f"Load the `{wrapper_id}` skill and follow it for this request.\n\n"
        "$ARGUMENTS\n"
    )
