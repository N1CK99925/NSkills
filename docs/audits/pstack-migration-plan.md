# Pstack migration plan

Audit date: 2026-11-03
Source: `pstack-claude` `0.9.120`
Destination: NSkills

## 1. Principles

- Import behavior, not repository structure.
- Preserve upstream copyright, license, and provenance for every imported file.
- Rewrite anything that names a host tool, model, plugin path, or hook.
- Do not port infrastructure without a demonstrated need.
- Ship a working installer and validator before expanding the skill catalog.
- Prefer one canonical file over generated copies. Render at install time.
- Keep approval gates explicit. Never import blanket autonomy.

## 2. Target architecture

```
NSkills/
  core/                 conventions, schemas, Python package
  skills/               canonical Agent Skills
  workflows/            composable execution contracts
  agents/               responsibility contracts
  rules/                stable policy fragments
  templates/            authoring templates
  tools/                repository tooling
  adapters/             harness-specific installers
    opencode/
    hermes/
    freebuff/
    generic/
  registry/             metadata index, no content copies
  scripts/              CLI entry point
  docs/                 design, audits, guides
  provenance/           import records
  tests/                registry, validator, adapter, installer tests
```

## 3. Import rules

### 3.1 PORT

Copy the body and preserve the description. Normalize frontmatter:

```yaml
name: <directory-id>
description: <original>
version: 0.1.0
license: MIT
compatibility: [opencode, hermes, freebuff, generic]
metadata:
  nskills:
    tags: [...]
    provenance: pstack:<skill>
```

Add a provenance entry with upstream repository, commit, path, copyright, and
license. Keep the upstream license files.

### 3.2 REWRITE

Do not copy the file. Write a new capability that preserves the useful decision
loop without host-specific names. Record the reference in provenance as
`derived_from` and state that it is a rewrite, not a copy.

Examples:

| Reference | NSkills capability |
| --- | --- |
| `architect` | `design-before-code` |
| `poteto-mode` | `rules/global.md` + workflows |
| `babysit` playbook | `workflows/ship-pr` |
| `thermos` | `workflows/review-change` |
| `how` | later `explain-subsystem` |
| `why` | later `investigate-rationale` |
| `principle-never-block-on-the-human` | narrowed rule in `rules/global.md` |

### 3.3 EXTEND

Port the core and add a declared contract: inputs, outputs, approvals,
dependencies, or a better failure mode. Do this after the first porting wave.

### 3.4 SKIP

Do not import. Record why in the inventory so the decision is auditable.

### 3.5 INVESTIGATE

Do not import until the dependency and expected value are measured. A large
toolchain does not enter the default install set.

## 4. Phases

### Phase 1: Audit and design (complete)

Outputs:

- `docs/audits/pstack-inventory.md`
- `docs/audits/pstack-architecture.md`
- `docs/audits/pstack-migration-plan.md`
- `docs/architecture.md`
- JSON schemas and conventions

Exit criteria: every reference component classified; canonical layout chosen;
schemas published.

### Phase 2: Core conventions and validation (complete in this milestone)

Outputs:

- `core/conventions.md`
- `core/schemas/*.schema.json`
- `core/nskills/frontmatter.py`, `model.py`, `registry.py`, `validator.py`
- `registry/registry.json`
- `nskills validate`, `nskills list`, `nskills search`, `nskills inspect`

Exit criteria: repository validates; registry matches filesystem; broken links
and missing dependencies fail with file and line.

### Phase 3: Representative port (complete in this milestone)

First wave, chosen for coverage rather than volume:

| Capability | Class | Why |
| --- | --- | --- |
| `unslop` | PORT | Writing quality, no dependencies |
| `technical-writing` | PORT | Documentation standard |
| `tdd` | PORT | Verification discipline |
| `deslop` | PORT | Code hygiene |
| `fix-ci` | PORT | External tool dependency declaration |
| `fix-merge-conflicts` | PORT | Git workflow, approval relevant |
| `bro` | PORT | Small instruction skill |
| `sharpen` | PORT | Task framing |
| `principle-prove-it-works` | PORT | Verification |
| `principle-fix-root-causes` | PORT | Debugging |
| `principle-laziness-protocol` | PORT | Minimal diff |
| `principle-model-the-domain` | PORT | Design |
| `principle-boundary-discipline` | PORT | Architecture |
| `design-before-code` | REWRITE | Replaces `architect` without model/arena coupling |

Plus four authored workflows and three authored agents. These are NSkills
originals, informed by the reference architecture.

Exit criteria: every ported skill validates; provenance exists; workflows
resolve all skill and agent references.

### Phase 4: OpenCode adapter (complete in this milestone)

- Global skills: `~/.config/opencode/skills/<id>/SKILL.md`.
- Project skills: `.opencode/skills/<id>/SKILL.md`.
- Global agents: `~/.config/opencode/agents/<id>.md`.
- Project agents: `.opencode/agents/<id>.md`.
- Global commands: `~/.config/opencode/commands/<id>.md`.
- Project commands: `.opencode/commands/<id>.md`.

Modes: symlink by default, copy with `--copy`. Workflows render a skill wrapper
plus a command. Agents render a subagent markdown file with permissions.

Exit criteria: real install into a temporary HOME followed by a file-tree
assertion; uninstall removes only managed paths; doctor detects a removed link.

### Phase 5: Hermes adapter (complete in this milestone)

- Skills: `$HERMES_HOME/skills/nskills/<id>/SKILL.md`, category `nskills`.
- Agents: `$HERMES_HOME/skills/nskills/agents/<id>/SKILL.md` wrapper, because
  Hermes has no file-based agent registry.
- Workflows: `$HERMES_HOME/skill-bundles/<id>.yaml` with dependencies and the
  workflow body as `instruction`.
- Rules and commands: unsupported, reported explicitly.

Exit criteria: bundle YAML parses; skill is discoverable by directory layout;
`hermes skills list` can see the skill when Hermes is installed. Tests cover
layout and content without invoking Hermes.

### Phase 6: Freebuff and generic adapters (complete in this milestone)

- Freebuff/global: `~/.agents/skills/<id>`.
- Freebuff/project: `.agents/skills/<id>`.
- Generic: same roots, documented as the cross-tool Agent Skills convention.
- Agents and workflows: rendered as skill wrappers because no native file
  configuration was found.
- Limitation: Freebuff has no verified local agent or command registry. Do not
  claim more.

Exit criteria: skill install works in a temporary HOME/project; limitation is in
the adapter manifest and docs.

### Phase 7: Expand the port

Order:

1. Remaining principles (all except `never-block-on-the-human` until rewritten).
2. `benchmark-checklist`, `blast-radius`, `show-me-your-work`,
   `typescript-best-practices`, `in-your-own-words`.
3. Review skills: `thermo-nuclear-review`,
   `thermo-nuclear-code-quality-review`, plus a merged review workflow.
4. PR skills: `get-pr-comments`, `make-pr-easy-to-review`,
   `what-did-i-get-done`, then `babysit` as a workflow.
5. Explanation: rewrite `how`, `why`, `teach`, `recall`.
6. Delegation: rewrite `arena`, `swarm`, `interrogate` as workflows with
   adapter-declared subagent support.
7. Verification generation: evaluate `create-verification-skill` and
   `create-formal-verification-skill` separately.

Exit criteria: each wave updates the registry, validator tests, and installed
capability matrix.

### Phase 8: Ongoing maintenance

- `nskills validate` in CI.
- `nskills doctor` after host upgrades.
- `nskills update` after repository changes.
- Provenance review for every imported file.
- A deprecation path for renamed capabilities.

## 5. Capability mapping

| Pstack concept | NSkills equivalent |
| --- | --- |
| `poteto-mode` router | `rules/global.md` + workflows + agent definitions |
| Playbook | `workflows/<id>/WORKFLOW.md` |
| Skill | `skills/<id>/SKILL.md` |
| Agent prompt fragment | `agents/<id>/AGENT.md` with a contract |
| Session-start mandate | Opt-in adapter hook, not default |
| Slash command stub | Adapter-rendered command, not committed |
| Model policy | Host-managed; no NSkills model registry |
| Per-runtime tool map | Adapter capability manifest + canonical capability names |
| `tools/generate.mjs` | `nskills validate` and adapter rendering |
| `tools/forks.json` | `provenance/pstack.json` |
| Plugin marketplace install | `nskills install --target ...` |
| Pstack namespace | Directory id; target adapter handles collisions |

## 6. Provenance policy

For each imported file:

- `provenance/pstack.json` records source repository, commit, path, class
  (`port` or `rewrite`), copyright, license, and a short change note.
- Root `NOTICE.md` lists upstream projects and licenses.
- Upstream license texts live in `licenses/`.
- Imported SKILL.md frontmatter carries `license: MIT` and
  `metadata.nskills.provenance`.
- NSkills-authored files are marked `license: MIT` with
  `metadata.nskills.provenance: original`.
- Never remove an upstream copyright notice.

## 7. Risks

| Risk | Mitigation |
| --- | --- |
| Adapter paths drift after host upgrades | Adapter manifests carry a verification date; `nskills doctor` checks paths; paths are centralized |
| Skill IDs collide with user skills | Install state records ownership; installer refuses to overwrite unmanaged paths |
| Symlinks break on Windows or sandboxed targets | `--copy` fallback and per-adapter preferred mode |
| Canonical prose drifts back to host tool names | Validator rejects a denylist of host-specific names in canonical skills |
| Ported skill references missing files | Validator resolves Markdown links and `references/` paths |
| Workflows reference uninstalled skills | Dependency resolution in installer, validation of closure |
| Provenance becomes stale | Registry and validator require a provenance key for imported capabilities |
| Too much scope | Phase order above; default install set stays small |

## 8. Deliberate non-goals

- Tracking upstream automatically.
- Reimplementing the plugin marketplace.
- Owning model selection.
- Shipping hooks by default.
- Porting the Pi extension or the statechart toolchain.
- Reproducing all 67 skills before the installer works.
- A database. A JSON registry and a JSON state file are enough.
