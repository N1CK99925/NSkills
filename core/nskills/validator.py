"""Repository validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from . import frontmatter
from .adapters import AdapterError, load_adapters
from .model import (
    ENTRY_FILES,
    TYPE_DIRS,
    TYPE_ORDER,
    Capability,
    CapabilityError,
    all_capabilities,
    load_capability,
)
from .registry import REGISTRY_PATH, build_registry, read_registry

ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
TAG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

REQUIRED_FIELDS = {
    "skill": ["name", "description", "version", "license", "compatibility", "metadata"],
    "workflow": [
        "name",
        "description",
        "version",
        "license",
        "compatibility",
        "inputs",
        "outputs",
        "skills",
        "agents",
        "approval",
        "metadata",
    ],
    "agent": [
        "name",
        "description",
        "version",
        "license",
        "compatibility",
        "mode",
        "tools",
        "delegates",
        "metadata",
    ],
}

WORKFLOW_SECTIONS = [
    "Objective",
    "Inputs",
    "Steps",
    "Skills",
    "Agents",
    "Outputs",
    "Approval checkpoints",
    "Failure behavior",
    "Completion criteria",
]
AGENT_SECTIONS = [
    "Responsibility",
    "Instructions",
    "Capabilities",
    "Inputs and outputs",
    "Delegation",
    "Tools",
]

HOST_TOOL_PATTERNS = [
    re.compile(r"`(?:Skill|Agent|Task|Bash|Read|Write|Edit|Glob|Grep|AskUserQuestion|TaskCreate|TaskUpdate)`"),
    re.compile(r"\bsubagent_type\b"),
    re.compile(r"CLAUDE_PLUGIN_ROOT|CODEX_PLUGIN_ROOT|COPILOT_PLUGIN_ROOT|MUSE_PLUGIN_ROOT"),
    re.compile(r"(?:^|[\s`(])(?:\.claude/|plugins/pstack|pstack-models)"),
    re.compile(r"\bclaude-[a-z0-9][a-z0-9.\-]*"),
    re.compile(r"\bgpt-[a-z0-9][a-z0-9.\-]*"),
]

LINK_RE = re.compile(r"\[[^\]]*\]\((<[^>]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\)")
PATH_REF_RE = re.compile(r"`((?:\.{0,2}/)?(?:references|scripts|assets)/[^`\s]+)`")
LOAD_SKILL_RE = re.compile(r"`load-skill`\s+`([a-z0-9]+(?:-[a-z0-9]+)*)`")


@dataclass
class Report:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def _line_of(text: str, needle: str) -> int:
    for index, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return index
    return 0


def validate_repo(repo_root: Path) -> Report:
    repo_root = Path(repo_root)
    report = Report()

    try:
        adapters = load_adapters(repo_root)
    except AdapterError as exc:
        report.error(str(exc))
        adapters = {}

    caps: List[Capability] = []
    seen: Dict[str, Capability] = {}
    for cap_type, directory in TYPE_DIRS.items():
        base = repo_root / directory
        if not base.is_dir():
            report.error(f"{base}: missing {directory} directory")
            continue
        for child in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")):
            entry = child / ENTRY_FILES[cap_type]
            if not entry.is_file():
                report.error(f"{entry}: missing {ENTRY_FILES[cap_type]}")
                continue
            try:
                cap = load_capability(repo_root, cap_type, child.name)
            except CapabilityError as exc:
                report.error(str(exc))
                continue
            caps.append(cap)
            if cap.id in seen:
                report.error(
                    f"{entry}: duplicate id {cap.id!r}; also defined by "
                    f"{seen[cap.id].entry_file}"
                )
            else:
                seen[cap.id] = cap
            _validate_capability(cap, repo_root, adapters, report)

    _validate_cycles(caps, report)
    _validate_registry(repo_root, report)
    _validate_provenance(caps, repo_root, report)
    _validate_rules(repo_root, report)
    return report


def _validate_capability(
    cap: Capability,
    repo_root: Path,
    adapters: Dict[str, Any],
    report: Report,
) -> None:
    entry = cap.entry_file
    rel = entry.relative_to(repo_root)
    meta = cap.meta

    if not ID_RE.match(cap.id):
        report.error(f"{entry}: id {cap.id!r} is not lowercase kebab-case")
    elif len(cap.id) > 64:
        report.error(f"{entry}: id is {len(cap.id)} characters; max is 64")

    for key in REQUIRED_FIELDS[cap.type]:
        if key not in meta or meta[key] in (None, "", []):
            report.error(f"{entry}: missing required frontmatter key {key!r}")

    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        report.error(f"{entry}: name must be a non-empty string")
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        report.error(f"{entry}: description must be a non-empty string")
    elif len(description) > 1024:
        report.error(f"{entry}: description is {len(description)} characters; max is 1024")
    version = meta.get("version")
    if not isinstance(version, str) or not VERSION_RE.match(version):
        report.error(f"{entry}: version must be MAJOR.MINOR.PATCH")
    license_name = meta.get("license")
    if not isinstance(license_name, str) or not license_name.strip():
        report.error(f"{entry}: license must be a non-empty string")

    compatibility = meta.get("compatibility")
    if not isinstance(compatibility, list) or not compatibility:
        report.error(f"{entry}: compatibility must be a non-empty list")
    else:
        for target in compatibility:
            if not isinstance(target, str):
                report.error(f"{entry}: compatibility entries must be strings")
                continue
            adapter = adapters.get(target)
            if adapter is None:
                report.error(f"{entry}: compatibility target {target!r} has no adapter")
            elif not adapter.supports(cap.type):
                report.error(
                    f"{entry}: adapter {target!r} does not support {cap.type} installs"
                )

    metadata = meta.get("metadata")
    if not isinstance(metadata, dict):
        report.error(f"{entry}: metadata must be a mapping")
    else:
        nskills = metadata.get("nskills")
        if not isinstance(nskills, dict):
            report.error(f"{entry}: metadata.nskills must be a mapping")
        else:
            tags = nskills.get("tags")
            if not isinstance(tags, list) or not tags:
                report.error(f"{entry}: metadata.nskills.tags must be a non-empty list")
            else:
                for tag in tags:
                    if not isinstance(tag, str) or not TAG_RE.match(tag):
                        report.error(f"{entry}: invalid tag {tag!r}")
                if len(tags) > 8:
                    report.error(f"{entry}: {len(tags)} tags; max is 8")
            provenance = nskills.get("provenance")
            if not isinstance(provenance, str) or not provenance.strip():
                report.error(f"{entry}: metadata.nskills.provenance must be a string")

    depends = meta.get("depends")
    if depends is not None:
        if not isinstance(depends, dict):
            report.error(f"{entry}: depends must be a mapping")
        else:
            for key in ("skills", "agents", "tools"):
                value = depends.get(key, [])
                if not isinstance(value, list):
                    report.error(f"{entry}: depends.{key} must be a list")
                else:
                    for item in value:
                        if not isinstance(item, str) or not item.strip():
                            report.error(f"{entry}: depends.{key} entries must be strings")

    if cap.type == "skill":
        invocable = meta.get("user-invocable")
        if invocable is not None and not isinstance(invocable, bool):
            report.error(f"{entry}: user-invocable must be a boolean")
        paths = meta.get("paths")
        if paths is not None and (
            not isinstance(paths, list) or not all(isinstance(p, str) for p in paths)
        ):
            report.error(f"{entry}: paths must be a list of strings")

    if cap.type == "workflow":
        for key in ("inputs", "outputs", "skills", "agents", "approval"):
            value = meta.get(key)
            if not isinstance(value, list):
                report.error(f"{entry}: {key} must be a list")
            elif key in ("inputs", "outputs") and not value:
                report.error(f"{entry}: {key} must not be empty")
        _require_sections(cap, WORKFLOW_SECTIONS, report)

    if cap.type == "agent":
        mode = meta.get("mode")
        if mode not in ("primary", "subagent"):
            report.error(f"{entry}: mode must be 'primary' or 'subagent'")
        tools = meta.get("tools")
        valid_tools = {
            "read",
            "search",
            "edit",
            "shell",
            "delegate",
            "web",
            "ask-human",
            "load-skill",
            "track",
        }
        if not isinstance(tools, list) or not tools:
            report.error(f"{entry}: tools must be a non-empty list")
        else:
            for tool in tools:
                if tool not in valid_tools:
                    report.error(f"{entry}: unknown canonical tool {tool!r}")
        delegates = meta.get("delegates")
        if not (delegates in ("none", "same-kind") or isinstance(delegates, list)):
            report.error(f"{entry}: delegates must be 'none', 'same-kind', or a list")
        _require_sections(cap, AGENT_SECTIONS, report)

    _validate_body(cap, entry, rel, report)


def _require_sections(cap: Capability, sections: Iterable[str], report: Report) -> None:
    headings = {
        line.strip()[2:].strip()
        for line in cap.body.splitlines()
        if line.strip().startswith("# ")
    }
    for section in sections:
        if section not in headings:
            report.error(f"{cap.entry_file}: missing '# {section}' section")


def _validate_body(cap: Capability, entry: Path, rel: Path, report: Report) -> None:
    body = cap.body
    for pattern in HOST_TOOL_PATTERNS:
        for match in pattern.finditer(body):
            line = _line_of(body, match.group(0))
            report.error(
                f"{entry}:{line}: host-specific token {match.group(0)!r} in canonical body"
            )
            break

    for match in LINK_RE.finditer(body):
        target = match.group(1).strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        if target.startswith(("http://", "https://", "mailto:", "data:", "#")):
            continue
        if "{" in target or "}" in target:
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        resolved = (cap.path / target).resolve()
        if not (resolved.exists() or resolved.is_symlink()):
            line = _line_of(body, match.group(0))
            report.error(f"{entry}:{line}: broken link {target!r}")
        else:
            try:
                resolved.relative_to(cap.path.resolve())
            except ValueError:
                line = _line_of(body, match.group(0))
                report.error(f"{entry}:{line}: link escapes the capability directory: {target!r}")

    for match in PATH_REF_RE.finditer(body):
        target = match.group(1).rstrip(".,:;")
        resolved = (cap.path / target).resolve()
        if not (resolved.exists() or resolved.is_symlink()):
            line = _line_of(body, match.group(0))
            report.error(f"{entry}:{line}: missing supporting path {target!r}")

    declared = set(cap.depends.get("skills", []))
    for match in LOAD_SKILL_RE.finditer(body):
        skill_id = match.group(1)
        if skill_id not in declared:
            line = _line_of(body, match.group(0))
            report.error(
                f"{entry}:{line}: load-skill reference {skill_id!r} is not declared "
                "in depends.skills or the workflow skills list"
            )


def _validate_cycles(caps: List[Capability], report: Report) -> None:
    by_id = {}
    for cap in caps:
        by_id.setdefault(cap.id, cap)
    state: Dict[str, int] = {}

    def visit(cap: Capability, chain: List[str]) -> None:
        status = state.get(cap.id)
        if status == 1:
            cycle = chain[chain.index(cap.id) :] + [cap.id]
            report.error("dependency cycle: " + " -> ".join(cycle))
            return
        if status == 2:
            return
        state[cap.id] = 1
        for skill_id in cap.depends.get("skills", []):
            dep = by_id.get(skill_id)
            if dep is None:
                report.error(f"{cap.entry_file}: missing skill dependency {skill_id!r}")
            elif dep.type != "skill":
                report.error(f"{cap.entry_file}: dependency {skill_id!r} is a {dep.type}, not a skill")
            else:
                visit(dep, chain + [cap.id])
        for agent_id in cap.depends.get("agents", []):
            dep = by_id.get(agent_id)
            if dep is None:
                report.error(f"{cap.entry_file}: missing agent dependency {agent_id!r}")
            elif dep.type != "agent":
                report.error(f"{cap.entry_file}: dependency {agent_id!r} is a {dep.type}, not an agent")
            else:
                visit(dep, chain + [cap.id])
        state[cap.id] = 2

    for cap in caps:
        visit(cap, [])


def _validate_registry(repo_root: Path, report: Report) -> None:
    path = repo_root / REGISTRY_PATH
    if not path.is_file():
        report.error(f"{path}: registry missing; run `nskills registry build`")
        return
    try:
        stored = read_registry(repo_root)
    except json.JSONDecodeError as exc:
        report.error(f"{path}: invalid JSON: {exc}")
        return
    built = build_registry(repo_root)
    if json.dumps(stored, sort_keys=True) != json.dumps(built, sort_keys=True):
        report.error(f"{path}: stale; run `nskills registry build`")
        return
    seen: Set[str] = set()
    for entry in stored.get("capabilities", []):
        cap_id = entry.get("id")
        if cap_id in seen:
            report.error(f"{path}: duplicate registry id {cap_id!r}")
        seen.add(cap_id)
        cap_path = repo_root / entry.get("path", "")
        if not cap_path.is_dir():
            report.error(f"{path}: registry path missing for {cap_id!r}: {entry.get('path')}")
        expected = repo_root / TYPE_DIRS.get(entry.get("type", ""), "") / str(cap_id)
        if cap_path != expected:
            report.error(f"{path}: registry path for {cap_id!r} should be {expected.relative_to(repo_root)}")


def _validate_provenance(caps: List[Capability], repo_root: Path, report: Report) -> None:
    path = repo_root / "provenance" / "pstack.json"
    imports: Dict[str, Any] = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            imports = data.get("imports", {}) if isinstance(data, dict) else {}
        except json.JSONDecodeError as exc:
            report.error(f"{path}: invalid JSON: {exc}")
            return
    for cap in caps:
        provenance = cap.provenance
        if not provenance:
            continue
        if provenance == "original":
            continue
        if provenance.startswith("pstack:") or provenance.startswith("derived:pstack:"):
            key = provenance.split(":", 1)[1]
            if key.startswith("pstack:"):
                key = key.split(":", 1)[1]
            entry = imports.get(cap.id)
            if entry is None:
                report.error(
                    f"{cap.entry_file}: provenance {provenance!r} has no entry for "
                    f"{cap.id!r} in {path}"
                )
            else:
                upstream = str(entry.get("upstream_path", "")).rstrip("/")
                source_id = upstream.split("/")[-1] if upstream else key
                if key != source_id:
                    report.error(
                        f"{cap.entry_file}: provenance source {key!r} does not match "
                        f"upstream path {entry.get('upstream_path')!r}"
                    )
                expected_class = "rewrite" if provenance.startswith("derived:") else "port"
                if entry.get("class") != expected_class:
                    report.error(
                        f"{cap.entry_file}: provenance class should be {expected_class!r}, "
                        f"got {entry.get('class')!r}"
                    )
                if entry.get("target") != cap.id:
                    report.error(
                        f"{cap.entry_file}: provenance target should be {cap.id!r}"
                    )
        else:
            report.warn(f"{cap.entry_file}: unrecognized provenance {provenance!r}")


def _validate_rules(repo_root: Path, report: Report) -> None:
    base = repo_root / "rules"
    if not base.is_dir():
        report.error(f"{base}: missing rules directory")
        return
    for path in sorted(base.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 40:
            report.error(f"{path}: rule is too short to be useful")
        for pattern in HOST_TOOL_PATTERNS:
            match = pattern.search(text)
            if match:
                report.error(f"{path}:{_line_of(text, match.group(0))}: host-specific token {match.group(0)!r}")
