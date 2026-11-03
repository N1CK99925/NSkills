---
name: Ship PR
description: Drive a pull request from opened to mergeable, resolving checks and conflicts without hiding failures.
version: 0.1.0
license: MIT
compatibility: [opencode, hermes, freebuff, generic]
inputs:
  - An open pull request, branch, or commit range
  - The repository's required checks and merge policy
outputs:
  - Green checks or an explanation of each remaining failure
  - Resolved conflicts with preserved intent on both sides
  - A merge-ready summary for the reviewer
skills:
  - fix-ci
  - fix-merge-conflicts
  - principle-prove-it-works
  - technical-writing
agents:
  - reviewer
approval:
  - Before pushing to a shared branch
  - Before force-pushing or rewriting history
  - Before merging or closing the pull request
depends:
  tools: [git]
metadata:
  nskills:
    tags: [pr, ci, git, shipping]
    provenance: original
---

# Objective

Get the pull request to a state a human can merge, with every remaining
failure explained rather than hidden.

# Inputs

- The pull request, branch, or commit range.
- The repository's required checks.
- Any review comments that still need a response.

# Steps

1. `track` the work.
2. Establish the current state: checks, conflicts, review status, and what the
   author claims the change does.
3. `load-skill` `fix-ci`. Work one failing check at a time from the log, not
   from the check name. Reproduce the failure locally before changing code.
4. When checks need a push, confirm the target branch and ask before pushing if
   the branch is shared.
5. If the branch has conflicts, `load-skill` `fix-merge-conflicts`. Resolve by
   understanding both sides, then run the verification that covers the merged
   behavior.
6. `load-skill` `principle-prove-it-works`. Re-run the failing check's local
   equivalent and the full suite after each fix.
7. `delegate` a final review pass to the `reviewer` agent once checks are green.
8. `load-skill` `technical-writing` and write the handoff: what changed, what
   is verified, what remains, and any decision the reviewer must make.
9. Stop before merging. Merging is the operator's decision.

# Skills

| Skill | Purpose in this workflow |
| --- | --- |
| `fix-ci` | Diagnose and fix failing checks from logs |
| `fix-merge-conflicts` | Resolve conflicts and validate the result |
| `principle-prove-it-works` | Confirm each fix with executed evidence |
| `technical-writing` | Write the merge-ready handoff |

# Agents

| Agent | Responsibility |
| --- | --- |
| `reviewer` | Final correctness pass before the operator merges |

# Outputs

- The state of every required check.
- Each conflict resolution and the reasoning behind it.
- The handoff summary for the reviewer.
- Explicit list of remaining risks or blockers.

# Approval checkpoints

Ask the operator before:

- Pushing to a shared branch.
- Force-pushing or rewriting history.
- Merging, closing, or converting the pull request to draft.
- Changing CI configuration to make a check pass.

Local commits on a private branch, reading logs, and running checks proceed
without asking.

# Failure behavior

- If a check cannot be reproduced locally, say so and report the closest local
  command. Do not push a speculative fix.
- If a conflict cannot be resolved without choosing between two intended
  behaviors, stop and ask which behavior wins.
- If a check is failing for an unrelated reason, report it as pre-existing and
  do not fix it inside this pull request.
- Never disable or skip a required check to reach green.

# Completion criteria

- Every required check passes, or its failure is explained as pre-existing or
  environmental.
- No unresolved conflicts remain.
- The handoff lets the reviewer merge without re-deriving the state.
- Nothing was merged without explicit operator approval.
