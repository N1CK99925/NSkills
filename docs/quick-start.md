# Quick start

A guided first run. Everything works from the repository root.

## 1. Check the repository

```bash
python3 scripts/nskills validate
python3 -m unittest discover -s tests
```

Validation reads the registry. If it says the registry is stale or missing:

```bash
python3 scripts/nskills validate --write
```

## 2. Look at what is available

```bash
python3 scripts/nskills list
python3 scripts/nskills search verification
python3 scripts/nskills inspect implement-feature
python3 scripts/nskills targets
```

`list` marks installed targets with `*`. `targets` shows each adapter's status,
supported capability types, detection result, and global root.

## 3. Install into a host

OpenCode, globally:

```bash
python3 scripts/nskills install implement-feature --target opencode
```

This installs the workflow, all of its skill dependencies, and its two agents.
Check the result:

```bash
python3 scripts/nskills doctor
```

Hermes, globally:

```bash
python3 scripts/nskills install implement-feature --target hermes
```

Hermes gets a skill bundle at `$HERMES_HOME/skill-bundles/implement-feature.yaml`
and skills under `$HERMES_HOME/skills/nskills/`. Hermes copies by default
because it warns about skills that resolve outside its trusted root.

Generic Agent Skills, in this project:

```bash
python3 scripts/nskills install implement-feature --target generic --scope project
```

This writes `.agents/skills/` beneath the current directory. Pass
`--project DIR` to target another directory.

## 4. Use a workflow

OpenCode:

```text
/implement-feature Add a --dry-run flag to the export command
```

The command loads `workflow-implement-feature`, whose body names the steps,
skills, and agents. The workflow delegates the sketch and implementation to the
`implementer` agent and the review pass to the `reviewer` agent.

Hermes:

```text
/implement-feature Add a --dry-run flag to the export command
```

The bundle loads the six skills and prepends the workflow body.

Generic hosts without commands:

```text
Load the workflow-implement-feature skill and follow it for: Add a --dry-run flag to the export command.
```

## 5. Change something and update

Edit a canonical skill under `skills/`. Rebuild and validate:

```bash
python3 scripts/nskills validate --write
python3 scripts/nskills update implement-feature --target opencode
```

Symlinked installs already see the change; copies need `update`. `doctor`
reports drift for copied files.

## 6. Remove an install

```bash
python3 scripts/nskills uninstall implement-feature --target opencode
```

Uninstall removes only paths recorded by NSkills. A file modified outside
NSkills is left in place and the command fails unless `--force` is passed, in
which case the removed files are kept under
`$XDG_STATE_HOME/nskills/backups/uninstall-*`.

## Common situations

**The destination already exists and is not managed.**
The installer refuses. Use `--force` to move the existing path into
`$XDG_STATE_HOME/nskills/backups/install-*` first, or remove it yourself.

**An installed file went missing.**
`doctor` reports it. Restore it with `sync`. `sync` writes only missing paths,
so a locally modified file is left alone.

**A required tool is missing.**
Installation still succeeds. `doctor` reports the missing tool named in the
capability's `depends.tools`.

**Two targets read the same directory.**
Freebuff and generic both use `~/.agents/skills`, and OpenCode also reads that
path as a compatibility source. Install into one of them to avoid duplicate
state. OpenCode's own root is `~/.config/opencode/skills`.

**A capability should not appear in the model's skill list.**
The importer marks reference leaves with `user-invocable: false`. OpenCode does
not interpret that field. Either accept the advertisement or install only the
skills you want. There is no hidden-copy transformation in phase one.
