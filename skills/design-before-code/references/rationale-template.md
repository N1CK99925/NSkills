# Rationale template

The prose that ships with the design sketch. One page. Replace the italic
notes with actual content. Delete any section that does not apply.

## Problem

*One paragraph. What we are trying to do, and what about the existing system or
constraints makes the shape non-obvious. Name the constraints grounding
surfaced: existing types to interop with, callers that cannot break, invariants
that cross the boundary.*

## Usage (caller's view)

*Write this first, before the type sketch. Show the README or quickstart the
consumer reads, plus two or three realistic call sites. What they import, what
they call, what comes back. The type sketch below is derived from this. When
they diverge, reconcile the sketch to the usage.*

## Shape

*The recommended architecture. Data structures first, then how data flows
through the signatures. Name the load-bearing decisions. State which invariants
are encoded in types, where validation lives, and what the system deliberately
does not do. Judge interface depth explicitly: what complexity does the public
surface hide, and what remains exposed?*

## Synthesis decision

*Which candidate became the base and why. What was adapted from each of the
others. What was rejected and why.*

## Tradeoffs accepted

*One bullet per tradeoff, in the form "we accept X in exchange for Y." Name
anything a future reader might mistake for an oversight.*

## Alternatives considered

*At least one concrete alternative shape, with one line on why it lost. Judge
each on interface depth, not implementation simplicity. When the constraints
forced the answer, say so.*

## Implementation reconciliation

*Accepted deviations and who accepted them. Update the affected usage,
contracts, signatures, and ownership here. Keep unaccepted changes unresolved.*

## Open questions and risks

*Questions the operator should resolve, phrased as questions, plus risks worth
flagging before implementation starts.*

## Next implementation step

*The first thing to build against the sketch. One sentence.*
