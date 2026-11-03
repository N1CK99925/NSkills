---
name: Review Change
description: Review a diff or branch for correctness, scope, maintainability, and test quality, then report findings by severity.
version: 0.1.0
license: MIT
compatibility: [opencode, hermes, freebuff, generic]
inputs:
  - A diff, branch, commit range, or working tree
  - The intent of the change, when known
outputs:
  - Findings ordered by severity, each with a file and line
  - A verdict that separates blocking issues from suggestions
skills:
  - deslop
  - unslop
  - technical-writing
  - principle-test-behavior-not-implementation
  - principle-boundary-discipline
agents:
  - reviewer
approval:
  - Before posting comments to an external review system
metadata:
  nskills:
    tags: [review, code-quality, correctness]
    provenance: original
---

# Objective

Find the problems that matter before a human reviewer or a merge does, and say
clearly which ones block.

# Inputs

- The diff, branch, or commit range to review.
- The stated intent, if the author provided one.
- Repository conventions that constrain the change.

# Steps

1. `track` the review.
2. Establish scope: what changed, what did not, and what the author claimed.
3. `delegate` the first pass to the `reviewer` agent with the diff and the
   stated intent.
4. Read the diff yourself. For each changed file, ask what could break and who
   depends on the old behavior.
5. Check correctness first: boundary validation, error paths, shared state,
   ordering, and null or empty cases.
6. Check scope: unrelated edits, dead code, files changed without a reason.
7. `load-skill` `principle-test-behavior-not-implementation`. Verify the tests
   would fail if the behavior were wrong.
8. Check maintainability in one pass with `deslop`: duplicated logic, leaky
   abstractions, comments that restate code.
9. Check the prose in comments, commit messages, and docs with `unslop` when
   the change includes writing.
10. For each finding, record severity, file and line, and the concrete change
    that would fix it. Do not report a finding you cannot point at.
11. `load-skill` `technical-writing` and write the summary: verdict first, then
    blocking findings, then suggestions.

# Skills

| Skill | Purpose in this workflow |
| --- | --- |
| `deslop` | Find code-quality problems in the diff |
| `unslop` | Remove AI tells from comments and docs in the change |
| `technical-writing` | Write a review a human can act on |
| `principle-test-behavior-not-implementation` | Judge whether tests prove behavior |
| `principle-boundary-discipline` | Check validation at the edges |

# Agents

| Agent | Responsibility |
| --- | --- |
| `reviewer` | Independent correctness and maintainability pass |

# Outputs

- A verdict: approve, approve with suggestions, or changes required.
- Blocking findings with file and line.
- Non-blocking suggestions, clearly separated.
- What was checked and what was not.

# Approval checkpoints

Ask the operator before:

- Posting comments to an external review system.
- Approving a change that touches security, data, or deployment paths.

Reviewing local files proceeds without asking.

# Failure behavior

- If the diff cannot be resolved, report the command that failed instead of
  reviewing a partial change.
- If the change has no stated intent, review for internal consistency and say
  that intent was unavailable.
- If a finding needs context outside the diff, name the file to read next
  rather than guessing.
- Do not soften a blocking finding to avoid disagreement. State it plainly and
  let the author respond.

# Completion criteria

- Every finding names a file and line.
- The verdict distinguishes blocking issues from suggestions.
- The review names what was not checked.
- No finding is based on style preference alone when the repository already
  has a convention.
