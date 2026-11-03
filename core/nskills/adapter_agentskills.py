"""Adapters for targets that read the cross-tool Agent Skills convention."""

from __future__ import annotations

from pathlib import Path

from .adapter import Adapter, AdapterContext, home


class AgentSkillsAdapter(Adapter):
    """Global root is ~/.agents, project root is <project>/.agents."""

    def root(self, context: AdapterContext) -> Path:
        if context.scope == "project":
            if context.project is None:
                raise ValueError("project scope requires a project directory")
            return Path(context.project) / ".agents"
        return home() / ".agents"
