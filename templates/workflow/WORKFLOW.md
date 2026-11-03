---
name: Workflow Name
description: One sentence that says what this workflow accomplishes.
version: 0.1.0
license: MIT
compatibility: [opencode, hermes, freebuff, generic]
inputs:
  - The request or artifact this workflow starts from
outputs:
  - What the operator receives when it finishes
skills:
  - skill-id
agents:
  - agent-id
approval:
  - Before an irreversible or external action
depends:
  tools: []
metadata:
  nskills:
    tags: [topic]
    provenance: original
---

# Objective

One paragraph. The outcome, and the constraint that shapes it.

# Inputs

- What is required before starting.
- What is optional.
- What to do when an input is missing.

# Steps

1. `track` the work.
2. State the first step. Name the skill it loads with `load-skill` if any.
3. Continue. Each step produces evidence the next step uses.
4. Verify. Name the command or check.
5. Report.

# Skills

| Skill | Purpose in this workflow |
| --- | --- |
| `skill-id` | Why this skill is loaded here |

# Agents

| Agent | Responsibility |
| --- | --- |
| `agent-id` | The narrow responsibility it owns |

# Outputs

- The primary artifact.
- The evidence that it works.
- What was not verified.

# Approval checkpoints

Ask the operator before:

- Irreversible actions.
- External actions.

Reading, local edits, and local tests proceed without asking.

# Failure behavior

- What happens when an input is invalid.
- What happens when verification fails.
- What happens when the task is out of scope.

# Completion criteria

- The output exists.
- The evidence was produced by running the check, not by assertion.
- Remaining risks are named.
