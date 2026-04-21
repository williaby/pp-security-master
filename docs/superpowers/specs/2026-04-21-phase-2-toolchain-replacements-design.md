# Phase 2: Toolchain Replacements -- Design Spec

> **Status**: Approved | Ready for Implementation
>
> **Date**: 2026-04-21
>
> **Parent plan**: `docs/superpowers/plans/2026-04-20-global-alignment.md` (Tasks 6-11)
>
> **Prerequisite**: Phase 1 complete (confirmed via merge of PR #9 on 2026-04-21)

---

## Overview

Phase 2 replaces three legacy tools (Black, MyPy, safety) with their global-standard equivalents
(Ruff format, BasedPyright, pip-audit) and adds three new quality gates (darglint, interrogate,
qlty). All work is scoped to `pyproject.toml`, `noxfile.py`, `Makefile`, and source files that
require type fixes.

Phase 3 (pre-commit) depends on Phase 2 being complete. The `.pre-commit-config.yaml` is not
created until Phase 3 begins.

---

## Branch Strategy

Phase 2 uses a risk-tiered split across three sequential branches. Each branch must be merged to
main before the next begins.

```
main
 └── feature/phase-2a-toolchain-swaps      (Tasks 6, 8)
      └── [merge to main]
           └── feature/phase-2b-basedpyright  (Task 7)
                └── [merge to main]
                     └── feature/phase-2c-new-gates   (Tasks 9, 10, 11)
                          └── [merge to main]
```

**Rationale for the split:**
- Tasks 6 and 8 are zero-risk removals with identical output characteristics. They do not need
  to wait for type work.
- Task 7 is the only task with unknown scope. BasedPyright strict mode will surface type errors
  that MyPy's current `ignore_errors = true` overrides have masked. Isolating it prevents
  type-fix churn from mixing with unrelated changes.
- Tasks 9, 10, and 11 are additive gates. They build on a clean type-checked base and are
  grouped because they share no risk with the type migration.

---

## Branch 2a: Toolchain Swaps (Tasks 6 + 8)

### Scope

**Removes:** Black (formatter), safety (vulnerability scanner)

**Adds:** `ruff format` as the canonical formatter, pip-audit as the sole vulnerability scanner
(already present; safety is redundant)

**Files touched:**
- `pyproject.toml`
- `noxfile.py`
- `Makefile`

### pyproject.toml changes

- Remove `black = "24.10.0"` from `[tool.poetry.group.dev.dependencies]`
- Remove `safety = ">=3.0.1"` from `[tool.poetry.group.dev.dependencies]`
- Remove the entire `[tool.black]` section
- Update `[tool.ruff.lint.isort]` `profile` from `"black"` to `"ruff"`
- Remove the `E501` ignore comment text "(handled by black)" -- the rule remains suppressed but
  the comment must not reference a removed tool
- Add `[tool.ruff.format]` config block:

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

### noxfile.py changes

- Lint session: replace `session.run("black", "--check", *args)` with
  `session.run("ruff", "format", "--check", *args)`
- Format session: replace `session.run("black", *args)` with `session.run("ruff", "format", *args)`
- Security session: remove the `safety check --json` invocation and its comment

### Makefile changes

- Lint target: replace `$(POETRY) run black --check .` with `$(POETRY) run ruff format --check .`
- Format target: replace `$(POETRY) run black .` with `$(POETRY) run ruff format .`
- Security target: replace `$(POETRY) run safety check` with `$(POETRY) run pip-audit`

### Verification gate

```bash
poetry install --sync
poetry run ruff format --check .   # must exit 0
poetry run nox -s security         # bandit and pip-audit pass; safety must not appear
```

### Commits

Two commits: one for Task 6 (Black removal), one for Task 8 (safety removal). Commit messages
are defined in the master plan.

### Risk assessment

Near-zero. Ruff format and Black produce identical output for standard Python. The only case
where a diff appears is files that Black never processed, which is an intentional improvement.

---

## Branch 2b: BasedPyright Migration (Task 7)

### Scope

**Removes:** MyPy, types-pyyaml, types-python-dateutil stubs, `[tool.mypy]`, `[tool.pydantic-mypy]`

**Adds:** BasedPyright in strict mode

**Files touched:**
- `pyproject.toml`
- `noxfile.py`
- `Makefile`
- `src/**/*.py` (count unknown until first run; all errors must be fixed)

### pyproject.toml changes

- Remove from `[tool.poetry.group.dev.dependencies]`:
  - `mypy = "1.13.0"`
  - `types-pyyaml = ">=6.0.12.12"`
  - `types-python-dateutil = ">=2.8.19.20240106"`
- Add to `[tool.poetry.group.dev.dependencies]`:
  - `basedpyright = ">=1.1.400"`
- Remove the entire `[tool.mypy]` section (currently lines 208-236)
- Remove the entire `[tool.pydantic-mypy]` section
- Remove all `[[tool.mypy.overrides]]` sections
- Add `[tool.basedpyright]` config:

```toml
[tool.basedpyright]
pythonVersion = "3.11"
pythonPlatform = "All"
typeCheckingMode = "strict"
strictListInference = true
strictDictionaryInference = true
strictSetInference = true
```

### noxfile.py changes

- Type check session: replace `session.run("mypy", "src")` with `session.run("basedpyright")`

### Makefile changes

- Type check target: replace `$(POETRY) run mypy src` with `$(POETRY) run basedpyright`

### Expected error categories

BasedPyright strict mode will likely surface errors in these categories, based on the current
MyPy config having `ignore_errors = true` on several override sections:

| Category | Typical cause | Fix |
|----------|--------------|-----|
| Missing return annotation | Functions without `-> ReturnType` | Add return type to signature |
| `Unknown` type | SQLAlchemy ORM columns, untyped third-party returns | Explicit annotation or `isinstance` narrowing |
| Optional not guarded | `value.attr` where `value` could be `None` | Add `if value is not None:` guard |
| Implicit `Any` | Untyped third-party imports without stubs | Use `cast()` or source-available stubs |

### Suppression policy

No `# type: ignore` or `# pyright: ignore` suppressions are permitted. If a third-party library
has no stubs and BasedPyright cannot resolve it, use `py.typed` marker files or inline `cast()`
calls. If a suppression is genuinely unavoidable, it must be paired with a comment referencing
an open issue number.

### Scope contingency

If BasedPyright surfaces more than 30 errors, fixes are broken into logical sub-commits by module
(e.g., one per `src/security_master/` subdirectory) within the same branch. The branch does not
close and the PR is not raised until `basedpyright` exits 0.

### Verification gate

```bash
poetry install --sync
poetry run basedpyright          # must exit 0, 0 errors
poetry run nox -s type_check     # must pass end-to-end
```

### Commits

One commit once all errors are resolved. Commit message defined in master plan.

### Risk assessment

High effort, unknown scope. Isolated in its own branch specifically to prevent this uncertainty
from blocking or polluting the other branches.

---

## Branch 2c: New Gates (Tasks 9, 10, 11)

Tasks within this branch execute in order: 9, then 10, then 11. Each is committed before the
next begins. The ordering matters because Task 9 may add docstrings that contain `raise`
statements, and Task 11's new EM/TRY rules will catch those patterns.

### Task 9: darglint + interrogate

**Goal:** Validate that docstring `Args`, `Returns`, and `Raises` sections match function
signatures; enforce 85% docstring coverage in `scripts/`.

**pyproject.toml changes:**
- Add to dev deps: `darglint = ">=1.8.1"`, `interrogate = ">=1.7.0"`
- Add `[tool.interrogate]` config:

```toml
[tool.interrogate]
ignore-init-method = true
ignore-init-module = false
ignore-magic = false
ignore-semiprivate = false
ignore-private = false
fail-under = 85
include = ["scripts/"]
verbose = 0
quiet = false
```

- Add `[tool.darglint]` config:

```toml
[tool.darglint]
strictness = long
ignore_regex = "^_"
```

**Fix work:**
- Run `poetry run python -m darglint src/` and fix all `DAR` errors by updating docstrings to
  match actual function signatures. No `# noqa: DAR` suppressions.
- Run `poetry run interrogate scripts/ --fail-under 85 --verbose` and add Google-style docstrings
  to any flagged functions. Minimal acceptable form:

```python
def my_function(arg: str) -> bool:
    """Check whether arg meets criteria.

    Args:
        arg: The string to evaluate.

    Returns:
        True if arg is non-empty, False otherwise.
    """
```

**Verification gate:**
```bash
poetry install --sync
poetry run python -m darglint src/       # exit 0
poetry run interrogate scripts/ --fail-under 85  # exit 0
```

### Task 10: qlty CLI

**Goal:** Wire qlty as the unified quality runner per the global packages standard.

**Note:** qlty is a standalone CLI binary, not a Python package. It is not added to
`pyproject.toml`.

**Files created/modified:**
- Create `.qlty/qlty.toml`:

```toml
[plugins]
enabled = ["ruff", "bandit"]

[ruff]
config = "pyproject.toml"

[bandit]
target = ["src"]
```

- Update `README.md` dev setup section: add qlty install step after `poetry install`:

```markdown
# Install qlty CLI (standalone, not a Python package)
curl https://qlty.sh | bash
# Then run quality checks
qlty check
```

**Verification gate:**
```bash
qlty check   # exit 0, no untracked findings
```

### Task 11: Ruff rule expansion

**Goal:** Align the Ruff select list with the PyStrict global standard, enforce specific
exception types, tighten branch limits, and update the target Python version.

**pyproject.toml changes:**

Add to the `[tool.ruff.lint]` `select` list:
```toml
"EM",    # flake8-errmsg: error message string literals
"SLF",   # flake8-self: private member access
"RSE",   # flake8-raise: raise statement best practices
"FA",    # flake8-future-annotations
"T10",   # flake8-debugger: no breakpoint() or pdb
"TCH",   # flake8-type-checking: TYPE_CHECKING imports
"FBT",   # flake8-boolean-trap
"TRY",   # tryceratops: try/except structural patterns
"FURB",  # refurb: modernization
"LOG",   # flake8-logging: logging best practices
"ASYNC", # flake8-async: async/await best practices
"C90",   # McCabe complexity (C901)
"PERF",  # perflint: performance anti-patterns
```

Remove from the `[tool.ruff.lint]` `ignore` list:
```toml
"BLE001",  # blind exception catching
```

Update `[tool.ruff.lint.pylint]`:
```toml
max-branches = 12   # was 18; aligns with global standard
```

Update `[tool.ruff]`:
```toml
target-version = "py312"   # was py311
```

**Fix work -- common manual patterns:**

`EM101`/`EM102` (string literals in raise): move message to a variable:
```python
# Before
raise ValueError("message")
# After
msg = "message"
raise ValueError(msg)
```

`FBT001`/`FBT002` (boolean positional arg): make keyword-only:
```python
# Before
def process(data, validate=True):
# After
def process(data, *, validate: bool = True):
```

`TRY003` (untyped raise): use a specific exception type:
```python
# Before
raise Exception("Something went wrong")
# After
raise RuntimeError("Something went wrong")
```

`BLE001` (broad exception catch): replace `except Exception:` with a specific type or the
project's base exception class.

**Verification gate:**
```bash
poetry run ruff check .          # exit 0, 0 violations
poetry run nox -s lint           # all lint sessions green
```

---

## Phase 2 Acceptance Criteria

Phase 2 is complete when all three branches are merged to main and the following gates all pass
from a clean checkout:

| Check | Command | Expected |
|-------|---------|----------|
| Format | `poetry run ruff format --check .` | exit 0 |
| Lint | `poetry run ruff check .` | exit 0, 0 violations |
| Type check | `poetry run basedpyright` | exit 0, 0 errors |
| Security | `poetry run nox -s security` | bandit + pip-audit pass |
| Docstring accuracy | `poetry run python -m darglint src/` | exit 0 |
| Docstring coverage | `poetry run interrogate scripts/ --fail-under 85` | exit 0 |
| Quality runner | `qlty check` | exit 0 |
| Full nox suite | `poetry run nox` | all sessions green |

**Tools that must not appear after Phase 2:** black, mypy, safety (in any invocation)

**Tools that must appear after Phase 2:** basedpyright, ruff format, pip-audit, darglint,
interrogate, qlty

**Phase gate:** Run `/phase-gate` before closing Phase 2. Phase 3 (pre-commit) does not begin
until Phase 2 passes the gate.

---

## Out of Scope

The following are explicitly excluded from Phase 2 and belong to later phases:

- `.pre-commit-config.yaml` (Phase 3)
- GitHub Actions workflow changes (Phase 4)
- `.claude/settings.json` (Phase 5)
- CLAUDE.md documentation updates (Phase 5)
- Em-dash scan across documentation (Phase 5)
- AGENTS.md and GEMINI.md relocation (Phase 5)
