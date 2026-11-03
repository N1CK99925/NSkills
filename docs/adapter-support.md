# Adapter support

Each adapter is a manifest plus a Python module under `adapters/<name>/`. The
manifest states support, status, and verification date. The module computes
install actions. Nothing in `skills/`, `workflows/`, or `agents/` names a host
path.

Verification date: 2026-11-03.

## Matrix

| Capability | OpenCode | Hermes | Freebuff | Generic |
| --- | --- | --- | --- | --- |
| Skill | native directory | native directory | Agent Skills | Agent Skills |
| Workflow | rendered skill + command | skill bundle | rendered skill | rendered skill |
| Agent | native markdown | rendered instruction skill | rendered skill | rendered skill |
| Rule | unsupported | unsupported | unsupported | unsupported |

Install mode: OpenCode, Freebuff, and generic symlink by default. Hermes copies
by default. Use `--copy` or `--symlink` to override.

## OpenCode

Status: verified. Sources: the OpenCode V2 skills, agents, and commands docs.

| Scope | Path |
| --- | --- |
| Global skills | `~/.config/opencode/skills/<id>/` |
| Project skills | `.opencode/skills/<id>/` |
| Global agents | `~/.config/opencode/agents/<id>.md` |
| Project agents | `.opencode/agents/<id>.md` |
| Global commands | `~/.config/opencode/commands/<id>.md` |
| Project commands | `.opencode/commands/<id>.md` |

Notes:

- The directory name is the skill ID. Frontmatter `name` is a display label.
- OpenCode reads `~/.agents/skills` and `.agents/skills` as compatibility
  sources. Skills installed by the generic or Freebuff adapter are visible to
  OpenCode too.
- Agents are markdown files; the body becomes the system prompt. The adapter
  emits `description`, `mode`, and `permissions`.
- Permissions deny `edit` when the canonical agent does not declare `edit`, and
  deny `shell` when it does not declare `shell`.
- Workflows install as `workflow-<id>` under `skills/` plus `<id>` under
  `commands/`. The command body loads the generated skill and passes
  `$ARGUMENTS`.
- `user-invocable: false` is not interpreted by OpenCode in V2. Reference
  leaves are installed and advertised unless you install selectively.

## Hermes

Status: verified against a local Hermes installation.

| Capability | Path |
| --- | --- |
| Skills | `$HERMES_HOME/skills/nskills/<id>/` |
| Agents | `$HERMES_HOME/skills/nskills/agents/<id>/SKILL.md` |
| Workflows, global | `$HERMES_HOME/skill-bundles/<id>.yaml` |
| Workflows, project | `<project>/.hermes/skills/nskills/workflow-<id>/SKILL.md` |

`HERMES_HOME` defaults to `~/.hermes`. Nested directories under `skills/` become
categories, so NSkills owns the `nskills` category.

Notes:

- Bundles require a non-empty `skills` list and load each entry by relative path
  from the skills root. The adapter writes `nskills/<id>`, not the bare ID.
- A bundle that names a missing skill still loads; Hermes reports the skipped
  entry. This happens with `--no-deps`.
- Hermes has no file-based agent registry. Agents become loadable instruction
  skills under `nskills/agents/`. This is a partial mapping, stated in the
  manifest, not native subagent dispatch.
- Hermes warns when a skill resolves outside its trusted skills directory
  through a symlink. Copies are the default for that reason.
- Rules are not installed.

## Freebuff

Status: partial. The path convention was verified from Freebuff's own guidance
and distributed files; loading inside a live session was not verified.

| Scope | Path |
| --- | --- |
| Global | `~/.agents/skills/<id>/` |
| Project | `.agents/skills/<id>/` |

Notes:

- Freebuff has no discovered local agent, command, or MCP configuration file.
  Workflows and agents render as generated Agent Skills.
- The project `.agents` directory requires Freebuff's trust flag
  (`--trust-agents`) to load.
- Treat this adapter as a convention-based install, not a native integration.

## Generic

Status: verified as a convention, not as a specific host.

| Scope | Path |
| --- | --- |
| Global | `~/.agents/skills/<id>/` |
| Project | `.agents/skills/<id>/` |

Uses the cross-tool Agent Skills layout. Skills are native; workflows and agents
render as generated skills. No instruction file, hook, or host config is edited.

## Skills-only hosts

Any host that reads a directory of `SKILL.md` trees can use the generic adapter
with an explicit project root. Point `--project` at the host's skill directory
and install with `--symlink` if the host follows links.

## What no adapter does

- No model selection.
- No session hooks.
- No automatic edit of `AGENTS.md`, `CLAUDE.md`, or host configuration.
- No installation of rules.
- No claim of support that was not verified. Unverified behavior is marked
  `partial` in the manifest and here.
