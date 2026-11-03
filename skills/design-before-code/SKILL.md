---
name: Design Before Code
description: Sketch usage, types, and module boundaries before writing code, then implement against the sketch and scrap it when reality disagrees.
version: 0.1.0
license: MIT
compatibility: [opencode, hermes, freebuff, generic]
metadata:
  nskills:
    tags: [design, architecture, planning]
    provenance: derived:pstack:architect
---

# Design Before Code

Use this for non-trivial work where jumping straight to code would lock in the
wrong shape. For a one-line change, skip it and make the change.

The goal is a small, reviewable design artifact that a later implementer can
follow without guessing. The sketch is a contract, not a prediction. When
reality disagrees with it, change the sketch on purpose.

## Workflow

1. Ground
2. Sketch
3. Agree
4. Implement
5. Scrap

Open a task list with one entry per phase before starting. Keep the entries
current; the list is the progress record.

## 1. Ground

Read every system the new code touches. Trace the actual call path, not the
directory listing. Identify:

- Who owns each piece of state.
- Which module currently decides each behavior.
- Where the existing seams are, and which ones are load-bearing.
- Which invariants the surrounding code already relies on.

Write down the explanation you would give a new contributor. If you cannot
explain why a module exists, you are not ready to design around it. Read its
callers and its tests instead of guessing.

Skip grounding only when the work is genuinely greenfield with no surrounding
system to integrate.

## 2. Sketch

Write the caller's usage first. Derive the types and signatures from how the
code will be read at the call site, not from how it is implemented.

Produce at least two structurally distinct candidates before choosing. Point
fixes inside one shape do not count; the alternatives must differ in where
responsibility sits. For small changes, a second candidate can be two
paragraphs of tradeoff. For larger work it is a module map with types.

Evaluate candidates on:

- **Interface depth.** Prefer the design that hides more complexity behind a
  smaller public surface.
- **Local reasoning.** A change that looks right from one file should be right
  for the whole repository.
- **Failure shape.** Which errors become impossible, and which become
  explicit?
- **Migration cost.** How much existing code must move, and can it move in
  verifiable units?

Screen each candidate with `references/design-red-flags.md` before synthesis.

Produce one design package:

- The usage sketch.
- Types, signatures, and module boundaries. Small changes: one file. Larger
  changes: a module map plus the type definitions.
- `not implemented` bodies and pseudocode where behavior is not obvious.
- A short rationale: candidates considered, why the chosen shape wins, and
  which constraints came from grounding.

Use `references/rationale-template.md` as the shape for the rationale.

## 3. Agree

Default: continue into implementation with the synthesized design. Ask the
operator only when a workflow's approval checkpoint requires it, or when the
design changes a public contract that other people own.

That checkpoint is worth taking when the design redefines ownership, deletes a
public interface, or commits to a migration that is expensive to reverse.
Surface the design and pause.

If the operator pushes back on the shape, treat it as new grounding evidence.
Return to step 1 before writing more code.

## 4. Implement against the sketch

Replace `not implemented` bodies with code. Replace pseudocode with logic. The
sketch is the contract.

When implementation needs something the sketch did not anticipate, decide
which of these is true:

- The sketch was wrong.
- The requirement was missed.
- The implementation is overreaching.

Say which one, out loud, in the rationale. Do not silently absorb a deviation.

For each accepted deviation, update the affected part of the design artifact
and record who accepted it. A local rename does not need an architecture
rewrite. A changed error contract does.

Do not edit the design merely to justify what was already built. If the next
worker would receive contradictory instructions, the unit is not reconciled.

## 5. Scrap when the architecture is wrong

Throw the sketch out when implementation keeps producing friction it cannot
absorb. Look for a pattern, not a single instance:

- The same workaround appearing in unrelated places.
- Unrelated edge cases that each need a special branch.
- Types that need escape hatches to compile.
- Callers that must know internal rules to use the abstraction.
- Repeated deviations of the same shape during implementation.

When you scrap:

1. Re-read what was built.
2. Redesign as if the new constraints had been day-one requirements.
3. Subtract before adding. The replacement sketch should be smaller than the
   old one before it grows.
4. Return to step 2.

Some problems are genuinely complex. Complexity in the data is not complexity
in the design; do not scrap a sound design because the domain is hard.

## Outputs

- A grounding summary.
- An interface sketch with usage first.
- A rationale that names the rejected candidates.
- The implementation, or an explicit list of unresolved deviations.

## References

- `references/design-red-flags.md`: failure shapes to screen out.
- `references/rationale-template.md`: the shape of the written rationale.
