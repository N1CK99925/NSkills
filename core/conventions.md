# NSkills conventions

Version: 1

These are the rules every canonical capability follows. The validator enforces
the machine-checkable parts.

## 1. Identifiers

- Lowercase kebab-case: `^[a-z0-9]+(-[a-z0-9]+)*$`.
- 1 to 64 characters.
- The directory name is the identifier. The frontmatter `name` is the display
  name.
- IDs are stable. Renaming requires a migration record and an alias in the
  registry.

## 2. Layout

```
skills/<id>/SKILL.md          required entry point
skills/<id>/references/*      optional supporting material
skills/<id>/scripts/*         optional executable helpers
skills/<id>/assets/*          optional binary or template assets
workflows/<id>/WORKFLOW.md    required entry point
agents/<id>/AGENT.md          required entry point
rules/<id>.md                 stable policy fragment
```

Supporting paths written inside a capability are relative to the capability
directory.

## 3. Common frontmatter

Every canonical capability starts with YAML frontmatter:

```yaml
---
name: Display Name
description: One sentence that says when to use this.
version: 0.1.0
license: MIT
compatibility: [opencode, hermes, freebuff, generic]
metadata:
  nskills:
    tags: [topic, topic]
    provenance: pstack:skill-id
---
```

Required:

| Key | Rule |
| --- | --- |
| `name` | Non-empty display name |
| `description` | One sentence, at most 1024 characters, starts with a verb or "Use when" |
| `version` | Semantic version `MAJOR.MINOR.PATCH` |
| `license` | SPDX identifier |
| `compatibility` | Non-empty subset of adapter target names |
| `metadata.nskills.tags` | 1 to 8 lowercase kebab-case tags |
| `metadata.nskills.provenance` | `original`, `pstack:<id>`, or `derived:pstack:<id>` |

Optional:

| Key | Use |
| --- | --- |
| `user-invocable` | `false` hides a reference leaf from command generation |
| `paths` | Glob list for host adapters that support path activation |
| `depends.skills` | Skill IDs required before this capability runs |
| `depends.tools` | Executable names checked by `nskills doctor` |
| `depends.agents` | Agent IDs required by a workflow |
| `metadata.nskills.notes` | Short maintainer note |

The canonical body never names a host tool. It uses the vocabulary in section 4.
Adapter manifests map that vocabulary to host tools.

## 4. Canonical capability vocabulary

Use these words in instructions instead of host tool names:

| Term | Meaning |
| --- | --- |
| `read` | Read a file or URL |
| `search` | Search file contents or paths |
| `edit` | Create or modify files |
| `shell` | Run a command in the workspace |
| `delegate` | Launch a subagent with a stated responsibility |
| `web` | Fetch or search the web |
| `ask-human` | Ask the operator for a decision |
| `load-skill` | Load another skill by ID |
| `track` | Maintain a task list or progress record |

Do not write: `Skill`, `Agent`, `Task`, `Bash`, `Read`, `Write`, `Edit`,
`Glob`, `Grep`, `AskUserQuestion`, `subagent_type`, `claude-*`, `gpt-*`, or a
host-specific plugin path. The validator rejects these in canonical bodies.
References to external commands such as `gh` are allowed when declared in
`depends.tools`.

## 5. Compatibility

Target names are adapter names:

- `opencode`
- `hermes`
- `freebuff`
- `generic`

A capability may list only targets that its adapter can install. The validator
checks this against `adapters/<target>/adapter.json`.

`generic` means the cross-tool Agent Skills convention. When two targets read
the same directory, one install can serve both hosts, but state is tracked per
target. Give a shared directory one owning target rather than installing the
same path twice; a second target's install is refused as unmanaged.

## 6. Dependencies

- Skills may depend on skills and tools.
- Workflows must declare every skill and agent they use.
- Agents may depend on tools and skills.
- Dependencies must exist and be acyclic.
- The installer resolves dependencies by default. `--no-deps` skips resolution
  and records an incomplete install so `doctor` can report it.

## 7. Workflows

A workflow is an execution contract, not a prompt dump. Required sections:

1. `# Objective`
2. `# Inputs`
3. `# Steps`
4. `# Skills`
5. `# Agents`
6. `# Outputs`
7. `# Approval checkpoints`
8. `# Failure behavior`
9. `# Completion criteria`

Steps reference skills by ID with `load-skill`. A workflow must not restate a
skill's instructions. It names the skill and the outcome the step needs.

## 8. Agents

An agent defines responsibility, not personality. Required sections:

1. `# Responsibility`
2. `# Instructions`
3. `# Capabilities`
4. `# Inputs and outputs`
5. `# Delegation`
6. `# Tools`

The frontmatter `mode` is `primary` or `subagent`. `tools` lists canonical
capability terms. `delegates` is `none`, `same-kind`, or a list of agent IDs.

## 9. Rules

Rules are short, stable policy fragments. They are not installed as skills.
Adapters may render a rule into a host instruction file only when the operator
asks for it. No adapter edits an existing instruction file automatically.

## 10. Versioning

- `0.x` is pre-stable. Behavior may change.
- `MAJOR` changes remove or rename behavior.
- `MINOR` adds behavior.
- `PATCH` clarifies without changing behavior.
- Installed state records the installed version and a content hash. `doctor`
  reports drift. `update` records the new version and hash.

## 11. Provenance

- Original work: `metadata.nskills.provenance: original`.
- Direct port: `pstack:<source-id>` plus an entry in `provenance/pstack.json`.
- Rewrite: `derived:pstack:<source-id>` plus an entry describing what changed.
- Imported files keep `license: MIT` and a root notice with upstream
  copyright.
- Never label imported material as independently authored.

## 12. Acceptance checks

A capability is valid only when:

- Frontmatter parses and satisfies section 3.
- The ID matches the directory.
- Every relative link and `references/`/`scripts/` path exists.
- Dependencies exist and all cycles are absent.
- Workflows contain every required section and all references resolve.
- Agents contain every required section.
- Compatibility names are real adapters and the adapter supports the type.
- Provenance is present and recorded.
- The registry entry matches the file.
- A real install and uninstall succeed in a temporary root.

Run `nskills validate`. Run `python3 -m unittest discover -s tests`.
