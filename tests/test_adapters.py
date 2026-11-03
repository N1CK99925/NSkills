"""Adapter planning tests for all four targets."""

from __future__ import annotations

import unittest
from pathlib import Path

from helpers import REPO_ROOT, adapters, temp_env

from nskills.adapter import AdapterContext
from nskills.model import load_capability


class AdapterRootTests(unittest.TestCase):
    def test_global_roots(self):
        with temp_env() as root:
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, scope="global")
            self.assertEqual(
                loaded["opencode"].root(context),
                root / "home" / ".config" / "opencode",
            )
            self.assertEqual(loaded["hermes"].root(context), root / "hermes")
            self.assertEqual(loaded["freebuff"].root(context), root / "home" / ".agents")
            self.assertEqual(loaded["generic"].root(context), root / "home" / ".agents")

    def test_project_roots(self):
        with temp_env() as root:
            loaded = adapters()
            project = root / "project"
            project.mkdir()
            context = AdapterContext(
                repo_root=REPO_ROOT, scope="project", project=project
            )
            self.assertEqual(
                loaded["opencode"].root(context), project / ".opencode"
            )
            self.assertEqual(loaded["hermes"].root(context), project / ".hermes")
            self.assertEqual(
                loaded["generic"].root(context), project / ".agents"
            )


class AdapterPlanTests(unittest.TestCase):
    def setUp(self):
        self.loaded = adapters()
        self.skill = load_capability(REPO_ROOT, "skill", "unslop")
        self.workflow = load_capability(REPO_ROOT, "workflow", "implement-feature")
        self.agent = load_capability(REPO_ROOT, "agent", "reviewer")

    def test_opencode_skill_is_a_directory_link(self):
        with temp_env():
            context = AdapterContext(repo_root=REPO_ROOT)
            actions = self.loaded["opencode"].plan(self.skill, context)
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0].mode, "symlink")
            self.assertEqual(actions[0].destination.name, "unslop")
            self.assertEqual(actions[0].destination.parent.name, "skills")

    def test_opencode_workflow_renders_skill_and_command(self):
        with temp_env() as root:
            context = AdapterContext(repo_root=REPO_ROOT)
            actions = self.loaded["opencode"].plan(self.workflow, context)
            destinations = {action.destination for action in actions}
            self.assertIn(
                root / "home" / ".config" / "opencode" / "skills"
                / "workflow-implement-feature" / "SKILL.md",
                destinations,
            )
            self.assertIn(
                root / "home" / ".config" / "opencode" / "commands"
                / "implement-feature.md",
                destinations,
            )
            command = next(
                a.content for a in actions if a.destination.suffix == ".md"
                and a.destination.parent.name == "commands"
            )
            self.assertIn("$ARGUMENTS", command)

    def test_opencode_agent_is_a_markdown_file(self):
        with temp_env() as root:
            context = AdapterContext(repo_root=REPO_ROOT)
            actions = self.loaded["opencode"].plan(self.agent, context)
            self.assertEqual(len(actions), 1)
            self.assertEqual(
                actions[0].destination,
                root / "home" / ".config" / "opencode" / "agents" / "reviewer.md",
            )
            self.assertIn("mode: subagent", actions[0].content)
            self.assertIn("permissions:", actions[0].content)

    def test_opencode_agent_permissions_match_tools(self):
        with temp_env():
            context = AdapterContext(repo_root=REPO_ROOT)
            actions = self.loaded["opencode"].plan(self.agent, context)
            content = actions[0].content
            self.assertIn("action: edit", content)
            self.assertIn("effect: deny", content)

    def test_hermes_skill_uses_nskills_category(self):
        with temp_env() as root:
            context = AdapterContext(repo_root=REPO_ROOT)
            actions = self.loaded["hermes"].plan(self.skill, context)
            self.assertEqual(
                actions[0].destination,
                root / "hermes" / "skills" / "nskills" / "unslop",
            )

    def test_hermes_workflow_is_a_bundle(self):
        with temp_env() as root:
            context = AdapterContext(repo_root=REPO_ROOT)
            actions = self.loaded["hermes"].plan(self.workflow, context)
            self.assertEqual(len(actions), 1)
            self.assertEqual(
                actions[0].destination,
                root / "hermes" / "skill-bundles" / "implement-feature.yaml",
            )
            self.assertIn("skills:", actions[0].content)
            self.assertIn("instruction: |", actions[0].content)

    def test_agent_skills_targets_render_wrappers(self):
        with temp_env() as root:
            context = AdapterContext(repo_root=REPO_ROOT)
            for target in ("freebuff", "generic"):
                actions = self.loaded[target].plan(self.workflow, context)
                self.assertEqual(
                    actions[0].destination,
                    root / "home" / ".agents" / "skills"
                    / "workflow-implement-feature" / "SKILL.md",
                )
                self.assertIn("generated", actions[0].content)

    def test_rules_are_unsupported_everywhere(self):
        with temp_env():
            context = AdapterContext(repo_root=REPO_ROOT)
            fake = type("Fake", (), {"type": "rule", "id": "global", "path": Path(".")})
            for name, adapter in self.loaded.items():
                with self.assertRaises(ValueError):
                    adapter.plan(fake, context)


if __name__ == "__main__":
    unittest.main()
