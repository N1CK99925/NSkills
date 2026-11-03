---
name: Fix Bug
description: Reproduce a defect, find its root cause, fix it, and prove the fix with a regression test.
version: 0.1.0
license: MIT
compatibility: [opencode, hermes, freebuff, generic]
inputs:
  - A reproducible symptom, failing test, or bug report
  - The command or path that triggers it
outputs:
  - A regression test that failed before the fix
  - The root-cause explanation
  - The fix and its verification evidence
skills:
  - tdd
  - principle-fix-root-causes
  - principle-prove-it-works
  - deslop
agents:
  - implementer
approval:
  - Before changing behavior that other callers depend on
  - Before disabling or deleting a test
metadata:
  nskills:
    tags: [bug, debugging, testing]
    provenance: original
---

# Objective

Remove the cause of the defect, not its symptom, and leave behind a test that
would have caught it.

# Inputs

- A symptom, stack trace, failing test, or report.
- The command or path that reproduces it.
- Any recent change suspected of introducing it.

# Steps

1. `track` the work.
2. Reproduce the defect. Run the smallest command that shows it. Record the
   exact command and output.
3. If it does not reproduce, stop and report what differs between the report
   and the local environment. Do not guess at a fix for an unseen failure.
4. `load-skill` `principle-prove-it-works` and capture the pre-fix evidence.
5. `load-skill` `principle-fix-root-causes`. Trace the failure to the decision
   that produced it. Read the callers, not only the failing line.
6. Write the causal chain in one short paragraph: trigger, mechanism, why the
   code assumed otherwise.
7. `load-skill` `tdd`. Add the regression test. Run it against the unfixed code
   and confirm it fails for the reason in the causal chain.
8. Fix the cause. Keep the diff to what the causal chain requires.
9. Run the regression test, then the surrounding suite, then the project's
   verification commands.
10. `load-skill` `deslop` and remove anything the fix left behind: dead
    branches, unused helpers, stale comments.
11. Report the causal chain, the fix, and the evidence.

# Skills

| Skill | Purpose in this workflow |
| --- | --- |
| `principle-fix-root-causes` | Find the decision that caused the defect |
| `tdd` | Lock the behavior with a failing test before the fix |
| `principle-prove-it-works` | Execute the reproduction and the verification |
| `deslop` | Remove code the fix made dead |

# Agents

| Agent | Responsibility |
| --- | --- |
| `implementer` | Reproduces, diagnoses, fixes, and verifies |

# Outputs

- Pre-fix reproduction evidence.
- The causal chain.
- The fix and the regression test.
- Post-fix verification output.

# Approval checkpoints

Ask the operator before:

- Changing behavior that other callers rely on.
- Deleting or skipping a test.
- Changing test fixtures or data that other tests share.

Reproduction, reading, local edits, and test runs proceed without asking.

# Failure behavior

- If the defect does not reproduce, report the environmental difference and
  stop. Do not ship a speculative fix.
- If the regression test passes before the fix, the test does not capture the
  defect. Rewrite the test before changing production code.
- If the root cause is outside this repository, document it and fix the local
  boundary rather than adding a workaround in the wrong layer.
- If the fix requires a broader redesign, switch to the `implement-feature`
  workflow instead of stretching this one.

# Completion criteria

- The defect is reproduced before the fix and gone after it.
- The regression test fails without the fix and passes with it.
- The causal chain is written down, not implied by the diff.
- The surrounding suite passes or its failures are explained.
