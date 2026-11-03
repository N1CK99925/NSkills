"""Install, uninstall, sync, update, and health checks."""

from __future__ import annotations

import copy
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import state as state_mod
from .adapter import Action, Adapter, AdapterContext, xdg_state_home
from .model import Capability, content_hash, discover, resolve_dependencies, tree_hash
from .registry import read_registry, registry_by_id


class InstallError(RuntimeError):
    pass


@dataclass
class InstallSummary:
    target: str
    records: List[Dict[str, Any]]
    warnings: List[str]

    def ids(self) -> List[str]:
        return [record["id"] for record in self.records]


def _backup_root() -> Path:
    return state_mod.state_dir() / "backups"


def _unique_backup_dir(prefix: str = "install-") -> Path:
    _backup_root().mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=_backup_root()))


def _move_to_backup(path: Path, backup_dir: Path, index: int) -> Path:
    target = backup_dir / f"{index}-{path.name}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(target))
    return target


def _restore_backups(mapping: List[Tuple[Path, Path]]) -> None:
    for original, backup in reversed(mapping):
        if backup.exists() or backup.is_symlink():
            original.parent.mkdir(parents=True, exist_ok=True)
            if original.exists() or original.is_symlink():
                _remove_path(original)
            shutil.move(str(backup), str(original))


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _prune_empty(path: Path, stop: Path) -> None:
    current = path
    stop = stop.resolve()
    while current != stop and stop in current.resolve().parents:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def _managed_path(record: Dict[str, Any], path: Path, repo_root: Path) -> bool:
    entries = {str(item.get("path")): item for item in record.get("paths", [])}
    entry = entries.get(str(path))
    if entry is None:
        return False
    if not (path.exists() or path.is_symlink()):
        return True
    if path.is_symlink():
        try:
            target = path.resolve()
        except OSError:
            return False
        expected = entry.get("source")
        if expected:
            try:
                return target == Path(str(expected)).resolve()
            except OSError:
                return False
        return repo_root.resolve() in target.parents or target == repo_root.resolve()
    expected = entry.get("hash")
    if not expected:
        return True
    try:
        if entry.get("kind") == "file" and path.is_file() and not path.is_symlink():
            return content_hash(path.read_text(encoding="utf-8")) == expected
        return tree_hash(path) == expected
    except OSError:
        return False


def _preflight(
    actions: List[Action],
    force: bool,
    managed_paths: set[Path],
) -> List[Path]:
    seen: Dict[Path, Action] = {}
    for action in actions:
        destination = action.destination
        if destination in seen:
            raise InstallError(f"two actions write the same path: {destination}")
        seen[destination] = action
    conflicts = []
    for path in seen:
        if path.exists() or path.is_symlink():
            if path in managed_paths:
                continue
            if force:
                continue
            conflicts.append(path)
    if conflicts:
        listing = "\n".join(f"  {p}" for p in conflicts)
        raise InstallError(
            "destination exists and is not managed by nskills (use --force to back it up):\n"
            + listing
        )
    return conflicts


def install_set(
    repo_root: Path,
    adapter: Adapter,
    ids: Iterable[str],
    context: AdapterContext,
    force: bool = False,
    no_deps: bool = False,
) -> InstallSummary:
    repo_root = Path(repo_root)
    by_id = discover(repo_root)
    roots: List[Capability] = []
    missing = []
    for cap_id in ids:
        cap = by_id.get(cap_id)
        if cap is None:
            missing.append(cap_id)
            continue
        roots.append(cap)
    if missing:
        raise InstallError("unknown capability: " + ", ".join(sorted(missing)))
    for cap in roots:
        if not adapter.supports(cap.type):
            raise InstallError(f"{cap.id}: {adapter.unsupported_reason(cap.type)}")

    if no_deps:
        caps = sorted(roots, key=lambda c: ({"skill": 0, "agent": 1, "workflow": 2}[c.type], c.id))
    else:
        caps = resolve_dependencies(repo_root, roots)
    for cap in caps:
        if not adapter.supports(cap.type):
            raise InstallError(f"{cap.id}: {adapter.unsupported_reason(cap.type)}")

    root = adapter.root(context)
    plans: List[Tuple[Capability, List[Action]]] = []
    all_actions: List[Action] = []
    for cap in caps:
        actions = adapter.plan(cap, context)
        plans.append((cap, actions))
        all_actions.extend(actions)

    state = state_mod.load_state()
    managed: Dict[Path, Dict[str, Any]] = {}
    for existing in state.get("installs", []):
        if (
            existing.get("target") == adapter.name
            and existing.get("scope") == context.scope
            and Path(str(existing.get("root"))) == root
        ):
            for item in existing.get("paths", []):
                managed[Path(item["path"])] = existing
    _preflight(all_actions, force, set(managed))

    modified = [
        action.destination
        for action in all_actions
        if action.destination in managed
        and (action.destination.exists() or action.destination.is_symlink())
        and not _managed_path(managed[action.destination], action.destination, repo_root)
    ]
    if modified and not force:
        listing = "\n".join(f"  {p}" for p in modified)
        raise InstallError(
            "refusing to overwrite paths modified outside nskills "
            "(use --force to back them up):\n" + listing
        )

    old_state = copy.deepcopy(state)
    backup_dir = _unique_backup_dir()
    backups: List[Tuple[Path, Path]] = []
    created: List[Path] = []
    installed_records: List[Dict[str, Any]] = []

    def backup(path: Path) -> None:
        if path.exists() or path.is_symlink():
            backups.append((path, _move_to_backup(path, backup_dir, len(backups))))

    try:
        for cap in caps:
            record = state_mod.find_record(state, cap.id, adapter.name, context.scope, root)
            if record:
                for item in record.get("paths", []):
                    backup(Path(item["path"]))
                state_mod.remove_record(state, record)

        for cap, actions in plans:
            for action in actions:
                destination = action.destination
                if destination.exists() or destination.is_symlink():
                    backup(destination)
                destination.parent.mkdir(parents=True, exist_ok=True)
                if action.mode == "symlink":
                    if action.source is None:
                        raise InstallError(f"{cap.id}: symlink action has no source")
                    os.symlink(action.source.resolve(), destination, target_is_directory=action.kind == "dir")
                elif action.mode == "copy-tree":
                    if action.source is None:
                        raise InstallError(f"{cap.id}: copy action has no source")
                    shutil.copytree(action.source, destination)
                elif action.mode == "write":
                    destination.write_text(action.content or "", encoding="utf-8")
                else:
                    raise InstallError(f"{cap.id}: unknown action mode {action.mode!r}")
                created.append(destination)

            record = {
                "id": cap.id,
                "type": cap.type,
                "target": adapter.name,
                "scope": context.scope,
                "root": str(root),
                "version": cap.version,
                "hash": cap.hash,
                "mode": (
                    "symlink"
                    if any(action.mode == "symlink" for action in actions)
                    else "copy"
                ),
                "paths": [
                    {
                        "path": str(action.destination),
                        "kind": action.kind,
                        "hash": action.hash(),
                        "source": (
                            str(action.source.resolve()) if action.source else None
                        ),
                    }
                    for action in actions
                ],
                "dependencies": cap.depends,
                "installed_at": state_mod.now_iso(),
            }
            state_mod.add_record(state, record)
            installed_records.append(record)
        state_mod.save_state(state)
    except Exception as exc:
        for path in reversed(created):
            try:
                if path.exists() or path.is_symlink():
                    _remove_path(path)
            except OSError:
                pass
        _restore_backups(backups)
        try:
            state_mod.save_state(old_state)
        except OSError:
            pass
        if isinstance(exc, InstallError):
            shutil.rmtree(backup_dir, ignore_errors=True)
            raise
        shutil.rmtree(backup_dir, ignore_errors=True)
        raise InstallError(f"install failed: {exc}") from exc

    warnings = []
    for cap in caps:
        tools = cap.depends.get("tools", [])
        for tool in tools:
            if shutil.which(tool) is None:
                warnings.append(f"{cap.id}: required tool not found on PATH: {tool}")
    if not (force and backups):
        shutil.rmtree(backup_dir, ignore_errors=True)
    return InstallSummary(adapter.name, installed_records, warnings)


def uninstall_one(
    repo_root: Path,
    adapter: Adapter,
    cap_id: str,
    context: AdapterContext,
    force: bool = False,
) -> Dict[str, Any]:
    repo_root = Path(repo_root)
    root = adapter.root(context)
    state = state_mod.load_state()
    record = state_mod.find_record(state, cap_id, adapter.name, context.scope, root)
    if record is None:
        raise InstallError(
            f"{cap_id} is not installed for {adapter.name} ({context.scope}, {root})"
        )
    modified = []
    for item in record.get("paths", []):
        path = Path(item["path"])
        if not (path.exists() or path.is_symlink()):
            continue
        if not _managed_path(record, path, repo_root):
            modified.append(path)
    if modified and not force:
        listing = "\n".join(f"  {p}" for p in modified)
        raise InstallError(
            "refusing to remove paths modified outside nskills (use --force):\n" + listing
        )
    backup_dir = _unique_backup_dir("uninstall-")
    backups: List[Tuple[Path, Path]] = []
    try:
        for item in record.get("paths", []):
            path = Path(item["path"])
            if path.exists() or path.is_symlink():
                backups.append((path, _move_to_backup(path, backup_dir, len(backups))))
        state_mod.remove_record(state, record)
        state_mod.save_state(state)
    except Exception:
        _restore_backups(backups)
        shutil.rmtree(backup_dir, ignore_errors=True)
        raise
    if modified and force:
        record["backup"] = str(backup_dir)
    else:
        shutil.rmtree(backup_dir, ignore_errors=True)
    for item in record.get("paths", []):
        _prune_empty(Path(item["path"]).parent, root)
    return record


def _restore_missing(actions: List[Action]) -> List[Action]:
    """Create only destinations that are absent. Returns the restored actions."""
    restored: List[Action] = []
    try:
        for action in actions:
            destination = action.destination
            if destination.is_symlink() and not destination.exists():
                if action.mode == "symlink" and action.source is not None:
                    try:
                        same_source = destination.resolve() == action.source.resolve()
                    except OSError:
                        same_source = False
                    if same_source:
                        destination.unlink()
                    else:
                        raise InstallError(
                            f"cannot restore {destination}: broken symlink was not "
                            "created by nskills"
                        )
                else:
                    raise InstallError(
                        f"cannot restore {destination}: broken symlink is in the way"
                    )
            if destination.exists() or destination.is_symlink():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if action.mode == "symlink":
                if action.source is None or not action.source.exists():
                    raise InstallError(
                        f"cannot restore {destination}: source is missing: {action.source}"
                    )
                os.symlink(
                    action.source.resolve(),
                    destination,
                    target_is_directory=action.kind == "dir",
                )
            elif action.mode == "copy-tree":
                if action.source is None or not action.source.is_dir():
                    raise InstallError(
                        f"cannot restore {destination}: source is missing: {action.source}"
                    )
                shutil.copytree(action.source, destination)
            elif action.mode == "write":
                destination.write_text(action.content or "", encoding="utf-8")
            else:
                raise InstallError(f"unknown action mode {action.mode!r}")
            restored.append(action)
    except Exception:
        for action in reversed(restored):
            try:
                if action.destination.exists() or action.destination.is_symlink():
                    _remove_path(action.destination)
            except OSError:
                pass
        raise
    return restored


def sync_all(
    repo_root: Path,
    adapters: Dict[str, Adapter],
    target: Optional[str] = None,
) -> List[str]:
    repo_root = Path(repo_root)
    state = state_mod.load_state()
    by_id = discover(repo_root)
    messages: List[str] = []
    changed = False
    for record in list(state.get("installs", [])):
        if target and record.get("target") != target:
            continue
        adapter = adapters.get(record.get("target"))
        if adapter is None:
            messages.append(f"{record['id']}: adapter {record.get('target')!r} is not available")
            continue
        missing = [
            item
            for item in record.get("paths", [])
            if not Path(item["path"]).exists()
        ]
        if not missing:
            continue
        cap = by_id.get(record["id"])
        if cap is None:
            messages.append(f"{record['id']}: canonical capability no longer exists")
            continue
        context = AdapterContext(
            repo_root=repo_root,
            scope=record.get("scope", "global"),
            project=Path(record["root"]).parent if record.get("scope") == "project" else None,
            copy=record.get("mode") == "copy",
        )
        try:
            actions = adapter.plan(cap, context)
            restored = _restore_missing(actions)
        except (InstallError, ValueError, OSError) as exc:
            messages.append(f"{record['id']}: could not restore: {exc}")
            continue
        if not restored:
            continue
        by_path = {action.destination: action for action in actions}
        for item in record.get("paths", []):
            action = by_path.get(Path(item["path"]))
            if action is not None:
                item["hash"] = action.hash()
                item["source"] = (
                    str(action.source.resolve()) if action.source else None
                )
        record["hash"] = cap.hash
        record["version"] = cap.version
        changed = True
        messages.append(f"{record['id']}: restored {len(restored)} missing path(s)")
    if changed:
        try:
            state_mod.save_state(state)
        except OSError as exc:
            messages.append(f"could not save state after restore: {exc}")
    return messages


def update_all(
    repo_root: Path,
    adapters: Dict[str, Adapter],
    target: Optional[str] = None,
    ids: Optional[List[str]] = None,
    force: bool = False,
) -> List[str]:
    repo_root = Path(repo_root)
    state = state_mod.load_state()
    by_id = discover(repo_root)
    messages: List[str] = []
    for record in list(state.get("installs", [])):
        if target and record.get("target") != target:
            continue
        if ids and record["id"] not in ids:
            continue
        adapter = adapters.get(record.get("target"))
        if adapter is None:
            messages.append(f"{record['id']}: adapter {record.get('target')!r} is not available")
            continue
        cap = by_id.get(record["id"])
        if cap is None:
            messages.append(f"{record['id']}: canonical capability no longer exists")
            continue
        context = AdapterContext(
            repo_root=repo_root,
            scope=record.get("scope", "global"),
            project=Path(record["root"]).parent if record.get("scope") == "project" else None,
            copy=record.get("mode") == "copy",
        )
        install_set(repo_root, adapter, [record["id"]], context, force=force, no_deps=True)
        messages.append(f"{record['id']}: {record.get('version')} -> {cap.version}")
    return messages


def doctor(repo_root: Path, adapters: Dict[str, Adapter]) -> List[Tuple[str, str]]:
    """Return (level, message) rows. Levels: ok, warn, info, error."""
    repo_root = Path(repo_root)
    rows: List[Tuple[str, str]] = []
    state = state_mod.load_state()
    by_id = discover(repo_root)
    if not state.get("installs"):
        rows.append(("info", "no nskills installs recorded"))
    for record in state.get("installs", []):
        label = f"{record['id']} [{record.get('target')}]"
        adapter = adapters.get(record.get("target"))
        if adapter is None:
            rows.append(("error", f"{label}: adapter missing"))
            continue
        missing = []
        drifted = []
        for item in record.get("paths", []):
            path = Path(item["path"])
            if not path.exists():
                missing.append(path)
            elif not _managed_path(record, path, repo_root):
                drifted.append(path)
        if missing:
            rows.append(("warn", f"{label}: {len(missing)} installed path(s) missing; run nskills sync"))
        else:
            rows.append(("ok", f"{label}: installed at {record.get('version')}"))
        if drifted:
            rows.append(
                (
                    "warn",
                    f"{label}: {len(drifted)} path(s) changed since install; "
                    "run nskills update or uninstall --force",
                )
            )
        cap = by_id.get(record["id"])
        if cap is None:
            rows.append(("warn", f"{label}: canonical capability missing"))
        elif cap.version != record.get("version"):
            rows.append(("info", f"{label}: update available {record.get('version')} -> {cap.version}"))
        elif record.get("mode") == "copy" and cap.hash != record.get("hash"):
            rows.append(("info", f"{label}: source changed since install; run nskills update"))
        if cap:
            root = Path(str(record.get("root", "")))
            for key, dep_type in (("skills", "skill"), ("agents", "agent")):
                for dep_id in cap.depends.get(key, []):
                    dependency = state_mod.find_record(
                        state,
                        dep_id,
                        str(record.get("target")),
                        str(record.get("scope")),
                        root,
                    )
                    if dependency is None:
                        rows.append(
                            (
                                "warn",
                                f"{label}: missing {dep_type} dependency {dep_id}; "
                                f"install it for {record.get('target')}",
                            )
                        )
            for tool in cap.depends.get("tools", []):
                if shutil.which(tool) is None:
                    rows.append(("warn", f"{label}: required tool not found: {tool}"))
    return rows


def installed_ids(target: Optional[str] = None) -> Dict[Tuple[str, str], Dict[str, Any]]:
    state = state_mod.load_state()
    result: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for record in state.get("installs", []):
        if target and record.get("target") != target:
            continue
        result[(record["id"], record.get("target", ""))] = record
    return result
