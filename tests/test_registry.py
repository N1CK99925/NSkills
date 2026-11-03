"""Registry tests."""

from __future__ import annotations

import unittest

from helpers import REPO_ROOT, adapters  # noqa: F401

from nskills.model import all_capabilities, discover, resolve_dependencies
from nskills.registry import (
    build_registry,
    read_registry,
    registry_by_id,
    search_registry,
)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.data = build_registry(REPO_ROOT)
        self.by_id = registry_by_id(self.data)

    def test_every_capability_is_indexed(self):
        ids = {cap.id for cap in all_capabilities(REPO_ROOT)}
        self.assertEqual(ids, set(self.by_id))
        self.assertIn("design-before-code", self.by_id)
        self.assertIn("implement-feature", self.by_id)
        self.assertIn("reviewer", self.by_id)

    def test_registry_contains_no_bodies(self):
        for entry in self.data["capabilities"]:
            self.assertNotIn("body", entry)
            self.assertNotIn("instructions", entry)

    def test_stored_registry_matches_filesystem(self):
        stored = read_registry(REPO_ROOT)
        self.assertEqual(stored, self.data)

    def test_search_matches_id_description_and_tags(self):
        self.assertTrue(search_registry(self.data, "tdd"))
        self.assertTrue(search_registry(self.data, "verification"))
        self.assertTrue(search_registry(self.data, "writing"))
        self.assertEqual(search_registry(self.data, "zzz-not-a-skill"), [])

    def test_types_are_known(self):
        types = {entry["type"] for entry in self.data["capabilities"]}
        self.assertEqual(types, {"skill", "workflow", "agent"})

    def test_workflow_dependencies_resolve(self):
        workflow = discover(REPO_ROOT)["implement-feature"]
        resolved = resolve_dependencies(REPO_ROOT, [workflow])
        ids = [cap.id for cap in resolved]
        for skill in workflow.depends["skills"]:
            self.assertIn(skill, ids)
        for agent in workflow.depends["agents"]:
            self.assertIn(agent, ids)

    def test_provenance_is_recorded_for_every_capability(self):
        for entry in self.data["capabilities"]:
            self.assertTrue(entry["provenance"], entry["id"])


if __name__ == "__main__":
    unittest.main()
