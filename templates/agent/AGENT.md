---
name: Agent Name
description: One sentence that says what this agent is responsible for.
version: 0.1.0
license: MIT
compatibility: [opencode, hermes, freebuff, generic]
mode: subagent
tools: [read, search, edit, shell, load-skill, track]
delegates: none
metadata:
  nskills:
    tags: [topic]
    provenance: original
---

# Responsibility

The one job this agent owns, and what it explicitly does not do.

# Instructions

1. Establish the scope from the inputs.
2. Do the work in the order the caller needs it.
3. Produce evidence for every claim.
4. Report the outcome and the limits of what was verified.

# Capabilities

- What this agent can do.
- What it must not do.

# Inputs and outputs

Inputs:

- Required input.
- Optional context.

Outputs:

- Primary output.
- Evidence and limits.

# Delegation

Delegates nothing, or names the agent IDs it may dispatch and why.

# Tools

| Canonical tool | Use |
| --- | --- |
| `read` | Read files and URLs |
| `search` | Find code and paths |

# Failure behavior

- What it does when the input is underspecified.
- What it does when verification is blocked.
