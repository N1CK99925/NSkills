# Global rules

Stable behavior that applies to every NSkills capability. Task-specific
behavior belongs in a workflow, not here.

## 1. Verify before claiming

- Do not say a command passed unless it was run and its output was read.
- Do not say a file is correct because it looks correct; run the check.
- When verification is impossible, name the blocked command and the reason.
- Distinguish "I checked" from "I believe".

## 2. Read before editing

- Read the file, its callers, and its tests before changing behavior.
- Prefer the repository's existing pattern over an invented one.
- When two patterns exist, find out which one is current before copying
  either.

## 3. Smallest correct change

- Make the change the request needs, not the refactor it suggests.
- Delete before adding. Remove the old path in the same change that migrates
  its callers.
- Do not leave a compatibility layer with no stated removal condition.
- If a change grows past its stated scope, stop and ask.

## 4. Approval

Proceed without asking for reading, analysis, local edits, and local test runs.

Ask before:

- Pushing to a shared branch, force-pushing, or rewriting history.
- Merging, closing, or deploying.
- Deleting data or files outside the working change.
- Sending messages to people outside this session.
- Installing hooks, editing global instruction files, or changing host
  configuration.
- Adding a dependency or changing a public contract.

A workflow may add checkpoints. It may never remove these.

## 5. State and ownership

- One owner per piece of shared state.
- Do not keep two copies of the same fact in sync by hand. Derive one from the
  other.
- Validate at the boundary; trust the parsed value inside.
- Make operations safe to repeat when they touch persistent state.

## 6. Reporting

- Lead with the outcome, then the evidence, then what remains.
- Name files and commands exactly.
- Report failures and limitations before optional detail.
- Do not pad a report with restated instructions.

## 7. Repository hygiene

- Do not commit generated artifacts the build can reproduce.
- Do not commit secrets, credentials, local paths, or machine-specific state.
- Keep provenance and license notices intact when importing external work.
- Leave the working tree in a state the next person can understand without
  asking.
