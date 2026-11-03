---
name: "Laziness Protocol"
description: "Apply when refactoring, evaluating diff size, or tempted to add abstractions, layers, or signal threading. Bias toward deletion and the smallest change that solves the problem."
version: 0.1.0
license: MIT
compatibility: [opencode, hermes, freebuff, generic]
user-invocable: false
metadata:
  nskills:
    tags: [minimal-change, refactoring]
    provenance: pstack:principle-laziness-protocol
---
# Laziness Protocol

- **Consolidate decisions.** Do not repeat the same choice in several places. Put it behind one source of truth and pass the result as a simple flag.
- **Minimize the diff.** Make the smallest change that solves the problem. Fewer lines beat "elegant" boilerplate.