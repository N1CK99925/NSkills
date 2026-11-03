# NSkills architecture

Status: implemented baseline
Version: 0.1.0

## 1. Goal

Keep one canonical definition of each engineering capability and install a
compatible rendering into whichever agent environment is in use. Improve a skill
once; distribute it everywhere the target supports it.

## 2. Layers

```
canonical repository                  target environment
-------------------                   ------------------
skills/       Agent Skills      --+
workflows/    orchestration       +--> adapter --> skills/, agents/, commands/,
agents/       responsibility      |                bundles/, instruction files
rules/        stable policy     --+
        |
        v
registry/registry.json  metadata index (no content)
        |
        v
core/nskills/  parser, validator, installer, state, CLI
```

Strict rule: canonical files never contain host-specific tool names, model IDs,
plugin paths, or installation paths. Those live in `adapters/<target>/`.

## 3. Capability types

| Type | Entry file | Contract |
| --- | --- | --- |
| Skill | `skills/<id>/SKILL.md` | When to use, instructions, dependencies, supporting files |
| Workflow | `workflows/<id>/WORKFLOW.md` | Objective, inputs, steps, skills, agents, outputs, approvals, failure, completion |
| Agent | `agents/<id>/AGENT.md` | Responsibility, instructions, capabilities, I/O, delegation, tools |
| Rule | `rules/<id>.md` | Stable policy fragment, rendered only on request |

A workflow references skills. It never copies their instructions. An agent is a
responsibility boundary, not a persona. A rule is policy, not a task.

## 4. Discovery and validation

`nskills validate` performs:

1. Walk `skills/`, `workflows/`, `agents/`.
2. Parse YAML frontmatter with a dependency-free parser.
3. Check required fields, ID shape, version, tags, provenance.
4. Check every relative Markdown link and every `references/`, `scripts/`,
   `assets/` path.
5. Reject host tool names and model IDs in canonical bodies.
6. Resolve skill, agent, and tool dependencies; detect cycles.
7. Check workflow and agent required sections.
8. Check compatibility against adapter manifests.
9. Compare the registry with the filesystem.

The registry is rebuilt with `nskills registry build` and checked with
`nskills validate`. It stores metadata and paths, never bodies.

## 5. Runtime selection

The user names targets:

```bash
nskills install design-before-code --target opencode
nskills install implement-feature --target hermes
nskills install --all --target freebuff
```

Each adapter declares:

- `name`, display name, and status (`verified`, `partial`, `experimental`).
- Global and project roots.
- Supported capability types.
- Preferred install mode (symlink or copy).
- Verification date and notes.

Adapter capability support:

| Capability | OpenCode | Hermes | Freebuff | Generic |
| --- | --- | --- | --- | --- |
| Skills | native | native | native Agent Skills | native Agent Skills |
| Workflows | rendered skill + command | skill bundle | rendered skill | rendered skill |
| Agents | native agent file | rendered agent skill | rendered skill (no native registry) | rendered skill |
| Rules | not installed | not installed | not installed | not installed |

Unsupported combinations fail before writing, with a clear reason.

## 6. Installation model

An install is a set of actions:

- `symlink`: link a canonical directory into the target. Default where the
  target follows links.
- `copy-tree`: copy a canonical directory. Used by `--copy` and targets that
  cannot follow links.
- `write`: render a file from canonical content (agent markdown, command, bundle
  YAML, workflow wrapper).

Safety:

- Every destination is checked against install state.
- An unmanaged existing path is never overwritten. `--force` moves it to a
  timestamped backup first.
- Install state is the only ownership proof. A symlink that happens to point
  into the NSkills repository is still unmanaged until a state record names it.
- Uninstall removes only paths recorded for that install, and only when they
  still match the recorded ownership. A modified path requires `--force`, which
  keeps the removed files in a timestamped backup.
- `sync` restores missing recorded paths only. It never overwrites an existing
  path, so local edits survive a repair.
- State lives at `$XDG_STATE_HOME/nskills/state.json` (typically
  `~/.local/state/nskills/state.json`).
- `--force` backups live under `$XDG_STATE_HOME/nskills/backups/`.

State record:

```json
{
  "id": "unslop",
  "type": "skill",
  "target": "opencode",
  "scope": "global",
  "root": "/home/me/.config/opencode",
  "version": "0.1.0",
  "hash": "sha256:...",
  "mode": "symlink",
  "paths": [
    {
      "path": "/home/me/.config/opencode/skills/unslop",
      "kind": "dir",
      "hash": "sha256:...",
      "source": "/home/me/NSkills/skills/unslop"
    }
  ],
  "dependencies": {"skills": [], "agents": [], "tools": []},
  "installed_at": "2026-11-03T00:00:00Z"
}
```

`mode` records how the capability was installed. Generated files use `copy`.
`source` is recorded only for symlinks so `doctor` and `uninstall` can tell
whether a link still points at the canonical capability.

## 7. CLI

```
nskills list [--type TYPE] [--target TARGET] [--installed]
nskills search QUERY
nskills inspect ID [--json]
nskills install ID... [--target TARGET]... [--scope global|project]
                       [--project DIR] [--copy] [--force] [--no-deps]
nskills uninstall ID... --target TARGET [--scope ...]
nskills sync [--target TARGET]
nskills update [ID...] [--target TARGET]
nskills doctor
nskills validate [--write]
nskills registry build
nskills targets
```

`list` and `search` read the registry. `inspect` shows the metadata and a short
body preview. `install` resolves dependencies and writes state. `sync` restores
missing managed paths. `update` reinstalls managed capabilities from the current
repository. `doctor` checks adapters, tools, and installs. `validate` is the
repository gate.

## 8. Adapters

### OpenCode

Verified against OpenCode V2 docs on 2026-11-03.

- Global skills: `~/.config/opencode/skills/<id>`
- Project skills: `.opencode/skills/<id>`
- Global agents: `~/.config/opencode/agents/<id>.md`
- Project agents: `.opencode/agents/<id>.md`
- Global commands: `~/.config/opencode/commands/<id>.md`
- Project commands: `.opencode/commands/<id>.md`
- Skill ID is the directory name; frontmatter `name` is a label.
- Agents accept frontmatter `description`, `mode`, `permissions`, `model`.
- Commands accept `$ARGUMENTS`.

Workflows install as a generated skill `workflow-<id>` plus a command `<id>`.

### Hermes

Verified against Hermes' local installation on 2026-11-03.

- Skills root: `$HERMES_HOME/skills` (default `~/.hermes/skills`).
- Nested directories become categories. NSkills uses `nskills/` and
  `nskills/agents/`.
- Workflows install as `$HERMES_HOME/skill-bundles/<id>.yaml`, which Hermes
  exposes as `/<id>` and uses to load several skills.
- No file-based agent registry was found. Agents are installed as loadable
  instruction skills, documented as a partial mapping.
- Rules are not installed.

### Freebuff

Investigated on 2026-11-03. Freebuff is a Codebuff-derived binary. Its system
prompt and its own guidance use the cross-tool `.agents/skills` convention and a
`skill` tool. Its distributed launcher has no local skill, agent, command, or
MCP configuration file; project state is limited to `.freebuff/project-id`. The
repository-level `.agents` directory is loaded with `--trust-agents`.

- Global skills: `~/.agents/skills/<id>`
- Project skills: `.agents/skills/<id>`
- Workflows and agents: rendered as Agent Skills because no native registry was
  found.
- Limitation: not verified inside a live Freebuff session. The adapter is marked
  `partial`.

### Generic

The cross-tool Agent Skills convention:

- Global: `~/.agents/skills`
- Project: `.agents/skills`

Skills are native. Workflows and agents render as skill wrappers. No commands,
hooks, or instructions are edited.

## 9. Human-in-the-loop

Canonical rules:

- Reading, analysis, local reversible edits, and tests proceed without asking.
- Ask before: force-push, history rewrite, deleting data, deploying, sending
  external messages, installing hooks, editing a global instruction file.
- Workflows declare their own approval checkpoints. A workflow cannot grant
  itself broader permission than `rules/global.md`.
- Unsafe or irreversible actions are never inferred from a skill description.

## 10. Failure behavior

- Invalid metadata fails validation with file and field.
- Missing references fail validation; the installer also refuses to install an
  invalid capability.
- Missing tools do not block installation. `doctor` reports them.
- Unsupported target/type combinations fail before writing.
- An unmanaged destination causes a refusal, not a merge.
- `--no-deps` installs are partial by request; `doctor` reports the absent
  dependencies.
- Adapter write failures remove paths created by that attempt and leave the
  previous state intact.

## 11. Non-goals

- Model selection or model policy.
- A plugin marketplace.
- Session-start prompt injection.
- Automatic editing of `AGENTS.md`, `CLAUDE.md`, or host config.
- A database.
- Vendor-specific runtime code inside canonical capabilities.
