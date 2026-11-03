"""Command line interface for NSkills."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from . import state as state_mod
from .adapter import AdapterContext, xdg_config_home
from .adapters import AdapterError, load_adapters
from .installer import (
    InstallError,
    doctor,
    install_set,
    sync_all,
    uninstall_one,
    update_all,
)
from .model import discover, load_capability
from .registry import (
    REGISTRY_PATH,
    build_registry,
    read_registry,
    registry_by_id,
    search_registry,
    write_registry,
)
from .validator import validate_repo


def repo_root() -> Path:
    override = os.environ.get("NSKILLS_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def _adapters(root: Path):
    try:
        return load_adapters(root)
    except AdapterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)


def _registry(root: Path) -> Dict:
    data = read_registry(root)
    if not data.get("capabilities"):
        data = build_registry(root)
    return data


def _print_table(rows: List[List[str]], headers: List[str]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(str(value)))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(line)
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        print("  ".join(str(value).ljust(widths[i]) for i, value in enumerate(row)))


def cmd_list(args) -> int:
    root = repo_root()
    data = _registry(root)
    entries = data.get("capabilities", [])
    if args.type:
        entries = [e for e in entries if e.get("type") == args.type]
    installed = state_mod.load_state()
    installed_keys = {(r.get("id"), r.get("target")) for r in installed.get("installs", [])}
    if args.installed:
        installed_ids = {cap_id for cap_id, _ in installed_keys}
        entries = [e for e in entries if e["id"] in installed_ids]
        if args.target:
            entries = [
                e
                for e in entries
                if any((e["id"], t) in installed_keys for t in args.target)
            ]
    if args.target:
        entries = [e for e in entries if any(t in e.get("compatibility", []) for t in args.target)]
    if args.json:
        print(json.dumps(entries, indent=2))
        return 0
    rows = []
    for entry in entries:
        marks = []
        for target in entry.get("compatibility", []):
            if (entry["id"], target) in installed_keys:
                marks.append(target + "*")
            else:
                marks.append(target)
        rows.append(
            [
                entry.get("type", ""),
                entry.get("id", ""),
                entry.get("version", ""),
                ",".join(marks),
                entry.get("description", ""),
            ]
        )
    _print_table(rows, ["type", "id", "version", "targets", "description"])
    return 0


def cmd_search(args) -> int:
    root = repo_root()
    data = _registry(root)
    entries = search_registry(data, args.query)
    if args.json:
        print(json.dumps(entries, indent=2))
        return 0
    for entry in entries:
        print(f"{entry['type']:8} {entry['id']:32} {entry['description']}")
    if not entries:
        print("no matches")
    return 0


def cmd_inspect(args) -> int:
    root = repo_root()
    data = _registry(root)
    entry = registry_by_id(data).get(args.id)
    if entry is None:
        print(f"error: unknown capability: {args.id}", file=sys.stderr)
        return 1
    cap = load_capability(root, entry["type"], entry["id"])
    state = state_mod.load_state()
    records = [r for r in state.get("installs", []) if r.get("id") == args.id]
    if args.json:
        payload = dict(entry)
        payload["installed"] = records
        payload["body"] = cap.body.strip()
        print(json.dumps(payload, indent=2))
        return 0
    print(f"{cap.name} ({cap.type}:{cap.id}) version {cap.version}")
    print(f"path: {cap.entry_file.relative_to(root)}")
    print(f"description: {cap.description}")
    print(f"license: {cap.license}")
    print(f"compatibility: {', '.join(cap.compatibility)}")
    print(f"tags: {', '.join(cap.tags)}")
    print(f"provenance: {cap.provenance}")
    deps = cap.depends
    if any(deps.values()):
        print("depends:")
        for key in ("skills", "agents", "tools"):
            if deps[key]:
                print(f"  {key}: {', '.join(deps[key])}")
    if records:
        print("installed:")
        for record in records:
            print(
                f"  {record.get('target')} {record.get('scope')} "
                f"v{record.get('version')} at {record.get('root')}"
            )
    else:
        print("installed: no")
    print()
    print(cap.body.strip())
    return 0


def _targets(values: Optional[List[str]]) -> List[str]:
    result: List[str] = []
    for value in values or []:
        for part in value.split(","):
            part = part.strip()
            if part and part not in result:
                result.append(part)
    return result


def cmd_install(args) -> int:
    root = repo_root()
    adapters = _adapters(root)
    target_names = _targets(args.target)
    if not target_names:
        print("error: --target is required", file=sys.stderr)
        return 2
    data = _registry(root)
    ids = list(args.ids)
    if args.all:
        ids = [entry["id"] for entry in data.get("capabilities", [])]
    if not ids:
        print("error: provide one or more capability ids or --all", file=sys.stderr)
        return 2
    unknown_targets = [t for t in target_names if t not in adapters]
    if unknown_targets:
        print("error: unknown target(s): " + ", ".join(unknown_targets), file=sys.stderr)
        return 2
    context = AdapterContext(
        repo_root=root,
        scope=args.scope,
        project=Path(args.project).expanduser().resolve() if args.scope == "project" else None,
        copy=args.copy,
    )
    if args.scope == "project" and context.project is None:
        context.project = Path.cwd()
    for target in target_names:
        adapter = adapters[target]
        context.copy = args.copy or (
            not args.symlink and adapter.manifest.get("preferred_mode") == "copy"
        )
        try:
            summary = install_set(
                root,
                adapter,
                ids,
                context,
                force=args.force,
                no_deps=args.no_deps,
            )
        except InstallError as exc:
            print(f"error [{target}]: {exc}", file=sys.stderr)
            return 1
        print(f"{target}: installed {len(summary.records)}: {', '.join(summary.ids())}")
        for warning in summary.warnings:
            print(f"  warning: {warning}")
    return 0


def cmd_uninstall(args) -> int:
    root = repo_root()
    adapters = _adapters(root)
    target_names = _targets(args.target)
    if not target_names:
        print("error: --target is required", file=sys.stderr)
        return 2
    context = AdapterContext(
        repo_root=root,
        scope=args.scope,
        project=Path(args.project).expanduser().resolve() if args.project else None,
    )
    if args.scope == "project" and context.project is None:
        context.project = Path.cwd()
    for target in target_names:
        adapter = adapters.get(target)
        if adapter is None:
            print(f"error: unknown target: {target}", file=sys.stderr)
            return 2
        for cap_id in args.ids:
            try:
                record = uninstall_one(root, adapter, cap_id, context, force=args.force)
            except InstallError as exc:
                print(f"error [{target}]: {exc}", file=sys.stderr)
                return 1
            print(f"{target}: removed {record['id']} ({len(record.get('paths', []))} path(s))")
            if record.get("backup"):
                print(f"  modified paths backed up to {record['backup']}")
    return 0


def cmd_sync(args) -> int:
    root = repo_root()
    adapters = _adapters(root)
    try:
        messages = sync_all(root, adapters, target=args.target)
    except InstallError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not messages:
        print("all recorded installs are present")
    for message in messages:
        print(message)
    return 0


def cmd_update(args) -> int:
    root = repo_root()
    adapters = _adapters(root)
    try:
        messages = update_all(
            root,
            adapters,
            target=args.target,
            ids=list(args.ids) or None,
            force=args.force,
        )
    except InstallError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not messages:
        print("nothing installed to update")
    for message in messages:
        print(message)
    return 0


def cmd_doctor(args) -> int:
    root = repo_root()
    adapters = _adapters(root)
    print("Adapters")
    for name, adapter in sorted(adapters.items()):
        available, detail = adapter.detect()
        print(f"  {'ok' if available else '--'} {name:10} {adapter.status:12} {detail}")
    print("\nInstalls")
    rows = doctor(root, adapters)
    for level, message in rows:
        print(f"  {level:5} {message}")
    return 1 if any(level == "error" for level, _ in rows) else 0


def cmd_validate(args) -> int:
    root = repo_root()
    if args.write:
        path = write_registry(root)
        print(f"wrote {path.relative_to(root)}")
    report = validate_repo(root)
    for warning in report.warnings:
        print(f"warning: {warning}")
    for error in report.errors:
        print(f"error: {error}", file=sys.stderr)
    if report.ok:
        data = read_registry(root)
        print(
            f"ok: {len(data.get('capabilities', []))} capabilities, "
            f"{len(report.warnings)} warning(s)"
        )
        return 0
    print(f"failed: {len(report.errors)} error(s)", file=sys.stderr)
    return 1


def cmd_registry(args) -> int:
    root = repo_root()
    if args.action == "build":
        path = write_registry(root)
        data = read_registry(root)
        print(f"wrote {path.relative_to(root)} ({len(data.get('capabilities', []))} capabilities)")
        return 0
    if args.action == "show":
        print(json.dumps(_registry(root), indent=2))
        return 0
    print(f"error: unknown registry action {args.action}", file=sys.stderr)
    return 2


def cmd_targets(args) -> int:
    root = repo_root()
    adapters = _adapters(root)
    rows = []
    for name, adapter in sorted(adapters.items()):
        available, detail = adapter.detect()
        context = AdapterContext(repo_root=root, scope="global")
        rows.append(
            [
                name,
                adapter.status,
                "yes" if available else "no",
                ",".join(sorted(adapter.supports_types)),
                str(adapter.root(context)),
                detail,
            ]
        )
    _print_table(rows, ["target", "status", "detected", "supports", "global root", "detail"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nskills",
        description="Install canonical NSkills capabilities into agent environments.",
    )
    parser.add_argument("--version", action="version", version="nskills 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="list capabilities")
    p.add_argument("--type", choices=["skill", "workflow", "agent"])
    p.add_argument("--target", action="append")
    p.add_argument("--installed", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("search", help="search capabilities")
    p.add_argument("query")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("inspect", help="show one capability")
    p.add_argument("id")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("install", help="install capabilities")
    p.add_argument("ids", nargs="*")
    p.add_argument("--target", action="append", required=False)
    p.add_argument("--scope", choices=["global", "project"], default="global")
    p.add_argument("--project", default=None)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--copy", action="store_true", help="copy instead of symlinking")
    mode.add_argument(
        "--symlink",
        action="store_true",
        help="symlink even when the adapter prefers copies",
    )
    p.add_argument("--force", action="store_true", help="back up and replace unmanaged paths")
    p.add_argument("--no-deps", action="store_true", help="do not install dependencies")
    p.add_argument("--all", action="store_true", help="install every capability")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("uninstall", help="remove installed capabilities")
    p.add_argument("ids", nargs="+")
    p.add_argument("--target", action="append", required=True)
    p.add_argument("--scope", choices=["global", "project"], default="global")
    p.add_argument("--project", default=None)
    p.add_argument("--force", action="store_true", help="remove paths modified outside nskills")
    p.set_defaults(func=cmd_uninstall)

    p = sub.add_parser("sync", help="restore missing installed paths")
    p.add_argument("--target")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("update", help="reinstall from the current repository")
    p.add_argument("ids", nargs="*")
    p.add_argument("--target")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("doctor", help="check adapters, tools, and installs")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("validate", help="validate the repository")
    p.add_argument("--write", action="store_true", help="rebuild the registry first")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("registry", help="registry commands")
    p.add_argument("action", choices=["build", "show"])
    p.set_defaults(func=cmd_registry)

    p = sub.add_parser("targets", help="list adapters")
    p.set_defaults(func=cmd_targets)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
