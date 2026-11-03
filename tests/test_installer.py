"""Installer, state, sync, update, and doctor tests."""

from __future__ import annotations

import json
import unittest

from helpers import REPO_ROOT, adapters, temp_env

from nskills import state as state_mod
from nskills.adapter import AdapterContext
from nskills.installer import (
    InstallError,
    doctor,
    install_set,
    sync_all,
    uninstall_one,
    update_all,
)


class InstallTests(unittest.TestCase):
    def test_copy_install_and_uninstall(self):
        with temp_env() as root:
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            summary = install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            self.assertEqual(summary.ids(), ["unslop"])
            destination = root / "home" / ".agents" / "skills" / "unslop"
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertFalse(destination.is_symlink())
            data = state_mod.load_state()
            self.assertEqual(len(data["installs"]), 1)
            self.assertEqual(data["installs"][0]["mode"], "copy")

            uninstall_one(REPO_ROOT, loaded["generic"], "unslop", context)
            self.assertFalse(destination.exists())
            self.assertEqual(state_mod.load_state()["installs"], [])

    def test_symlink_install_and_uninstall(self):
        with temp_env() as root:
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT)
            install_set(REPO_ROOT, loaded["opencode"], ["unslop"], context)
            destination = root / "home" / ".config" / "opencode" / "skills" / "unslop"
            self.assertTrue(destination.is_symlink())
            self.assertEqual(destination.resolve(), (REPO_ROOT / "skills" / "unslop").resolve())
            record = state_mod.load_state()["installs"][0]
            self.assertEqual(
                record["paths"][0]["source"],
                str((REPO_ROOT / "skills" / "unslop").resolve()),
            )
            uninstall_one(REPO_ROOT, loaded["opencode"], "unslop", context)
            self.assertFalse(destination.exists())
            self.assertFalse(destination.is_symlink())

    def test_unmanaged_symlink_into_repository_is_not_overwritten(self):
        with temp_env() as root:
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            destination = root / "home" / ".agents" / "skills" / "unslop"
            destination.parent.mkdir(parents=True)
            destination.symlink_to(REPO_ROOT / "skills" / "tdd")
            with self.assertRaises(InstallError):
                install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            self.assertTrue(destination.is_symlink())
            self.assertEqual(destination.resolve(), (REPO_ROOT / "skills" / "tdd").resolve())

    def test_dependencies_are_installed_by_default(self):
        with temp_env():
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            summary = install_set(
                REPO_ROOT, loaded["generic"], ["implement-feature"], context
            )
            installed = set(summary.ids())
            self.assertIn("implement-feature", installed)
            self.assertIn("tdd", installed)
            self.assertIn("implementer", installed)
            self.assertIn("reviewer", installed)

    def test_no_deps_skips_dependencies(self):
        with temp_env():
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            summary = install_set(
                REPO_ROOT,
                loaded["generic"],
                ["implement-feature"],
                context,
                no_deps=True,
            )
            self.assertEqual(summary.ids(), ["implement-feature"])

    def test_refuses_to_overwrite_unmanaged_path(self):
        with temp_env() as root:
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            destination = root / "home" / ".agents" / "skills" / "unslop"
            destination.mkdir(parents=True)
            (destination / "mine.txt").write_text("user data\n", encoding="utf-8")
            with self.assertRaises(InstallError) as caught:
                install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            self.assertIn("not managed", str(caught.exception))
            self.assertTrue((destination / "mine.txt").is_file())

    def test_reinstall_refuses_modified_managed_path(self):
        with temp_env() as root:
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            destination = root / "home" / ".agents" / "skills" / "unslop" / "SKILL.md"
            destination.write_text("local edit\n", encoding="utf-8")
            with self.assertRaises(InstallError) as caught:
                install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            self.assertIn("modified outside nskills", str(caught.exception))
            install_set(REPO_ROOT, loaded["generic"], ["unslop"], context, force=True)
            self.assertNotEqual(
                destination.read_text(encoding="utf-8"), "local edit\n"
            )

    def test_force_backs_up_unmanaged_path(self):
        with temp_env() as root:
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            destination = root / "home" / ".agents" / "skills" / "unslop"
            destination.mkdir(parents=True)
            (destination / "mine.txt").write_text("user data\n", encoding="utf-8")
            install_set(REPO_ROOT, loaded["generic"], ["unslop"], context, force=True)
            self.assertTrue((destination / "SKILL.md").is_file())
            backups = list((root / "home" / ".local" / "state" / "nskills" / "backups").iterdir())
            self.assertTrue(backups)
            restored = list(backups[0].rglob("mine.txt"))
            self.assertEqual(len(restored), 1)
            self.assertEqual(restored[0].read_text(encoding="utf-8"), "user data\n")

    def test_unknown_capability_rejected(self):
        with temp_env():
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT)
            with self.assertRaises(InstallError):
                install_set(REPO_ROOT, loaded["generic"], ["does-not-exist"], context)

    def test_project_scope_writes_into_project(self):
        with temp_env() as root:
            loaded = adapters()
            project = root / "project"
            project.mkdir()
            context = AdapterContext(
                repo_root=REPO_ROOT, scope="project", project=project, copy=True
            )
            install_set(REPO_ROOT, loaded["opencode"], ["unslop"], context)
            self.assertTrue((project / ".opencode" / "skills" / "unslop" / "SKILL.md").is_file())


class MaintenanceTests(unittest.TestCase):
    def test_sync_restores_missing_paths(self):
        with temp_env() as root:
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            destination = root / "home" / ".agents" / "skills" / "unslop"
            self.assertTrue(destination.exists())
            for item in sorted(destination.rglob("*"), reverse=True):
                if item.is_file():
                    item.unlink()
            destination.rmdir()
            self.assertFalse(destination.exists())
            messages = sync_all(REPO_ROOT, loaded)
            self.assertTrue(any("restored" in message for message in messages))
            self.assertTrue((destination / "SKILL.md").is_file())

    def test_sync_only_restores_missing_paths(self):
        with temp_env() as root:
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            install_set(REPO_ROOT, loaded["opencode"], ["implement-feature"], context)
            skill_file = (
                root / "home" / ".config" / "opencode" / "skills"
                / "workflow-implement-feature" / "SKILL.md"
            )
            command_file = (
                root / "home" / ".config" / "opencode" / "commands"
                / "implement-feature.md"
            )
            command_file.write_text("local edit\n", encoding="utf-8")
            skill_file.unlink()
            messages = sync_all(REPO_ROOT, loaded)
            self.assertTrue(any("restored" in message for message in messages))
            self.assertTrue(skill_file.is_file())
            self.assertEqual(command_file.read_text(encoding="utf-8"), "local edit\n")

    def test_doctor_reports_missing_paths(self):
        with temp_env() as root:
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            destination = root / "home" / ".agents" / "skills" / "unslop"
            import shutil

            shutil.rmtree(destination)
            rows = doctor(REPO_ROOT, loaded)
            messages = "\n".join(message for _, message in rows)
            self.assertIn("missing", messages)

    def test_doctor_reports_drift(self):
        with temp_env():
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            summary = state_mod.load_state()["installs"][0]
            from pathlib import Path

            entry = Path(summary["paths"][0]["path"])
            target = entry / "SKILL.md"
            target.write_text(target.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")
            rows = doctor(REPO_ROOT, loaded)
            messages = "\n".join(message for _, message in rows)
            self.assertIn("changed since install", messages)

    def test_doctor_reports_source_change_for_copies(self):
        with temp_env():
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            state = state_mod.load_state()
            state["installs"][0]["hash"] = "sha256:stale"
            state_mod.save_state(state)
            rows = doctor(REPO_ROOT, loaded)
            messages = "\n".join(message for _, message in rows)
            self.assertIn("source changed since install", messages)

    def test_doctor_reports_missing_dependencies(self):
        with temp_env():
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            install_set(
                REPO_ROOT,
                loaded["generic"],
                ["implement-feature"],
                context,
                no_deps=True,
            )
            rows = doctor(REPO_ROOT, loaded)
            messages = "\n".join(message for _, message in rows)
            self.assertIn("missing skill dependency tdd", messages)
            self.assertIn("missing agent dependency reviewer", messages)

    def test_update_reinstalls_managed_capability(self):
        with temp_env():
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            messages = update_all(REPO_ROOT, loaded)
            self.assertTrue(any("->" in message for message in messages))
            self.assertEqual(
                state_mod.load_state()["installs"][0]["version"], "0.1.0"
            )

    def test_uninstall_refuses_modified_files(self):
        with temp_env():
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            from pathlib import Path

            record = state_mod.load_state()["installs"][0]
            skill_file = Path(record["paths"][0]["path"]) / "SKILL.md"
            skill_file.write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(InstallError):
                uninstall_one(REPO_ROOT, loaded["generic"], "unslop", context)
            record = uninstall_one(
                REPO_ROOT, loaded["generic"], "unslop", context, force=True
            )
            self.assertEqual(record["id"], "unslop")
            backup = Path(record["backup"])
            self.assertTrue((backup / "0-unslop" / "SKILL.md").is_file())
            self.assertEqual(
                (backup / "0-unslop" / "SKILL.md").read_text(encoding="utf-8"),
                "tampered\n",
            )

    def test_state_file_is_json(self):
        with temp_env():
            loaded = adapters()
            context = AdapterContext(repo_root=REPO_ROOT, copy=True)
            install_set(REPO_ROOT, loaded["generic"], ["unslop"], context)
            text = state_mod.state_path().read_text(encoding="utf-8")
            data = json.loads(text)
            self.assertEqual(data["schema_version"], 1)
            self.assertEqual(data["installs"][0]["id"], "unslop")


if __name__ == "__main__":
    unittest.main()
