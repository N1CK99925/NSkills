# Pstack inventory

Audit date: 2026-11-03
Reference: `/home/nick/Documents/GitHub/pstack-claude` (read-only)
Reference version: `0.9.120` (plugin manifests), 788 tracked files.

This inventory classifies every component family in the reference repository. The
classification is about suitability for NSkills, not the quality of the upstream
work.

- **PORT**: useful and suitable with metadata and harness-neutral cleanup.
- **REWRITE**: valuable behavior, unsuitable implementation or coupling.
- **EXTEND**: worth keeping and improving.
- **SKIP**: not useful for NSkills.
- **INVESTIGATE**: cost, dependency, or behavior is not yet clear.

## 1. Repository shape

| Path | What it is | Files | Classification |
| --- | --- | ---: | --- |
| `plugins/pstack/skills/` | 67 Agent Skills: 43 public and 24 `principle-*` reference leaves | 513 | PORT / REWRITE / SKIP per skill |
| `plugins/pstack/agents/` | Four markdown subagent definitions | 4 | REWRITE / PORT |
| `plugins/pstack/hooks/` | Session-start context injection and Copilot pre-tool checks for Claude, Codex, Copilot, Muse | 17 | REWRITE |
| `plugins/pstack/pi/` | 1,951 lines of TypeScript implementing a Pi harness adapter | 13 | INVESTIGATE / REWRITE |
| `plugins/pstack/.claude-plugin/` | Claude Code plugin manifest | 2 | REWRITE |
| `plugins/pstack/.codex-plugin/` | Codex manifest plus 43 generated prompt stubs | 44 | REWRITE |
| `plugins/pstack/.muse-plugin/` | Muse plugin manifest | 1 | REWRITE |
| `plugins/pstack/.github/plugin/` | GitHub Copilot plugin manifest | 1 | REWRITE |
| `.claude-plugin/marketplace.json` | Claude plugin marketplace entry | 1 | PORT concept |
| `.agents/plugins/marketplace.json` | Cross-agent marketplace entry | 1 | PORT concept |
| `tools/` | Generator, validator, upstream sync, fork registry, runtime matrix | 10 files, 204 KB | REWRITE / SKIP |
| `docs/` | Reference manual and Pi equivalence notes | 2 | PORT structure |
| `.github/workflows/` | CI and security checks | 2 | EXTEND |
| `.github/scripts/statechart-watchdog.sh` | Watchdog for generated statechart artifacts | 1 | SKIP |
| `lean/` | Lean model of a watch/poll loop | 7 | SKIP |
| `tests/` | 728 KB of fixture and oracle data, mostly statechart | many | SKIP |
| `assets/` | Images and image prompts | 4 | SKIP |
| `CHANGES.md` | 208 KB release log | 1 | SKIP |
| `NOTICE.md`, `NOTICE-skills.md`, `LICENSE*` | Provenance and licenses | 5 | PORT |
| `bun.lock`, `bunfig.toml`, `package.json` | Bun workspace and dependencies | 3 | SKIP |

The repository is a distribution and generation project, not a small skill
collection. Most of the engineering effort is in cross-runtime generation and
validation, plus one very large statechart tool.

## 2. Skills

### 2.1 Public workflow skills

| Skill | Purpose | Classification | NSkills treatment |
| --- | --- | --- | --- |
| `architect` | Design types and module shape before code | REWRITE | Replace with `design-before-code`; remove model-sheet, arena, and platform-mapping coupling |
| `arena` | Run N candidates and graft the best | REWRITE | Model as a workflow after the core installer exists; subagent fan-out is harness-specific |
| `automate-me` | Draft a personal `-mode` skill from transcripts | REWRITE | Requires transcript discovery and plugin-dev skill; later optional tool |
| `babysit` | Drive a PR to mergeable | EXTEND | Port as a workflow after `fix-ci` and review skills are installed |
| `benchmark-checklist` | Vet performance measurements | PORT | Harness-neutral |
| `blast-radius` | Find what a change could break | PORT | Harness-neutral; depends on running real code |
| `bro` | Restate plainly | PORT | Trivial and useful |
| `correct` | Turn repeated agent mistakes into permanent checks | EXTEND | Strong idea; depends on repo conventions |
| `create-formal-verification-skill` | Generate a TLA+/Lean/Kani project skill | INVESTIGATE | External toolchain and huge statechart precedent; later |
| `create-verification-skill` | Generate a project verification driver | EXTEND | Useful, but needs template design |
| `deslop` | Remove AI code slop | PORT | Harness-neutral |
| `figure-it-out` | Design a bespoke rigorous playbook | REWRITE | Overlaps NSkills workflows; extract the decision-loop idea |
| `fix-ci` | Fix failing PR checks iteratively | PORT | Depends on `gh`; declare tool dependency |
| `fix-merge-conflicts` | Resolve conflicts and validate | PORT | Harness-neutral |
| `get-pr-comments` | Fetch and summarize review comments | PORT | Depends on `gh` |
| `how` | Explain a subsystem | REWRITE | Useful; remove parallel-MCP and model policy |
| `interrogate` | Multi-model adversarial review | REWRITE | Depends on subagent fan-out and model panels |
| `in-your-own-words` | Restate user goals | PORT | Trivial |
| `ketchup` | Catch the user up | REWRITE | Depends on chat history and visual output |
| `ketchup-video` | Video catch-up | SKIP | Heavy media toolchain |
| `maintain-formal-verification-skill` | Keep formal model in sync | INVESTIGATE | External toolchain |
| `maintain-verification-skill` | Keep verification skill honest | EXTEND | Later |
| `make-pr-easy-to-review` | Clean history and annotate a PR | PORT | Harness-neutral; git operations need approval |
| `no-comments` | Run `comment-sicko` and fix findings | REWRITE | Agent dependency is Claude-specific |
| `poteto-help` | Routing help | REWRITE | Replace with `nskills` CLI and a short routing guide |
| `poteto-mode` | Entry point, 174-line style and routing mandate | REWRITE | Split into rules, workflows, and agent definitions |
| `recall` | Reconstruct recent work context | REWRITE | Depends on transcript locations per harness |
| `reflect` | Turn a transcript into skill edits | EXTEND | Needs a harness-neutral transcript input |
| `setup-pstack` | Choose models per role | SKIP | NSkills does not own model policy |
| `sharpen` | Deepen a task before rewriting the prompt | PORT | Harness-neutral |
| `show-me-your-work` | TSV decision trail | PORT | Strong operational value |
| `statechart` | TLA+ model checking plus Mermaid statechart | SKIP | 374 support files, JVM, TLA+, Graphviz; separate project |
| `swarm` | Fan out N workers and collect one report | REWRITE | Harness-specific; later workflow |
| `tdd` | Failing test before fix | PORT | Harness-neutral |
| `teach` | Explain work using `how` and `why` | REWRITE | Depends on two rewrites |
| `technical-writing` | Layered writing standard | PORT | Harness-neutral |
| `thermo-nuclear-code-quality-review` | Strict maintainability audit | EXTEND | Keep rubric, rewrite dispatch |
| `thermo-nuclear-review` | Security and correctness diff audit | EXTEND | Keep rubric, rewrite dispatch |
| `thermos` | Run both reviews and synthesize | REWRITE | Becomes a review workflow |
| `typescript-best-practices` | TypeScript guidance | PORT | Harness-neutral |
| `unslop` | Remove AI writing tells | PORT | Harness-neutral, stable rule ids |
| `what-did-i-get-done` | Summarize authored commits | PORT | Harness-neutral |

### 2.2 Principle skills

All 24 are short, harness-neutral reference leaves. They are the strongest part
of the reference for NSkills.

| Skill | Classification | Note |
| --- | --- | --- |
| `principle-attack-the-premise` | PORT | Debugging discipline |
| `principle-boundary-discipline` | PORT | Validation at boundaries |
| `principle-build-the-lever` | PORT | Build tools instead of manual sweeps |
| `principle-encode-lessons-in-structure` | PORT | Turn corrections into checks |
| `principle-exhaust-the-design-space` | PORT | Competing prototypes |
| `principle-experience-first` | PORT | Product tradeoffs |
| `principle-explain-the-number` | PORT | Measurement discipline |
| `principle-fix-root-causes` | PORT | Debugging discipline |
| `principle-foundational-thinking` | PORT | Data structures before logic |
| `principle-guard-the-context-window` | PORT | Context routing |
| `principle-laziness-protocol` | PORT | Smallest diff |
| `principle-make-operations-idempotent` | PORT | Crash-safe commands |
| `principle-migrate-callers-then-delete-legacy-apis` | PORT | No compatibility layer |
| `principle-minimize-reader-load` | PORT | Traceability |
| `principle-model-the-domain` | PORT | Structure over conditionals |
| `principle-never-block-on-the-human` | REWRITE | Contradicts NSkills approval gates unless narrowed to reversible work |
| `principle-outcome-oriented-execution` | PORT | Converge on target architecture |
| `principle-prove-it-works` | PORT | Direct verification |
| `principle-redesign-from-first-principles` | PORT | New requirements |
| `principle-separate-before-serializing-shared-state` | PORT | Concurrency |
| `principle-sequence-verifiable-units` | PORT | Small verified units |
| `principle-subtract-before-you-add` | PORT | Delete first |
| `principle-test-behavior-not-implementation` | PORT | Behavioral tests |
| `principle-type-system-discipline` | PORT | Types |

## 3. Agents

| Agent | Purpose | Classification | Note |
| --- | --- | --- | --- |
| `poteto-agent` | Delegate that reads `poteto-mode` and applies its style | REWRITE | Canonical `implementer` / `researcher` replace it |
| `comment-sicko` | Hostile comment reviewer | REWRITE | Persona is fun; make a normal `reviewer` mode |
| `thermo-nuclear-review-subagent` | Security/correctness reviewer | PORT rubric / REWRITE wrapper | Agent body is harness-neutral enough |
| `thermo-nuclear-code-quality-review-subagent` | Maintainability reviewer | PORT rubric / REWRITE wrapper | Same |

Agent definitions in the reference are prompt fragments, not capability
contracts. They do not declare allowed tools, inputs, outputs, or delegation
limits in a machine-readable way. NSkills adds those fields.

## 4. Hooks

| File | Purpose | Classification |
| --- | --- | --- |
| `hooks/hooks.json` | Claude `SessionStart` injection | SKIP as-is |
| `hooks/codex-hooks.json` | Codex session-start | SKIP as-is |
| `hooks/copilot-hooks.json` | Copilot session-start and pre-tool checks | SKIP as-is |
| `hooks/session-start.sh` | Resolve runtime sheet and inject routing mandate | REWRITE |
| `hooks/session-start.ps1` | Windows Muse variant | SKIP |
| `hooks/session-start-context.md` | Mandate injected into every session | REWRITE |
| `hooks/session-start-copilot*.md` | Copilot-specific mandates | SKIP |
| `hooks/session-start-muse*.md` | Muse-specific mandates | SKIP |
| `hooks/pre-tool-use.sh` | Copilot permission bridge | SKIP |
| `hooks/*.awk` | JSON escaping, sheet parsing, script contracts, pre-tool policy | SKIP |
| `hooks/copilot-context.awk` | Copilot model-sheet injection | SKIP |

Hooks are where the reference couples most tightly to harnesses and model
policy. NSkills only adds an adapter hook when a target needs one, keeps it
opt-in, and never injects a global routing mandate.

## 5. Commands and invocation

The reference has no separate `commands/` tree. Invocation differs per harness:

| Harness | Skills | Slash commands | Agents | Notes |
| --- | --- | --- | --- | --- |
| Claude Code | plugin `skills/` | `/pstack:<name>` | plugin `agents/` with `pstack:` namespace | Hooks inject routing |
| Codex | shared `skills/` | 43 generated prompt stubs in `.codex-plugin/prompts/` | tool mapping file | Marketplace install |
| Muse | shared `skills/` | each user-invocable skill | Workflow children | PowerShell on Windows |
| GitHub Copilot | shared `skills/` | prompt stubs | agent mapping | Pre-tool hook |
| Pi | shared `skills/` plus TypeScript extension | `/skill:<name>` | extension-provided agents | 1,951 lines of adapter code |
| OpenCode | claimed in keywords and generator notes | none shipped | none shipped | No adapter is present in this checkout |

The OpenCode claim is documentation-only in the audited tree. NSkills implements
and tests it.

## 6. Tools and generation

| Tool | Purpose | Classification | Note |
| --- | --- | --- | --- |
| `tools/generate.mjs` | Stamp versions, model policy, command stubs, tool preambles; validate cross-file contracts | REWRITE | The single-source idea is good; 1,084 lines and Bun/TypeBox are too much for phase one |
| `tools/validate-skills.mjs` | Parse frontmatter, walk Markdown, validate links and layout | REWRITE | Adopt the checks, replace the implementation |
| `tools/plugin.mjs` | Shared paths and Markdown helpers | REWRITE | Fold into validator |
| `tools/runtimes.mjs` | Runtime matrix and packaging validators | REWRITE | NSkills uses adapter manifests |
| `tools/sync.mjs` | Sync upstream and apply forks | SKIP | NSkills is independent, not a tracking fork |
| `tools/upstream.json` | Upstream commit and excluded paths | SKIP | Keep a provenance snapshot instead |
| `tools/forks.json` | Files diverged from upstream and why | PORT concept | Becomes `provenance/` records |
| `tools/substitutions.json` | Token rewrites per harness | REWRITE | Too brittle; canonical writing removes the need |
| `tools/pi-package.mjs`, `tools/typecheck-pi.mjs` | Pi package assembly and typecheck | SKIP | No Pi target in phase one |

Important dependencies: Bun, TypeBox, Node, `gh`/`glab`, TLA+ tools, Java,
Graphviz, Mermaid, ImageMagick/ffmpeg for ketchup-video, and the Pi coding-agent
package. NSkills phase one uses Python 3 standard library only.

## 7. Rules and instructions

There is no `rules/` directory. Rules are embedded in:

- `poteto-mode/SKILL.md`: non-negotiables, autonomy, subagent policy, reply
  style, comments, model routing.
- `hooks/session-start-context.md`: mandatory routing at session start.
- `agents/poteto-agent.md`: delegation behavior.
- Per-runtime mapping references: `codex-tools.md`, `pi-tools.md`,
  `copilot-tools.md`, `muse-tools.md`.

Classification: REWRITE. The content is valuable; the placement makes a single
session carry a large mandate and makes behavior hard to compose. NSkills moves
stable guidance into `rules/` and task behavior into workflows.

## 8. Templates and examples

The reference ships references and playbooks rather than templates:

- `poteto-mode/playbooks/*.md`: 20 operational playbooks.
- `poteto-mode/references/*`: tool maps, model sheet, bugbot triage, agent and
  license copies.
- `architect/references/*`: runner prompt, design red flags, rationale template.
- `create-verification-skill/references/feature-map-example/`.
- `templates/` package in `statechart`.

Classification: EXTEND. NSkills adds templates for skills, workflows, agents,
and registry entries, and keeps reference files beside the capability that uses
them.

## 9. Packaging and installation

| Mechanism | Classification | NSkills response |
| --- | --- | --- |
| Claude plugin marketplace | REWRITE | OpenCode, Hermes, Freebuff, and generic installers instead |
| Codex `.agents/plugins/marketplace.json` | REWRITE | Generic `.agents/skills` installation |
| Manifest-per-harness with duplicated version | REWRITE | One registry plus per-install state |
| Skill directories with supporting files | PORT | Same convention |
| Generated prompt stubs | REWRITE | Adapters render commands only when the target supports them |
| Session-start hook | SKIP | No global injection by default |
| Symlinked skill trees | PORT | Default install mode; copy fallback |

## 10. Documentation

| Document | Classification | Use |
| --- | --- | --- |
| `README.md` | REWRITE | Positioning, install, first task |
| `docs/reference.md` | PORT structure | Command table becomes registry-driven CLI docs |
| `docs/pi-equivalence.md` | SKIP | Pi not targeted |
| `CONTEXT.md` | REWRITE | Architecture notes |
| `CONTRIBUTING.md` | SKIP | Upstream release process |
| `CHANGES.md` | SKIP | Historical |
| `NOTICE*.md`, `LICENSE*` | PORT | Required attribution for imported material |

## 11. External dependencies found

- Node and Bun for tooling.
- TypeBox for schema validation in the generator.
- `gh` and `glab` for PR skills.
- TLA+, Java, Graphviz, Mermaid for `statechart`.
- ffmpeg and image tooling for `ketchup-video`.
- Pi coding-agent package for the Pi extension.
- Runtime-specific environment variables and plugin caches.

NSkills core has no third-party Python dependency. Optional tools are declared
on each capability and checked by `nskills doctor`.

## 12. Inventory conclusions

1. The portable core is the 24 principles plus roughly 20 harness-neutral
   workflow skills.
2. The largest maintenance cost is not the skills. It is the generator, hook
   matrix, Pi adapter, and statechart toolchain.
3. The reference is a fork that tracks upstream. NSkills should import a
   snapshot with provenance and then evolve independently.
4. OpenCode is claimed but not implemented in this checkout. Hermes and
   Freebuff are absent. NSkills must implement those adapters and state clearly
   what each one supports.
5. The most valuable structural change is to separate reusable behavior
   (skills), orchestration (workflows), responsibility contracts (agents), and
   stable policy (rules).
