"""Validator tests against the real repository and targeted fixtures."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT

from nskills.validator import validate_repo


GOOD_SKILL = """---
name: Sample
description: A sample skill for validator tests.
version: 0.1.0
license: MIT
compatibility: [generic]
metadata:
  nskills:
    tags: [sample]
    provenance: original
---

# Sample

Body text.
"""


def make_repo(root: Path, skill_text: str = GOOD_SKILL) -> Path:
    (root / "skills" / "sample").mkdir(parents=True)
    (root / "skills" / "sample" / "SKILL.md").write_text(skill_text, encoding="utf-8")
    (root / "workflows").mkdir()
    (root / "agents").mkdir()
    (root / "rules").mkdir()
    (root / "rules" / "global.md").write_text(
        "# Global\n\nA rule long enough to be considered useful.\n", encoding="utf-8"
    )
    (root / "registry").mkdir()
    (root / "registry" / "registry.json").write_text(
        '{"schema_version": 1, "capabilities": []}\n', encoding="utf-8"
    )
    (root / "adapters").symlink_to(REPO_ROOT / "adapters", target_is_directory=True)
    return root


class RepositoryValidationTests(unittest.TestCase):
    def test_repository_is_valid(self):
        report = validate_repo(REPO_ROOT)
        self.assertTrue(report.ok, "\n".join(report.errors))
        self.assertEqual(report.warnings, [])


class FixtureValidationTests(unittest.TestCase):
    def assert_error(self, text: str, expected: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp), text)
            report = validate_repo(root)
            self.assertFalse(report.ok)
            joined = "\n".join(report.errors)
            self.assertIn(expected, joined)

    def test_missing_required_field(self):
        text = GOOD_SKILL.replace("license: MIT\n", "")
        self.assert_error(text, "missing required frontmatter key 'license'")

    def test_bad_version(self):
        text = GOOD_SKILL.replace("version: 0.1.0", "version: 1")
        self.assert_error(text, "version must be MAJOR.MINOR.PATCH")

    def test_unknown_compatibility_target(self):
        text = GOOD_SKILL.replace("[generic]", "[generic, nowhere]")
        self.assert_error(text, "compatibility target 'nowhere' has no adapter")

    def test_missing_tag(self):
        text = GOOD_SKILL.replace("    tags: [sample]\n", "")
        self.assert_error(text, "metadata.nskills.tags must be a non-empty list")

    def test_host_tool_token_rejected(self):
        text = GOOD_SKILL + "\nRun `Read` on the file.\n"
        self.assert_error(text, "host-specific token")

    def test_model_name_rejected(self):
        text = GOOD_SKILL + "\nUse claude-sonnet for this.\n"
        self.assert_error(text, "host-specific token")

    def test_broken_link_rejected(self):
        text = GOOD_SKILL + "\nSee [missing](references/missing.md).\n"
        self.assert_error(text, "broken link")

    def test_undeclared_load_skill_rejected(self):
        text = GOOD_SKILL + "\n`load-skill` `other-skill` before starting.\n"
        self.assert_error(text, "load-skill reference 'other-skill' is not declared")

    def test_too_many_tags_rejected(self):
        tags = ", ".join(f"tag{i}" for i in range(9))
        text = GOOD_SKILL.replace("tags: [sample]", f"tags: [{tags}]")
        self.assert_error(text, "9 tags; max is 8")

    def test_link_escaping_capability_rejected(self):
        text = GOOD_SKILL + "\nSee [outside](../../outside.md).\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp), text)
            (root / "outside.md").write_text("outside\n", encoding="utf-8")
            report = validate_repo(root)
            self.assertIn(
                "link escapes the capability directory", "\n".join(report.errors)
            )

    def test_stale_registry_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp))
            report = validate_repo(root)
            self.assertIn("stale", "\n".join(report.errors))

    def test_missing_workflow_section_rejected(self):
        text = GOOD_SKILL.replace("A sample skill for validator tests.", "A sample workflow.")
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp))
            workflow = root / "workflows" / "flow"
            workflow.mkdir()
            (workflow / "WORKFLOW.md").write_text(
                "---\n"
                "name: Flow\n"
                "description: A sample workflow for validator tests.\n"
                "version: 0.1.0\n"
                "license: MIT\n"
                "compatibility: [generic]\n"
                "inputs: [x]\n"
                "outputs: [y]\n"
                "skills: []\n"
                "agents: []\n"
                "approval: []\n"
                "metadata:\n"
                "  nskills:\n"
                "    tags: [sample]\n"
                "    provenance: original\n"
                "---\n\n"
                "# Objective\n\nOnly one section.\n",
                encoding="utf-8",
            )
            report = validate_repo(root)
            self.assertIn("missing '# Steps' section", "\n".join(report.errors))


if __name__ == "__main__":
    unittest.main()
