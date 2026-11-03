# Rules

Rules are short, stable policy fragments. They are not skills and they are not
installed by default.

- `global.md`: the baseline that applies to every capability.

## Authoring

- One topic per file, kebab-case filename.
- State the behavior, not the rationale. Put rationale in a sentence after the
  rule when it is not obvious.
- Keep each rule short enough to read in one sitting.
- No host tool names, model IDs, or installation paths.

## Installation

The installer does not write rules into host config. An adapter may render a
rule into an instruction file only when the operator asks for it, and it must
never edit an existing instruction file automatically.

When a rule is useful in a host, copy the relevant text into the project's
instruction file deliberately, or install it as a skill and load it explicitly.
