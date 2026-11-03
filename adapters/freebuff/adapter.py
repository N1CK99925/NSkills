"""Freebuff adapter.

Freebuff reads the cross-tool .agents/skills convention. No native file-based
agent or command registry was found, so those capability types render as
generated skills. The adapter is marked partial because live-session loading was
not verified in the audit environment.
"""

from __future__ import annotations

import shutil

from nskills.adapter_agentskills import AgentSkillsAdapter


class FreebuffAdapter(AgentSkillsAdapter):
    def detect(self) -> tuple[bool, str]:
        binary = shutil.which("freebuff")
        if binary:
            return True, f"freebuff on PATH: {binary}"
        return False, "freebuff not found on PATH"
