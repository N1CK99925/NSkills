# NOTICE

NSkills contains original work and material imported from
[pstack-claude](https://github.com/michael-denyer/pstack-claude), which is
itself a port of MIT-licensed Cursor plugin work.

NSkills-authored files are (c) 2026 NSkills contributors under the
[MIT license](LICENSE).

## Imported material

| NSkills capability | Upstream | Copyright | License | License file |
| --- | --- | --- | --- | --- |
| `skills/unslop`, `skills/technical-writing`, `skills/tdd`, `skills/bro`, `skills/sharpen`, `skills/benchmark-checklist`, `skills/principle-*`, `skills/design-before-code/references/design-red-flags.md` | [cursor/plugins/pstack](https://github.com/cursor/plugins) via `pstack-claude` | (c) 2026 Lauren Tan | MIT | [LICENSE-pstack](licenses/LICENSE-pstack) |
| `skills/deslop`, `skills/fix-ci`, `skills/fix-merge-conflicts` | [cursor/plugins/cursor-team-kit](https://github.com/cursor/plugins) via `pstack-claude` | (c) 2026 Cursor | MIT | [LICENSE-cursor-team-kit](licenses/LICENSE-cursor-team-kit) |

`skills/design-before-code` is a rewrite of the upstream `architect` skill,
not a copy. Its reference file `design-red-flags.md` is a direct port.

The exact source commit, path, and change note for every imported file is in
[`provenance/pstack.json`](provenance/pstack.json).

## What changed

- Frontmatter normalized to the NSkills contract: version, license,
  compatibility, tags, provenance.
- Host-specific tool names, model policy, session hooks, and platform mapping
  instructions removed from imported bodies.
- One declared substitution in `principle-prove-it-works`: a reference to a
  skill that was not imported was replaced with a plain statement.
- `design-before-code` replaces `architect` without the arena/model/runtime
  coupling.

No upstream copyright notice was removed.
