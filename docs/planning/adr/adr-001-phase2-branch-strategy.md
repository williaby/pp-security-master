# ADR-001: Phase 2 Toolchain Replacement Branch Strategy

> **Status**: Accepted
> **Date**: 2026-04-21

## TL;DR

Phase 2 toolchain replacements are split across three sequential branches to isolate
BasedPyright's unknown type-error surface area from the zero-risk tool swaps.

## Context

### Problem

Phase 2 replaces three tools (Black, MyPy, safety) and adds three new gates (darglint,
interrogate, qlty). All six tasks could land on one branch, but the tasks differ significantly
in risk profile: some produce identical output (Black to Ruff format), while others will
surface an unknown number of pre-existing bugs (MyPy to BasedPyright strict mode).

### Constraints

- **Technical**: BasedPyright strict mode is significantly more aggressive than the current
  MyPy config, which uses `ignore_errors = true` on several override sections. The number of
  errors it will surface is unknown until the tool runs.
- **Business**: Phase 3 (pre-commit) cannot begin until Phase 2 is complete and all gates
  pass. A blocked Phase 2 blocks the full pipeline.

### Significance

The branching decision determines whether type-fix churn can block unrelated zero-risk changes
from merging. Getting it wrong means delays to Phase 3 if BasedPyright surfaces many errors.

### Branch Topology

All three branches are independent branches off `main`, not stacked. Each targets `main` as
its base. The constraint is on merge order, not on branch creation order:

- `feature/phase-2a-toolchain-swaps` must **merge to main** before `feature/phase-2b-basedpyright` is raised as a PR
- `feature/phase-2b-basedpyright` must **merge to main** before `feature/phase-2c-new-gates` is raised as a PR

Work on a subsequent branch may begin locally before the prior PR merges, but the branch must
be rebased on the updated `main` after each merge before its own PR is opened.

## Decision

**We will use a risk-tiered split across three sequential branches because it isolates the
highest-uncertainty task (BasedPyright migration) without blocking the mergeable zero-risk
tasks.**

### Rationale

The key criterion is containment: if BasedPyright surfaces 50 type errors, that work should
not hold up the Black removal or the qlty configuration. Separate branches allow each group
to merge independently on its own timeline.

## Options Considered

### Option B: Risk-Tiered Split (3 branches) -- Chosen

- `feature/phase-2a-toolchain-swaps` (Task 6: Black → Ruff format; Task 8: safety → pip-audit)
- `feature/phase-2b-basedpyright` (Task 7: MyPy → BasedPyright strict + fix all type errors)
- `feature/phase-2c-new-gates` (Task 9: add darglint + interrogate; Task 10: add qlty CLI; Task 11: expand Ruff rules to PyStrict set)

**Pros:**

- Isolates the unknown-scope task (BasedPyright type fixes) so it cannot block zero-risk work
- Each branch has a single reviewable concern
- Phase-2a can merge and CI can validate it independently before type work starts

**Cons:**

- Three PRs to manage instead of one
- Requires sequential merge discipline (2a before 2b, 2b before 2c)

### Option A: Single Feature Branch (1 branch)

All six tasks land on one `feature/phase-2-toolchain` branch.

**Pros:**

- One PR, simpler tracking

**Cons:**

- BasedPyright type-fix churn mixed with unrelated changes in the same diff
- If BasedPyright surfaces many errors, the entire branch stalls including the zero-risk parts
- Harder to review: formatting removals, type annotations, and new tool configs in one diff

### Option C: Two-Branch Split

- Branch 1: Replacements (Tasks 6, 7, 8)
- Branch 2: Additions (Tasks 9, 10, 11)

**Pros:**

- Simpler than Option B

**Cons:**

- Still bundles Task 7 risk with the safe swaps in Branch 1
- Does not actually isolate the high-risk task

## Consequences

### Positive

- Zero-risk tool swaps (2a) can merge quickly without waiting for type-fix work
- BasedPyright failures stay contained to the 2b branch
- Code review is scoped: each PR has one logical concern

### Trade-offs

- Sequential merge discipline required: reviewers must not open 2b until 2a merges
- Three separate PRs means three separate CI runs

### Technical Debt

None. This is a process decision with no long-term debt implications.

## Implementation

### Components Affected

1. **`feature/phase-2a-toolchain-swaps`**: pyproject.toml, noxfile.py, Makefile
2. **`feature/phase-2b-basedpyright`**: pyproject.toml, noxfile.py, Makefile, src/**/*.py
3. **`feature/phase-2c-new-gates`**: pyproject.toml, .qlty/qlty.toml, README.md, src/, scripts/

### Testing Strategy

- Unit: existing test suite must pass green after each branch merges
- Integration: `poetry run nox` must exit 0 at the tip of each branch before PR is raised

## Validation

### Success Criteria

- [ ] Branch 2a merges with `ruff format --check .` and `nox -s security` both green
- [ ] Branch 2b merges with `basedpyright` exiting 0 and no type suppressions added except under
  the escalation policy: if a third-party library has no stubs and the error cannot be resolved
  by any other means, a targeted `# pyright: ignore[reportUnknownMemberType]` (or narrowest
  applicable code) is acceptable when paired with a GitHub issue reference tracking a proper
  fix. Blanket `# type: ignore` suppressions are never acceptable.
- [ ] Branch 2c merges with `ruff check .`, `darglint`, `interrogate`, and `qlty check` all green
- [ ] `poetry run nox` passes completely after all three branches merge

### Review Schedule

- Initial: on merge of each branch
- Post-Phase-2: run `/phase-gate` before opening Phase 3

## Related

- [Phase 2 Design Spec](../../superpowers/specs/2026-04-21-phase-2-toolchain-replacements-design.md)
- [Global Alignment Plan](../../superpowers/plans/2026-04-20-global-alignment.md)
