---
name: Implement Feature
description: Take a feature request from framing through design, failing tests, implementation, and review.
version: 0.1.0
license: MIT
compatibility: [opencode, hermes, freebuff, generic]
inputs:
  - A feature request or issue, in the operator's words
  - The repository or subsystem it applies to
outputs:
  - A design sketch and rationale when the change is non-trivial
  - Working code with tests that failed before it
  - A short change summary naming what was verified and what was not
skills:
  - sharpen
  - design-before-code
  - tdd
  - principle-prove-it-works
  - principle-sequence-verifiable-units
  - technical-writing
agents:
  - implementer
  - reviewer
approval:
  - Before expanding scope beyond the request
  - Before changing a public interface or stored data shape
  - Before adding a dependency
metadata:
  nskills:
    tags: [feature, implementation, tdd]
    provenance: original
---

# Objective

Deliver the smallest coherent implementation of the request that can be
verified, without locking in a shape the request does not need.

# Inputs

- The request, in the operator's words.
- The repository or subsystem to change.
- Any existing conventions, tests, or interfaces that constrain the shape.

If the request is ambiguous in a way that changes the design, ask one focused
question before starting. Do not ask a list of questions the repository can
answer.

# Steps

1. `track` the work. One entry per step below, updated as work moves.
2. `load-skill` `sharpen` and restate the request as a concrete outcome: what
   changes, for whom, and how it will be verified.
3. Read the code the change touches. Identify the callers, the tests, and the
   invariants already in place.
4. Decide whether the change needs a design sketch. Load `design-before-code`
   when it changes a public interface, moves responsibility between modules, or
   would be expensive to reverse. Skip it for a local change and say so.
5. When the design is non-trivial, `delegate` the sketch and rationale to the
   `implementer` agent and review the result before writing code.
6. `load-skill` `tdd`. Write the failing test that proves the missing behavior,
   run it, and confirm it fails for the expected reason.
7. Implement in units that each leave the suite passing, per
   `principle-sequence-verifiable-units`.
8. Add or update tests where the change moved a contract. Do not add tests that
   restate the implementation.
9. Run the project's real verification: test suite, type check, linter, build.
   Record the commands and their results.
10. `load-skill` `technical-writing` for the change summary. Keep it to what
    changed, why, and what was verified.
11. `delegate` a review pass to the `reviewer` agent when the change is larger
    than a local fix. Address findings or record why they are out of scope.

# Skills

| Skill | Purpose in this workflow |
| --- | --- |
| `sharpen` | Turn the request into one concrete, verifiable outcome |
| `design-before-code` | Sketch interfaces and responsibility before implementation |
| `tdd` | Prove the missing behavior with a failing test first |
| `principle-prove-it-works` | Replace assumption with executed evidence |
| `principle-sequence-verifiable-units` | Keep each step independently checkable |
| `technical-writing` | Write the change summary for a reviewer |

# Agents

| Agent | Responsibility |
| --- | --- |
| `implementer` | Produces the design sketch and the implementation |
| `reviewer` | Independent pass for correctness, scope, and maintainability |

# Outputs

- The implemented change.
- Tests that demonstrate the behavior.
- A change summary with the exact verification commands and their results.
- Unresolved questions or accepted tradeoffs, named explicitly.

# Approval checkpoints

Ask the operator before:

- Expanding scope past the request.
- Changing a public interface, CLI flag, config key, or stored data shape.
- Adding a runtime dependency.
- Touching code outside the repository the request named.

Reading, analysis, local edits, and running tests proceed without asking.

# Failure behavior

- If the failing test cannot be made to fail for the expected reason, stop and
  report what the code actually does. Do not write a test that passes trivially.
- If verification cannot run in this environment, say which command is blocked
  and why. Do not claim it passed.
- If implementation keeps fighting the design, return to the sketch step and
  replace the design rather than patching around it.
- If a review finding is real but out of scope, record it in the output instead
  of silently leaving it.

# Completion criteria

- The requested behavior exists and is covered by an executed test.
- The full verification commands pass, or their failure is explained.
- No unrelated files changed without a stated reason.
- The change summary lets a reviewer understand the change without reading the
  whole diff.
