"""Hermes adapter.

Verified against the local Hermes installation on 2026-11-03:
skills live under $HERMES_HOME/skills with nested categories, and workflows map
to skill bundles under $HERMES_HOME/skill-bundles. Hermes has no file-based
agent registry, so agents install as loadable instruction skills.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import List

from nskills.adapter import Action, Adapter, AdapterContext, home, render_wrapper


class HermesAdapter(Adapter):
    def detect(self) -> tuple[bool, str]:
        root = self.root(AdapterContext(repo_root=self.repo_root, scope="global"))
        binary = shutil.which("hermes")
        if root.is_dir():
            return True, f"HERMES_HOME exists: {root}"
        if binary:
            return True, f"hermes on PATH: {binary}"
        return False, "hermes not found and HERMES_HOME does not exist"

    def root(self, context: AdapterContext) -> Path:
        if context.scope == "project":
            if context.project is None:
                raise ValueError("project scope requires a project directory")
            return Path(context.project) / ".hermes"
        return Path(os.environ.get("HERMES_HOME", str(home() / ".hermes")))

    def skill_root(self, context: AdapterContext) -> Path:
        return self.root(context) / "skills" / "nskills"

    def _plan_workflow(self, cap, context: AdapterContext) -> List[Action]:
        root = self.root(context)
        if context.scope == "global":
            destination = root / "skill-bundles" / f"{cap.id}.yaml"
            return [Action("write", destination, content=render_bundle(cap), kind="file")]
        wrapper_id = f"workflow-{cap.id}"
        return [
            Action(
                "write",
                root / "skills" / "nskills" / wrapper_id / "SKILL.md",
                content=render_wrapper(cap, wrapper_id, "workflow"),
                kind="file",
            )
        ]

    def _plan_agent(self, cap, context: AdapterContext) -> List[Action]:
        wrapper_id = f"agent-{cap.id}"
        destination = self.root(context) / "skills" / "nskills" / "agents" / cap.id
        return [
            Action(
                "write",
                destination / "SKILL.md",
                content=render_wrapper(cap, wrapper_id, "agent"),
                kind="file",
            )
        ]


def render_bundle(cap) -> str:
    deps = cap.depends.get("skills", [])
    lines = [
        f"name: {json.dumps(cap.id)}",
        f"description: {json.dumps(cap.description)}",
        "skills:",
    ]
    if deps:
        for skill_id in deps:
            lines.append(f"  - {json.dumps('nskills/' + skill_id)}")
    else:
        lines[-1] = "skills: []"
    lines.append("instruction: |")
    for line in cap.body.strip().splitlines():
        lines.append(("  " + line) if line.strip() else "")
    lines.append("")
    return "\n".join(lines)
