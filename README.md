# NSkills

One canonical library of engineering capabilities, installed into whichever
agent environment you use: OpenCode, Hermes, Freebuff, or any host that reads
the cross-tool Agent Skills convention.

Skills, workflows, and agents live once in this repository. Adapters render them
into each host's real format. The registry is metadata only; it never copies
instructions.

## Status

- Core CLI, validator, and installer: implemented with the Python 3 standard
  library only.
- Adapters: OpenCode (verified against the V2 docs), Hermes (verified against a
  local install), Freebuff (partial), generic Agent Skills (verified).
- Ported capabilities: 22 skills from `pstack-claude`, plus one rewrite
  (`design-before-code`).
- Authored capabilities: 4 workflows, 3 agents, 1 global rule set.

## Requirements

- Python 3.10 or newer.
- A target host. None of the adapters need the host at install time except
  `doctor` detection.
- Optional: `git`, `gh`, and the host CLI for the workflows that use them.

No third-party Python packages, no database, no build step.

## Quick start

```bash
# What is available?
python3 scripts/nskills list

# What does one capability do?
python3 scripts/nskills inspect design-before-code

# Install a workflow and its dependencies into OpenCode
python3 scripts/nskills install implement-feature --target opencode

# Install everything into this project instead of globally
python3 scripts/nskills install --all --target generic --scope project

# Check what is installed and whether the host is present
python3 scripts/nskills doctor

# Remove what you installed
python3 scripts/nskills uninstall implement-feature --target opencode
```

`install` resolves skill and agent dependencies by default. `--no-deps` skips
them and leaves the record incomplete, which `doctor` reports.

See [docs/quick-start.md](docs/quick-start.md) for a guided first run and
[docs/adapter-support.md](docs/adapter-support.md) for the exact path each
adapter writes.

## Commands

| Command | Purpose |
| --- | --- |
| `list` | List capabilities from the registry; filter by type, target, or installed |
| `search QUERY` | Search IDs, names, descriptions, and tags |
| `inspect ID` | Show metadata, dependencies, install state, and body |
| `install ID... --target T` | Install capabilities and dependencies |
| `uninstall ID... --target T` | Remove a managed install; `--force` keeps modified files in a backup |
| `sync` | Restore missing files for recorded installs without overwriting existing paths |
| `update [ID...]` | Reinstall managed capabilities from the current repository |
| `doctor` | Check adapters, required tools, missing paths, and drift |
| `validate [--write]` | Validate the repository and registry |
| `registry build` | Rebuild `registry/registry.json` from the filesystem |
| `targets` | Show adapters, support, detection, and global roots |

`install` and `uninstall` require `--target`. Use `--scope project` to write into
the current directory (or `--project DIR`). `--copy` copies instead of linking;
`--symlink` overrides an adapter that prefers copies. `--force` moves an
unmanaged destination to a timestamped backup before replacing it.

## Layout

```text
core/                 conventions, schemas, and the Python package
skills/               canonical Agent Skills
workflows/            execution contracts
agents/               responsibility contracts
rules/                stable policy fragments
templates/            authoring templates
adapters/             one directory per host
registry/registry.json metadata index
scripts/nskills       CLI entry point
tools/import_pstack.py first-wave importer, kept for the audit trail
provenance/           import records
docs/                 architecture, audits, guides
tests/                unit and integration tests
```

## What is in the library

Skills:

- Writing and cleanup: `unslop`, `technical-writing`, `deslop`, `bro`,
  `sharpen`.
- Verification: `tdd`, `benchmark-checklist`.
- Design: `design-before-code`.
- Delivery: `fix-ci`, `fix-merge-conflicts`.
- Principles: the 13 imported `principle-*` reference leaves.

Workflows:

- `implement-feature`: framing, design, failing tests, implementation, review.
- `fix-bug`: reproduce, root cause, regression test, fix, verify.
- `review-change`: correctness, scope, maintainability, test quality.
- `ship-pr`: checks, conflicts, final review, handoff before merge.

Agents:

- `implementer`, `reviewer`, `researcher`.

Rules:

- `rules/global.md`: verification, reading, smallest change, approval, state,
  reporting, and hygiene.

## Canonical vocabulary

Canonical instructions never name host tools. They use `read`, `search`, `edit`,
`shell`, `delegate`, `web`, `ask-human`, `load-skill`, and `track`. Adapters map
those capabilities to the host. The validator rejects host-specific tokens in
canonical bodies.

See [core/conventions.md](core/conventions.md) for the full contract.

## Validation

```bash
python3 scripts/nskills validate --write
python3 -m unittest discover -s tests
```

`validate --write` rebuilds the registry before checking. Without a registry,
validation fails on purpose.

The validator checks metadata, IDs, versions, tags, provenance, relative links,
supporting paths, dependency closure, cycles, workflow and agent sections,
compatibility against real adapter manifests, and registry freshness.

## Adapter support

| Capability | OpenCode | Hermes | Freebuff | Generic |
| --- | --- | --- | --- | --- |
| Skills | native | native | Agent Skills | Agent Skills |
| Workflows | skill + command | skill bundle | skill wrapper | skill wrapper |
| Agents | native markdown | instruction skill | skill wrapper | skill wrapper |
| Rules | not installed | not installed | not installed | not installed |

Freebuff is marked `partial`: the Agent Skills path was verified, but loading
inside a live session was not. See [docs/adapter-support.md](docs/adapter-support.md).

## Provenance

Imported material keeps its upstream MIT copyright and license. See
[NOTICE.md](NOTICE.md), `licenses/`, and `provenance/pstack.json`.

## Non-goals

- Choosing models for you.
- Injecting a session-start mandate.
- Editing `AGENTS.md` or other host instruction files automatically.
- A plugin marketplace or a database.
- Porting the upstream statechart toolchain or Pi extension.

## License

MIT. Imported portions retain their upstream copyright; see `NOTICE.md`.
