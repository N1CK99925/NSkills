# Pstack architecture

Audit date: 2026-11-03
Scope: `pstack-claude` at version `0.9.120`, excluding `.git`.

## 1. One-paragraph model

Pstack is a Claude Code plugin that ports Lauren Tan's Cursor skill stack to
several agent harnesses. A single `plugins/pstack/skills/` tree holds Agent
Skills. A generator (`tools/generate.mjs`) stamps shared facts into per-runtime
manifests, Codex prompt stubs, model sections, and tool-mapping preambles. Hooks
inject a routing mandate and a model override sheet at session start. A large
`poteto-mode` skill acts as the router, style guide, and playbook index. The Pi
harness gets a TypeScript extension that reimplements agents, background
scheduling, path-scoped skills, and worktrees.

The system is optimized for one maintainer tracking an upstream repository. It
is not a general installer, and it is not harness-neutral in execution.

## 2. Layering

```
cursor/plugins upstream
        |
        v
tools/sync.mjs -- forks.json, substitutions.json
        |
        v
plugins/pstack/skills/*          canonical-ish Agent Skills
plugins/pstack/agents/*          Claude prompt fragments
plugins/pstack/hooks/*           session-start + pre-tool policy
        |
        +--> .claude-plugin/plugin.json + hooks.json
        +--> .codex-plugin/plugin.json + prompts/*.md + codex-hooks.json
        +--> .muse-plugin/plugin.json + PowerShell hook
        +--> .github/plugin/plugin.json + copilot hooks
        +--> pi/*.ts + package metadata
        +--> .agents/plugins/marketplace.json
```

`tools/generate.mjs` is the synchronization layer. Its declared sources of
truth are:

- `VERSION` and `CHANGES.md`.
- Skill frontmatter (`name`, `description`).
- `docs/reference.md`'s slash-command table.
- `plugins/pstack/models.json`.
- Per-runtime tool maps.
- `DRIVER_PLAYBOOKS`, licenses, notices, and portable agent copies.

It writes or validates every derived copy. CI runs it with `--check`, so a
stale copy fails the build. This is the strongest engineering idea in the
reference. It is also the source of most complexity: 1,084 lines of generator
plus runtime validators, with Bun and TypeBox dependencies.

## 3. Skill anatomy

A normal skill is a directory with `SKILL.md`. Frontmatter is the Agent Skills
subset: `name`, `description`, sometimes `user-invocable: false`. Some skills add
`paths:` globs for automatic loading. Supporting files live in `references/`,
`scripts/`, and `assets/`.

The body is written for Claude Code first. Skills call Claude tool names
directly: `Skill`, `Agent`, `AskUserQuestion`, `TaskCreate`, `TaskUpdate`,
`Bash`, `Read`. Where a skill must run elsewhere, it links to a runtime mapping
file:

- `poteto-mode/references/codex-tools.md`
- `poteto-mode/references/pi-tools.md`
- `poteto-mode/references/copilot-tools.md`
- `poteto-mode/references/muse-tools.md`

This is a documentation-level adapter. It keeps one copy of the prose but
requires the model to translate tool calls at runtime. The translation is not
executable contract, and it cannot be validated automatically.

## 4. Routing and execution

Execution has four layers.

1. **Session hook.** `SessionStart` injects `session-start-context.md` and the
   user's model sheet. The mandate tells the agent to use `poteto-mode` for
   non-trivial work and to honor model roles.
2. **Router skill.** `poteto-mode` holds the non-negotiables, autonomy rules,
   subagent defaults, reply style, principle index, and playbook index. It
   selects a playbook and tells the agent to copy the playbook steps into a
   todo list.
3. **Playbook.** One of 20 files under `poteto-mode/playbooks/` defines a task
   shape: investigation, bug fix, feature, refactor, shipping, and so on.
4. **Leaf skill.** A specific skill (`tdd`, `architect`, `unslop`) supplies the
   instructions for one step.

The router is a skill rather than a command, so it can be invoked by name and
can also be loaded by a subagent. The agent definitions are prompt fragments
that point back at the router. There is no machine-readable orchestration
graph. The graph exists only as prose in `poteto-mode` and its playbooks.

## 5. Per-harness integration

### Claude Code

Native plugin. Skills are namespaced `pstack:<name>`, agents `pstack:<agent>`.
The `SessionStart` hook is the only automatic behavior. Installation is through
the plugin marketplace.

### Codex

Shared skills plus generated prompt stubs. Each stub is one prompt that names a
skill. Codex has no plugin agent namespace, so the tool map explains how to
dispatch. Hooks inject the same mandate.

### GitHub Copilot

Shared skills plus prompt stubs and a pre-tool hook. The pre-tool hook approves
reads of the plugin's own files, validates strict script runs, and denies agent
dispatch on a model missing from the override sheet. This is the most
harness-specific behavior in the repository.

### Muse

Shared skills, a plugin manifest, and a PowerShell session hook on Windows. Muse
has its own model IDs and workflow-child effort semantics.

### Pi

A full extension, not a documentation mapping. It implements agent dispatch,
model discovery, background scheduling, path-scoped skill activation, and
worktree helpers. It is effectively a second product surface.

### OpenCode

Named in the manifest keywords, the generator comments, and the README. No
OpenCode adapter, manifest, command stubs, or hook exists in this checkout. The
skills tree is compatible because OpenCode reads Agent Skills, but installation
and agent/command support are unverified.

## 6. Duplicated capabilities inside the reference

| Duplication | Where | Effect |
| --- | --- | --- |
| PR shepherding | `babysit` skill vs `playbooks/babysit.md` vs `fix-ci`, `get-pr-comments` | Two routing paths with overlapping behavior; the router explicitly prefers the playbook, but the skill remains discoverable on the same words |
| Review | `thermo-nuclear-review`, `thermo-nuclear-code-quality-review`, `thermos`, `interrogate`, `no-comments`, `blast-radius` | Six review-shaped skills with different scope and dispatch rules |
| Explanation | `how`, `why`, `teach`, `recall`, `bro`, `in-your-own-words`, `ketchup` | Overlapping intents, distinguished mainly by prose |
| Planning | `architect`, `figure-it-out`, `sharpen`, `arena`, `swarm` | Design and fan-out ideas repeated across skills |
| Autonomy policy | `poteto-mode` Autonomy section, `principle-never-block-on-the-human`, playbooks | Contradictory defaults unless the reader tracks scope |
| Model policy | `models.json`, `poteto-mode` Models section, each model-consuming skill, `setup-pstack`, hooks, runtime maps | One policy spread over a dozen generated copies |
| Tool mappings | Four runtime mapping files plus generated per-skill preambles | Same translation repeated per harness and per skill |
| Playbook steps | Copied verbatim into todo lists, then repeated in CHANGES and docs | Intentional, but no machine check that a copied step still exists |
| Skill catalog | `docs/reference.md`, `user-invocable` flags, Codex prompt stubs, manifests | Four sources that the generator reconciles |
| License/notice copies | Root notice plus portable copies under `poteto-mode/references/licenses/` | Necessary for the skills-only distribution, but easy to drift |
| Statechart fixture corpus | 374 support files, 3.9 MB, with generated `.out`, `.dot`, `.cfg` | Test data dwarfs the skill |

The duplication is mostly deliberate: generated copies keep each harness
self-contained. NSkills should keep the single-source principle but avoid
duplicating generated content into the repository. Adapters can render at
install time instead.

## 7. Dependency and failure behavior

- The generator fails on stale derived files. Good.
- The validator walks Markdown and checks links and layout. Good.
- Runtime failures are mostly soft: missing optional tools (TLA+, Java, `gh`)
  are described in prose, not declared as machine-readable dependencies.
- Model override parsing has multiple fallbacks. When a model slug is rejected,
  skills tell the agent to fall back in a prescribed order. This is robust in
  prose and impossible to test centrally.
- Hook failures can be silent. `pre-tool-use.sh` deliberately exits zero on
  every path so Copilot does not deny all calls after a hook bug.
- There is no install state, no version tracking per installed skill, and no
  uninstall path outside the host plugin manager.
- Skills can reference sibling files; the reference is relative to the skill
  directory. There is no check that a `references/` file used by a workflow is
  installed with it.

## 8. Security and approval posture

The reference is aggressive about autonomy:

- "Use any MCP tool."
- Reversible work and external actions proceed without asking.
- Always pause only for force-push, deploy, data deletion, and customer
  messages.
- `principle-never-block-on-the-human` tells the agent not to ask on reversible
  work.

This is coherent for the author's workflow. It is not a safe default for a
multi-harness personal system. NSkills keeps the bias toward action but makes
approval checkpoints explicit in each workflow, and never lets a skill grant
itself new permissions.

Hooks also run shell and awk code at session start. NSkills does not install
hooks by default.

## 9. What transfers cleanly

- Agent Skills directory convention.
- Principle leaves as small, composable references.
- The idea of a router, but expressed as workflows rather than a mega-skill.
- The idea of a single source for metadata, but implemented as validation, not
  generated copies.
- Provenance discipline: `NOTICE.md`, per-upstream license files, and a record
  of what changed.
- The distinction between a task shape (playbook) and a technique (skill).

## 10. What does not transfer

- Model policy. NSkills should inherit the host's model.
- Session-start mandate injection.
- Claude tool names in canonical prose.
- Generated per-runtime prompt stubs committed to the repository.
- Bun, TypeBox, and the runtime matrix.
- The Pi extension and the statechart toolchain.
- A 174-line entry-point skill that duplicates routing, style, and policy.

## 11. Architectural conclusions for NSkills

1. Canonical capabilities must be executable contracts, not prose with implicit
   conventions. Each skill, workflow, and agent gets validated frontmatter.
2. Harness translation belongs in adapters, at install time. Canonical prose
   names capabilities, not host tools.
3. Workflows replace the router and playbooks. A workflow declares inputs,
   steps, skill dependencies, agents, approvals, outputs, failure behavior, and
   completion criteria.
4. The registry is metadata only. It indexes files; it does not copy them.
5. Installation must be stateful: know what was installed, where, at what
   version, and how to remove or update it. Symlinks by default, copies when
   the target cannot follow links.
6. Validation must cover metadata, references, dependency closure, workflows,
   agents, adapter support, and real installation in a temporary root.
7. No global hooks or mandate injection in phase one. Opt-in only.
