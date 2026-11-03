#!/usr/bin/env python3
"""Import the first-wave Pstack skills with normalized metadata.

Run once from the NSkills repository root:
    python3 tools/import_pstack.py /path/to/pstack-claude

The source repository is read-only. Existing destination directories are
replaced only when they are absent or match a prior import; this script is kept
for the audit trail and is not part of the install path.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from nskills import frontmatter  # noqa: E402

IMPORTS = [
    {
        "id": "unslop",
        "name": "Unslop",
        "tags": ["writing", "editing", "prose"],
    },
    {
        "id": "technical-writing",
        "name": "Technical Writing",
        "tags": ["writing", "documentation", "review"],
    },
    {
        "id": "tdd",
        "name": "Test-Driven Bug Fix",
        "tags": ["testing", "debugging", "verification"],
    },
    {
        "id": "deslop",
        "name": "Deslop",
        "tags": ["code-quality", "cleanup", "review"],
    },
    {
        "id": "fix-ci",
        "name": "Fix CI",
        "tags": ["ci", "github", "debugging"],
        "tools": ["git", "gh"],
    },
    {
        "id": "fix-merge-conflicts",
        "name": "Fix Merge Conflicts",
        "tags": ["git", "merge", "verification"],
        "tools": ["git"],
    },
    {
        "id": "bro",
        "name": "Bro",
        "tags": ["communication", "plain-language"],
    },
    {
        "id": "sharpen",
        "name": "Sharpen",
        "tags": ["planning", "prompting", "depth"],
    },
    {
        "id": "principle-prove-it-works",
        "name": "Prove It Works",
        "tags": ["verification", "evidence"],
        "user_invocable": False,
        "replacements": [
            (
                " (the **show-me-your-work** skill).",
                ".",
            )
        ],
    },
    {
        "id": "principle-fix-root-causes",
        "name": "Fix Root Causes",
        "tags": ["debugging", "root-cause"],
        "user_invocable": False,
    },
    {
        "id": "principle-laziness-protocol",
        "name": "Laziness Protocol",
        "tags": ["minimal-change", "refactoring"],
        "user_invocable": False,
    },
    {
        "id": "principle-model-the-domain",
        "name": "Model the Domain",
        "tags": ["design", "data-modeling"],
        "user_invocable": False,
    },
    {
        "id": "principle-boundary-discipline",
        "name": "Boundary Discipline",
        "tags": ["architecture", "validation"],
        "user_invocable": False,
    },
    {
        "id": "principle-type-system-discipline",
        "name": "Type System Discipline",
        "tags": ["types", "design"],
        "user_invocable": False,
    },
    {
        "id": "principle-test-behavior-not-implementation",
        "name": "Test Behavior, Not Implementation",
        "tags": ["testing", "design"],
        "user_invocable": False,
    },
    {
        "id": "principle-encode-lessons-in-structure",
        "name": "Encode Lessons in Structure",
        "tags": ["automation", "tooling"],
        "user_invocable": False,
    },
    {
        "id": "principle-explain-the-number",
        "name": "Explain the Number",
        "tags": ["measurement", "performance"],
        "user_invocable": False,
    },
    {
        "id": "principle-subtract-before-you-add",
        "name": "Subtract Before You Add",
        "tags": ["refactoring", "sequencing"],
        "user_invocable": False,
    },
    {
        "id": "principle-sequence-verifiable-units",
        "name": "Sequence Verifiable Units",
        "tags": ["planning", "verification"],
        "user_invocable": False,
    },
    {
        "id": "principle-minimize-reader-load",
        "name": "Minimize Reader Load",
        "tags": ["readability", "design"],
        "user_invocable": False,
    },
    {
        "id": "benchmark-checklist",
        "name": "Benchmark Checklist",
        "tags": ["performance", "measurement"],
    },
    {
        "id": "principle-guard-the-context-window",
        "name": "Guard the Context Window",
        "tags": ["context", "reading"],
        "user_invocable": False,
    },
]


def source_commit(source_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def render_meta(item, description: str, skill_deps) -> str:
    compatibility = "[opencode, hermes, freebuff, generic]"
    lines = [
        "---",
        f"name: {json.dumps(item['name'])}",
        f"description: {json.dumps(description.strip())}",
        "version: 0.1.0",
        "license: MIT",
        f"compatibility: {compatibility}",
    ]
    if item.get("user_invocable") is False:
        lines.append("user-invocable: false")
    if item.get("tools") or skill_deps:
        lines.append("depends:")
        if skill_deps:
            lines.append("  skills: [" + ", ".join(skill_deps) + "]")
        if item.get("tools"):
            lines.append("  tools: [" + ", ".join(item["tools"]) + "]")
    lines.extend(
        [
            "metadata:",
            "  nskills:",
            "    tags: [" + ", ".join(item["tags"]) + "]",
            f"    provenance: pstack:{item['id']}",
            "---",
            "",
        ]
    )
    return "\n".join(lines)


SIBLING_LINK_RE = re.compile(r"\[([^\]]+)\]\(\.\./([a-z0-9-]+)/SKILL\.md\)")


def rewrite_sibling_links(body: str):
    """Replace relative links to sibling skills with canonical skill IDs.

    Canonical capabilities do not link outside their own directory; they name
    the skill and declare it in depends.skills instead.
    """
    found = []

    def replace(match):
        skill_id = match.group(2)
        if skill_id not in found:
            found.append(skill_id)
        return f"`{skill_id}`"

    return SIBLING_LINK_RE.sub(replace, body), found


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    source_root = Path(argv[1]).resolve() / "plugins" / "pstack" / "skills"
    if not source_root.is_dir():
        print(f"error: {source_root} is not a skills directory", file=sys.stderr)
        return 1
    commit = source_commit(source_root.parents[2])
    provenance = {
        "source": {
            "repository": "https://github.com/michael-denyer/pstack-claude",
            "commit": commit,
            "audited_at": "2026-11-03",
            "license": "MIT",
            "copyright": "Copyright (c) 2026 Lauren Tan; portions Copyright (c) 2026 Cursor",
        },
        "imports": {},
    }
    for item in IMPORTS:
        source = source_root / item["id"]
        if not source.is_dir():
            print(f"error: missing source skill {source}", file=sys.stderr)
            return 1
        text = (source / "SKILL.md").read_text(encoding="utf-8")
        meta, body = frontmatter.parse(text)
        for old, new in item.get("replacements", []):
            body = body.replace(old, new)
        body, skill_deps = rewrite_sibling_links(body)
        destination = ROOT / "skills" / item["id"]
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        (destination / "SKILL.md").write_text(
            render_meta(item, str(meta.get("description", "")), skill_deps)
            + body.lstrip("\n"),
            encoding="utf-8",
        )
        provenance["imports"][item["id"]] = {
            "class": "port",
            "target": item["id"],
            "upstream_path": f"plugins/pstack/skills/{item['id']}",
            "changes": "Frontmatter normalized; host coupling removed; sibling skill links rewritten to skill IDs.",
        }
        print(f"imported {item['id']}")
    provenance["imports"]["design-before-code"] = {
        "class": "rewrite",
        "target": "design-before-code",
        "upstream_path": "plugins/pstack/skills/architect",
        "changes": (
            "Rewritten as a harness-neutral skill. Removed arena fan-out, model "
            "policy, runtime mappings, and phase links. Kept the ground/sketch/"
            "agree/implement/scrap loop. Ported references/design-red-flags.md "
            "verbatim."
        ),
    }
    provenance_path = ROOT / "provenance" / "pstack.json"
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {provenance_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
