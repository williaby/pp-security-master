# Phase 2c: New Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add darglint, interrogate, and qlty as docstring and quality gates, then expand the Ruff rule set to full PyStrict alignment and fix all surfaced violations.

**Architecture:** Three sequential task sets on a single branch (`feature/phase-2c-new-gates`). Task 9 (darglint + interrogate) runs first because docstring additions may introduce `raise` statements that Task 11's new EM/TRY rules will catch. Task 10 (qlty) is independent but sits between 9 and 11 to give an early quality signal. Task 11 (Ruff rules) closes the branch.

**Tech Stack:** Poetry, darglint >=1.8.1, interrogate >=1.7.0, qlty CLI (standalone binary), Ruff 0.12.3, nox, Make

**Spec:** `docs/superpowers/specs/2026-04-21-phase-2-toolchain-replacements-design.md` (Branch 2c section)

**Prerequisite:** Branch `feature/phase-2b-basedpyright` merged to main (PR #11, confirmed merged 2026-04-23).

---

## Discovery Notes

These findings from the pre-plan codebase scan inform several plan decisions:

- **scripts/ is already 100% documented** -- all three Python scripts have full Google-style docstrings on every function. The 85% interrogate gate is trivially satisfied. No fix work needed there.
- **models.py is 0% documented** -- the five `__repr__` methods on `SecurityMaster`, `KuberaSheet`, `KuberaSection`, `KuberaHolding`, and `HoldingComparison` have no docstrings. These are the primary gap for the src/ 70% threshold.
- **database.py has thin single-line docstrings** -- all five functions are documented with one-liners. darglint `strictness = long` will flag them all for missing `Args:` / `Returns:` sections.
- **Two pre-existing Ruff violations in scripts/workflow_prepare_pr.py** -- PLC0207 (line 138) and RUF059 (line 187). Both rules are already in the select list but the nox lint session scopes to `src/ tests/` only, missing `scripts/`. These must be fixed before expanding the rule set.
- **"C90" must NOT be added to select** -- the existing `"C"` entry already selects all C rules including C901. The real change is removing `"C901"` from the ignore list to start enforcing it.
- **darglint skips dunder methods** -- `ignore_regex = "^_"` matches `__repr__`, `__str__`, etc. The models.py `__repr__` docstrings only need to satisfy interrogate (any docstring at all); darglint will skip them entirely.

---

## File Structure

| File | Change |
|------|--------|
| `pyproject.toml` | Add darglint + interrogate dev deps; add `[tool.interrogate]` and `[tool.darglint]` config blocks; add 12 new Ruff rule codes to select; remove `BLE001` and `C901` from ignore; set `max-branches = 12`; set `target-version = "py312"` |
| `noxfile.py` | Add darglint and interrogate invocations to lint session (lines 185-198) |
| `Makefile` | Add darglint and interrogate to lint target |
| `.qlty/qlty.toml` | Create new file |
| `README.md` | Add qlty CLI install step to dev setup section |
| `src/security_master/storage/models.py` | Add one-line `__repr__` docstrings to all 5 model classes |
| `src/security_master/storage/database.py` | Expand thin one-liner docstrings to full Google-style (darglint fix) |
| `src/**/*.py` | Expand any remaining thin docstrings; fix EM/FBT/TRY/BLE/C901/TCH violations from new Ruff rules |
| `scripts/workflow_prepare_pr.py` | Fix 2 pre-existing violations (PLC0207 line 138, RUF059 line 187) |

---

## Task 1: Create feature branch

**Files:** none (setup only)

- [ ] **Step 1: Create and switch to the feature branch**

```bash
git checkout main
git pull
git checkout -b feature/phase-2c-new-gates
```

Expected: branch created, working tree clean.

- [ ] **Step 2: Verify the baseline is clean**

```bash
poetry run ruff check src/ tests/
```

Expected: exit 0, no violations. This confirms the starting point before any config changes.

---

## Task 2: Add darglint + interrogate to pyproject.toml

**Files:**

- Modify: `pyproject.toml`

- [ ] **Step 1: Add darglint and interrogate to dev dependencies**

In `pyproject.toml`, in `[tool.poetry.group.dev.dependencies]`, after `basedpyright = ">=1.1.400"`, add:

```toml
darglint = ">=1.8.1"
interrogate = ">=1.7.0"
```

- [ ] **Step 2: Add [tool.interrogate] and [tool.darglint] config blocks**

The current file has this sequence around line 169-175:

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.basedpyright]
```

Change it to:

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.interrogate]
ignore-init-method = true
ignore-init-module = false
ignore-magic = false
ignore-semiprivate = false
ignore-private = false
fail-under = 70
verbose = 0
quiet = false

[tool.darglint]
strictness = long
ignore_regex = "^_"

[tool.basedpyright]
```

**Note on thresholds:** `fail-under = 70` is the `src/` threshold. The `scripts/` check always passes `--fail-under 85` on the command line (wired into nox in Task 6). The `ignore_regex = "^_"` means darglint skips all dunder methods (`__repr__`, `__init__`, etc.), so those need only a plain docstring for interrogate -- no `Args:`/`Returns:` sections required.

- [ ] **Step 3: Verify pyproject.toml is valid TOML**

```bash
python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" && echo "Valid TOML"
```

Expected: `Valid TOML`. If it fails, look for an unclosed string or misplaced bracket near the new blocks.

- [ ] **Step 4: Install new dependencies**

```bash
poetry install --sync
```

Confirm both packages installed:

```bash
poetry show darglint 2>&1 | head -1
poetry show interrogate 2>&1 | head -1
```

Expected: version lines for both (not "Package darglint not found").

---

## Task 3: Triage -- run darglint and interrogate baseline

**Files:** none (discovery only, no commit)

- [ ] **Step 1: Run darglint and capture full output**

```bash
poetry run darglint src/ 2>&1 | tee /tmp/darglint-baseline.txt
wc -l /tmp/darglint-baseline.txt
```

Darglint prints one line per violation. The count tells you how much fix work Task 4 requires. Common codes:

| Code | Meaning |
|------|---------|
| `DAR101` | Parameter in function signature but missing from `Args:` section |
| `DAR201` | Function returns non-None but docstring has no `Returns:` section |
| `DAR401` | Function body has a `raise` statement but docstring has no `Raises:` section |
| `DAR301` | Generator function but docstring has no `Yields:` section |

- [ ] **Step 2: Run interrogate baseline on src/ and scripts/**

```bash
poetry run interrogate src/ --verbose 2>&1 | tail -8
poetry run interrogate scripts/ --verbose 2>&1 | tail -8
```

Note both coverage percentages. scripts/ should already be at 100%. src/ will be below 70%, primarily because of the five undocumented `__repr__` methods in `models.py`.

---

## Task 4: Expand thin docstrings in src/ (darglint fix)

**Files:**

- Modify: `src/security_master/storage/database.py` (definitely flagged)
- Modify: any other `src/**/*.py` files listed in `/tmp/darglint-baseline.txt`

- [ ] **Step 1: Fix database.py -- expand all five one-liner docstrings**

`database.py` currently has one-line docstrings on all five functions. darglint `strictness = long` requires `Args:`, `Returns:`, and `Raises:` sections wherever the signature demands them. Replace the current thin docstrings with these:

```python
def get_database_url() -> str:
    """Construct the database connection URL from environment variables.

    Reads DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD with
    development-friendly defaults when variables are absent.

    Returns:
        PostgreSQL connection URL as a string.
    """
```

```python
def create_db_engine(database_url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine with connection pooling configured.

    Args:
        database_url: PostgreSQL connection URL. When None, calls
            get_database_url() to read from environment variables.

    Returns:
        SQLAlchemy Engine with pool_pre_ping enabled and pool_recycle=300.
    """
```

```python
def create_tables(engine: Engine) -> None:
    """Create all ORM-mapped tables in the target database if they do not exist.

    Args:
        engine: SQLAlchemy Engine connected to the target database.
    """
```

```python
def get_session_factory(engine: Engine) -> Callable[[], Session]:
    """Build a callable session factory bound to the given engine.

    Args:
        engine: SQLAlchemy Engine to bind new sessions to.

    Returns:
        Callable that returns a fresh Session on each invocation.
    """
```

```python
def get_db_session(
    session_factory: Callable[[], Session],
) -> Generator[Session, None, None]:
    """Yield a database session that commits on success and rolls back on error.

    Commits automatically on clean exit. Rolls back and re-raises on any
    exception. Always closes the session in the finally block.

    Args:
        session_factory: Callable that produces a new Session instance.

    Yields:
        An active, open database Session.

    Raises:
        Exception: Re-raises any exception after rolling back the session.
    """
```

- [ ] **Step 2: Verify database.py is clean**

```bash
poetry run darglint src/security_master/storage/database.py
```

Expected: no output (zero violations). If darglint still reports errors, the docstring section is missing or misspelled -- check indentation and that `Args:` / `Returns:` / `Raises:` end with a colon.

- [ ] **Step 3: Fix darglint violations in remaining src/ files**

Work through each file listed in `/tmp/darglint-baseline.txt`. Run darglint per-file to focus:

```bash
poetry run darglint src/security_master/storage/mappers.py
poetry run darglint src/security_master/storage/validators.py
poetry run darglint src/security_master/storage/views.py
poetry run darglint src/security_master/storage/schema_export.py
poetry run darglint src/security_master/patch/pp_xml_export.py
```

For each violation, expand the flagged docstring. Rules for which sections are required under `strictness = long`:

- `Args:` is required when the function has parameters other than `self` or `cls`
- `Returns:` is required when the return type annotation is anything other than `None` or `-> None`
- `Raises:` is required when the function body contains an explicit `raise` statement
- Dunder methods (`__repr__`, `__init__`, etc.) are skipped entirely because `ignore_regex = "^_"` matches names starting with `_`

Use this template for any function that has parameters, returns a value, and may raise:

```python
def some_method(self, arg1: str, arg2: int = 0) -> list[str]:
    """Short imperative summary of what this does.

    Any additional explanation of behavior, constraints, or non-obvious logic.

    Args:
        arg1: What arg1 represents.
        arg2: What arg2 controls. Defaults to 0.

    Returns:
        Description of the returned list contents.

    Raises:
        ValueError: When arg1 is empty or malformed.
    """
```

- [ ] **Step 4: Run full darglint suite until clean**

```bash
poetry run darglint src/ 2>&1
```

Expected: no output. Do not proceed to Task 5 until this exits with zero output.

---

## Task 5: Add `__repr__` docstrings to models.py (interrogate fix)

**Files:**

- Modify: `src/security_master/storage/models.py`

- [ ] **Step 1: Add one-line docstrings to all five `__repr__` methods**

Locate each `__repr__` method (lines 117, 154, 201, 341, 420 approximately) and add a one-line docstring. darglint will skip these because of `ignore_regex = "^_"`, so a single line is all interrogate needs:

```python
# SecurityMaster (line ~117)
def __repr__(self) -> str:
    """Return a debug-friendly string representation of this SecurityMaster record."""
    ...

# KuberaSheet (line ~154)
def __repr__(self) -> str:
    """Return a debug-friendly string representation of this KuberaSheet record."""
    ...

# KuberaSection (line ~201)
def __repr__(self) -> str:
    """Return a debug-friendly string representation of this KuberaSection record."""
    ...

# KuberaHolding (line ~341)
def __repr__(self) -> str:
    """Return a debug-friendly string representation of this KuberaHolding record."""
    ...

# HoldingComparison (line ~420)
def __repr__(self) -> str:
    """Return a debug-friendly string representation of this HoldingComparison record."""
    ...
```

- [ ] **Step 2: Verify darglint still produces no output on models.py**

```bash
poetry run darglint src/security_master/storage/models.py
```

Expected: no output. darglint must skip the `__repr__` methods via `ignore_regex`. If darglint reports violations, double-check the `[tool.darglint]` config block was added correctly in Task 2.

- [ ] **Step 3: Run interrogate on src/ to verify the 70% threshold**

```bash
poetry run interrogate src/ --fail-under 70 --verbose 2>&1 | tail -5
```

Expected: `RESULT: PASSED (minimum: 70.0%, actual: XX.X%)`. If it still fails:

```bash
poetry run interrogate src/ --verbose 2>&1 | grep "MISSING"
```

For each function listed under `MISSING`, add a one-line docstring. Repeat until `--fail-under 70` passes.

- [ ] **Step 4: Verify scripts/ threshold passes**

```bash
poetry run interrogate scripts/ --fail-under 85 --verbose 2>&1 | tail -5
```

Expected: `RESULT: PASSED` (scripts/ is already 100% documented).

---

## Task 6: Wire darglint and interrogate into nox and Makefile, commit Task 9

**Files:**

- Modify: `noxfile.py` (lines 185-198)
- Modify: `Makefile`

- [ ] **Step 1: Add darglint and interrogate to the nox lint session**

The lint session currently ends with `session.run("yamllint", ".", external=True)`. Add the three new calls after it:

```python
@nox.session(python="3.11")
def lint(session):
    """Run linters."""
    args = session.posargs or SRC_LOCATIONS
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("ruff", "format", "--check", *args)
    session.run("ruff", "check", *args)

    # Markdown linting
    session.run("markdownlint", "**/*.md", external=True)

    # YAML linting
    session.run("yamllint", ".", external=True)

    # Docstring quality gates
    session.run("darglint", "src/")
    session.run("interrogate", "src/", "--fail-under", "70")
    session.run("interrogate", "scripts/", "--fail-under", "85")
```

- [ ] **Step 2: Add darglint and interrogate to the Makefile lint target**

In `Makefile`, the lint target currently reads:

```makefile
lint: ## Run linting checks
 $(POETRY) run ruff format --check .
 $(POETRY) run ruff check .
 $(POETRY) run basedpyright
 markdownlint **/*.md
 yamllint .
```

Change to:

```makefile
lint: ## Run linting checks
 $(POETRY) run ruff format --check .
 $(POETRY) run ruff check .
 $(POETRY) run basedpyright
 markdownlint **/*.md
 yamllint .
 $(POETRY) run darglint src/
 $(POETRY) run interrogate src/ --fail-under 70
 $(POETRY) run interrogate scripts/ --fail-under 85
```

- [ ] **Step 3: Run the full nox lint session to confirm it passes**

```bash
poetry run nox -s lint
```

Expected: exits 0. All steps pass including the new darglint and interrogate gates.

- [ ] **Step 4: Commit Task 9**

Stage all files changed in Tasks 2-6:

```bash
git add pyproject.toml noxfile.py Makefile \
        src/security_master/storage/database.py \
        src/security_master/storage/models.py \
        src/security_master/
git status
```

Review the staged files, then commit:

```bash
git commit -m "feat(quality): add darglint and interrogate docstring gates

Adds darglint >=1.8.1 with strictness=long to enforce Args/Returns/Raises
sections matching function signatures. Adds interrogate >=1.7.0 with 70%
threshold for src/ and 85% for scripts/. Expands thin one-liner docstrings
in database.py and other src/ files to pass darglint. Adds __repr__
docstrings in models.py for interrogate. Wires both gates into the nox
lint session and Makefile lint target.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Create .qlty/qlty.toml and update README.md

**Files:**

- Create: `.qlty/qlty.toml`
- Modify: `README.md`

- [ ] **Step 1: Check whether the qlty CLI is installed**

```bash
qlty --version 2>/dev/null || echo "qlty not installed"
```

If not installed:

```bash
curl https://qlty.sh | bash
```

Then reload your shell profile and verify:

```bash
source ~/.bashrc   # or ~/.zshrc
qlty --version
```

Expected: a version string such as `qlty 0.x.x`.

- [ ] **Step 2: Create .qlty/qlty.toml**

```bash
mkdir -p .qlty
```

Create `.qlty/qlty.toml` with this exact content:

```toml
[plugins]
enabled = ["ruff", "bandit"]

[ruff]
config = "pyproject.toml"

[bandit]
target = ["src"]
```

**Note:** basedpyright is not a qlty plugin. It runs via `poetry run basedpyright` in nox and Makefile only.

- [ ] **Step 3: Run qlty check to confirm it works**

```bash
qlty check
```

Expected: qlty reads ruff config from `pyproject.toml` and runs bandit against `src/`. If qlty reports any findings that are not already tracked, investigate each one before proceeding. Do not add suppressions without a tracked justification.

- [ ] **Step 4: Add qlty install step to README.md dev setup section**

In `README.md`, locate the development setup section. After the `poetry install` line and before the first test command, insert:

```markdown
# Install qlty CLI (standalone binary, not a Python package)
curl https://qlty.sh | bash
# Then run unified quality checks
qlty check
```

- [ ] **Step 5: Commit Task 10**

```bash
git add .qlty/ README.md
git commit -m "feat(quality): add qlty CLI configuration

qlty is the unified quality runner per the global packages standard.
Configured with ruff and bandit plugins, delegating to pyproject.toml
for ruff settings.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Expand Ruff rule set (pyproject.toml config only)

**Files:**

- Modify: `pyproject.toml`
- Modify: `scripts/workflow_prepare_pr.py` (pre-existing violation cleanup)

- [ ] **Step 1: Fix 2 pre-existing violations in workflow_prepare_pr.py**

These violations exist under the current config. Fix them before expanding rules to keep the before/after signal clean.

**PLC0207 at line 138 -- add maxsplit=1:**

Find:

```python
issue.split("-")[0][1:]
```

Change to:

```python
issue.split("-", 1)[0][1:]
```

**RUF059 at line 187 -- rename unused unpacked variable to `_`:**

Find:

```python
user_host, path_part = remote_url.split("@", 1)
```

Change to:

```python
_, path_part = remote_url.split("@", 1)
```

Verify clean:

```bash
poetry run ruff check scripts/workflow_prepare_pr.py
```

Expected: exit 0.

- [ ] **Step 2: Add 12 new rule codes to the Ruff select list**

In `pyproject.toml`, in the `[tool.ruff.lint]` `select` list, add after `"RUF",  # ruff-specific`:

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
    "PERF",  # perflint: performance anti-patterns
```

**Do NOT add "C90".** The existing `"C"` entry already selects all C rules including C901. The real change is removing `"C901"` from the ignore list in Step 4.

- [ ] **Step 3: Remove BLE001 from the ignore list**

In `pyproject.toml`, in the `[tool.ruff.lint]` `ignore` list, delete:

```toml
    "BLE001",  # blind exception catching (needed for generic error handlers)
```

BLE001 enforces catching specific exception types instead of bare `except Exception`. With this removed, all broad exception catches must be replaced. The fix patterns are in Task 10.

- [ ] **Step 4: Remove C901 from the ignore list**

In `pyproject.toml`, in the `[tool.ruff.lint]` `ignore` list, delete:

```toml
    "C901",    # too complex
```

C901 (McCabe complexity) was already selected via `"C"` but suppressed in ignore. Removing it activates complexity enforcement. The threshold drops to 12 in the next step.

- [ ] **Step 5: Set max-branches to 12 and target-version to py312**

In `pyproject.toml`, change:

```toml
[tool.ruff.lint.pylint]
max-branches = 18      # Increased from default 12 for industry standards
max-statements = 75    # Increased from default 50 for industry standards
```

to:

```toml
[tool.ruff.lint.pylint]
max-branches = 12
max-statements = 75
```

Change:

```toml
target-version = "py311"
```

to:

```toml
target-version = "py312"
```

- [ ] **Step 6: Verify pyproject.toml is valid TOML**

```bash
python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" && echo "Valid TOML"
```

Expected: `Valid TOML`.

---

## Task 9: Auto-fix what ruff can

**Files:**

- Modify: any files with auto-fixable violations reported by `ruff check --fix`

- [ ] **Step 1: Run ruff with --fix and capture what changed**

```bash
poetry run ruff check . --fix 2>&1 | tee /tmp/ruff-autofix.txt
cat /tmp/ruff-autofix.txt
```

`--fix` applies safe, mechanical transformations. Common auto-fixes from the new rules:

- `FURB` -- rewrites `dict(x=1)` to `{"x": 1}`, `list(range(...))` to `[*range(...)]`, etc.
- `PERF` -- rewrites certain inefficient loop patterns
- `FA` -- adds `from __future__ import annotations` where needed for deferred evaluation

- [ ] **Step 2: Identify remaining manual violations**

```bash
poetry run ruff check . 2>&1 | tee /tmp/ruff-remaining.txt
cat /tmp/ruff-remaining.txt
```

Group the remaining violations by rule code to understand the scope before fixing:

```bash
grep -oP '[A-Z]+[0-9]+' /tmp/ruff-remaining.txt | sort | uniq -c | sort -rn
```

Proceed to Task 10 to fix each category.

---

## Task 10: Manually fix remaining Ruff violations

**Files:**

- Modify: any `src/**/*.py` files listed in `/tmp/ruff-remaining.txt`

Work through violations rule code by rule code. After fixing each category, run the scoped check to confirm that category is clean before moving to the next.

- [ ] **Step 1: Fix EM101 / EM102 -- string literals in raise statements**

EM102 flags string literals; EM101 flags f-strings. Move the message to a named variable:

```python
# Before (EM102 -- string literal)
raise ValueError("isin must be a 12-character string")

# After
msg = "isin must be a 12-character string"
raise ValueError(msg)
```

```python
# Before (EM101 -- f-string)
raise ValueError(f"unknown broker: {broker_name}")

# After
msg = f"unknown broker: {broker_name}"
raise ValueError(msg)
```

Confirm clean:

```bash
poetry run ruff check . --select EM
```

Expected: exit 0, no EM violations.

- [ ] **Step 2: Fix FBT001 / FBT002 -- boolean positional arguments**

FBT001 flags boolean positional parameters; FBT002 flags boolean default values on positional parameters. Both are fixed by making the parameter keyword-only with `*`:

```python
# Before (FBT002)
def process(data: list[str], validate: bool = True) -> list[str]:

# After
def process(data: list[str], *, validate: bool = True) -> list[str]:
```

For FBT001 (boolean positional without a default):

```python
# Before (FBT001)
def export_xml(securities: list[SecurityMaster], pretty_print: bool) -> str:

# After
def export_xml(securities: list[SecurityMaster], *, pretty_print: bool) -> str:
```

After making a parameter keyword-only, update every call site in the codebase that passes that argument positionally:

```python
# Before (now broken -- positional bool)
result = export_xml(data, True)

# After
result = export_xml(data, pretty_print=True)
```

Confirm clean:

```bash
poetry run ruff check . --select FBT
```

- [ ] **Step 3: Fix TRY003 -- untyped exception messages**

TRY003 flags bare `raise Exception(...)` where a specific exception type should be used:

```python
# Before (TRY003)
raise Exception("Failed to connect to database")

# After
raise RuntimeError("Failed to connect to database")
```

Use `RuntimeError` for unexpected program states, `ValueError` for bad argument values, `OSError` for I/O failures. If the codebase defines a project-level base exception in `src/security_master/__init__.py` or `utils.py`, use that instead.

Confirm clean:

```bash
poetry run ruff check . --select TRY003
```

- [ ] **Step 4: Fix BLE001 -- broad exception catches**

BLE001 fires on `except Exception:`. The `get_db_session` function in `database.py` uses this pattern for rollback-and-reraise. The correct fix depends on what exceptions can actually occur at that call site.

For a session manager that must handle any failure (including non-SQLAlchemy exceptions), use `BaseException`:

```python
# Before (BLE001 -- still catches too broadly for BLE's intent)
except Exception:
    session.rollback()
    raise

# After (Option A: explicit catch-all with reraise intent)
except BaseException:
    session.rollback()
    raise
```

For error handlers that only need to handle SQLAlchemy failures, narrow to the specific type:

```python
# After (Option B: specific exception type)
from sqlalchemy import exc as sa_exc

except sa_exc.SQLAlchemyError:
    session.rollback()
    raise
```

Choose Option B if only SQLAlchemy errors are expected at that call site. Choose Option A only when the catch genuinely must handle any exception (keyboard interrupt, memory error, etc.).

For any other `except Exception:` blocks across the codebase that swallow exceptions silently, replace with the most specific type that applies.

Confirm clean:

```bash
poetry run ruff check . --select BLE
```

- [ ] **Step 5: Fix C901 -- functions exceeding max-branches = 12**

Functions with more than 12 branch points are now flagged. Extract sub-logic into focused helper methods to reduce the branch count:

```python
# Before: one method with 15+ branches
def classify_security(security: SecurityMaster) -> str:
    if security.isin:
        if len(security.isin) == 12:
            if ...:
                ...
            elif ...:
                ...
        # ... more branches
    elif security.ticker:
        # ... more branches

# After: extract sub-classifiers to reduce branches per method
def _classify_by_isin(security: SecurityMaster) -> str | None:
    """Attempt classification via ISIN. Returns None if ISIN is unavailable."""
    if not security.isin or len(security.isin) != 12:
        return None
    ...

def _classify_by_ticker(security: SecurityMaster) -> str | None:
    """Attempt classification via ticker symbol. Returns None if ticker is absent."""
    if not security.ticker:
        return None
    ...

def classify_security(security: SecurityMaster) -> str:
    """Classify security using available identifiers in priority order.
    ...
    """
    result = _classify_by_isin(security)
    if result:
        return result
    result = _classify_by_ticker(security)
    ...
```

List all flagged functions first:

```bash
poetry run ruff check . --select C901
```

Fix each one until `poetry run ruff check . --select C901` exits 0.

- [ ] **Step 6: Fix TCH -- imports only used in type annotations**

TCH001 flags stdlib imports used only in annotations; TCH002 flags third-party imports used only in annotations. Both should be moved into `TYPE_CHECKING` blocks to avoid runtime cost.

**Important prerequisite:** When moving an import into `TYPE_CHECKING`, add `from __future__ import annotations` at the top of the file. Without it, the type annotation is evaluated at runtime, which will fail since the import is only available during type checking.

```python
# Before (TCH001 -- stdlib Generator only used in annotations)
from collections.abc import Callable, Generator

def get_db_session(
    session_factory: Callable[[], Session],
) -> Generator[Session, None, None]:
    ...
```

```python
# After
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

def get_db_session(
    session_factory: Callable[[], Session],
) -> Generator[Session, None, None]:
    ...
```

After moving imports into `TYPE_CHECKING`, verify basedpyright still passes (the TCH fix can expose type issues if the annotation is evaluated at runtime anywhere):

```bash
poetry run basedpyright
```

Confirm TCH clean:

```bash
poetry run ruff check . --select TCH
```

- [ ] **Step 7: Run full ruff check -- must exit 0**

```bash
poetry run ruff check .
```

Expected: exit 0, no violations. If any remain, apply the fix from Steps 1-6 for that rule code and repeat.

---

## Task 11: Verification gate, commit Task 11, open PR

**Files:** none (verification only, then PR)

- [ ] **Step 1: Run the full nox lint session**

```bash
poetry run nox -s lint
```

Expected: exits 0. All gates pass: ruff format check, ruff check (0 violations), markdownlint, yamllint, darglint (0 violations), interrogate src/ (>=70%), interrogate scripts/ (>=85%).

- [ ] **Step 2: Run the nox type_check session**

```bash
poetry run nox -s type_check
```

Expected: exits 0. The `FA` and `TCH` fixes (adding `from __future__ import annotations` and moving imports into `TYPE_CHECKING`) must not have broken any basedpyright types. If they have, fix the type error and re-run ruff check to confirm no new lint violations.

- [ ] **Step 3: Run the nox security session**

```bash
poetry run nox -s security
```

Expected: exits 0. bandit and pip-audit pass.

- [ ] **Step 4: Run qlty check**

```bash
qlty check
```

Expected: exits 0. No untracked findings.

- [ ] **Step 5: Verify BLE001 and C901 are no longer in the ignore list**

```bash
grep "BLE001\|C901" pyproject.toml
```

Expected: no output. If either appears, it was not removed in Task 8.

- [ ] **Step 6: Commit Task 11**

```bash
git add pyproject.toml src/ tests/ scripts/
git commit -m "fix(quality): align Ruff rules with PyStrict global standard

Adds EM, SLF, RSE, FA, T10, TCH, FBT, TRY, FURB, LOG, ASYNC, PERF rule
codes. Removes BLE001 and C901 from ignore list. Sets max-branches=12 and
target-version=py312. Fixes all violations surfaced by the new rules
including EM raise-message extraction, FBT keyword-only booleans, TRY003
typed exceptions, BLE001 specific catches, C901 complexity splits, and TCH
TYPE_CHECKING imports.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

- [ ] **Step 7: Push branch and open PR**

```bash
git push -u origin feature/phase-2c-new-gates
```

Open a PR targeting `main`. Title:

`feat(quality): phase 2c -- darglint, interrogate, qlty, PyStrict Ruff alignment`

Body:

```sql
## Summary

- Adds darglint >=1.8.1 (strictness=long; Args/Returns/Raises enforcement)
- Adds interrogate >=1.7.0 (70% threshold src/, 85% threshold scripts/)
- Creates .qlty/qlty.toml with ruff and bandit plugins
- Expands Ruff select to 12 new PyStrict-aligned rule codes
- Removes BLE001 and C901 from ignore; sets max-branches=12, target=py312
- Fixes all violations surfaced by the new rules; zero noqa suppressions

## Verification

- `poetry run nox -s lint` passes (darglint, interrogate, ruff all green)
- `poetry run nox -s type_check` passes
- `poetry run nox -s security` passes
- `qlty check` exits 0

## Phase gate

Phase 3 (pre-commit) does not begin until this PR merges.
Run /phase-gate after merge to verify Phase 2 is fully complete.
```

---

## Self-Review Against Spec

### Spec Coverage Check

| Spec requirement (Branch 2c section) | Covered by task |
|--------------------------------------|----------------|
| Add `darglint = ">=1.8.1"` to dev deps | Task 2 Step 1 |
| Add `interrogate = ">=1.7.0"` to dev deps | Task 2 Step 1 |
| Add `[tool.interrogate]` config block | Task 2 Step 2 |
| Add `[tool.darglint]` config block | Task 2 Step 2 |
| Run darglint on src/, fix all DAR errors | Tasks 4, 6 |
| Run interrogate on scripts/ at 85% | Tasks 5, 6 |
| Run interrogate on src/ at 70% (user addition) | Tasks 5, 6 |
| Wire both gates into nox lint session and Makefile | Task 6 |
| Create `.qlty/qlty.toml` | Task 7 Step 2 |
| Add qlty install step to README.md | Task 7 Step 4 |
| Add "EM", "SLF", "RSE", "FA", "T10", "TCH", "FBT", "TRY", "FURB", "LOG", "ASYNC", "PERF" to select | Task 8 Step 2 |
| Do NOT add "C90" (already covered by "C") | Task 8 Step 2 note |
| Remove "BLE001" from ignore | Task 8 Step 3 |
| Remove "C901" from ignore | Task 8 Step 4 |
| Set max-branches = 12 | Task 8 Step 5 |
| Set target-version = "py312" | Task 8 Step 5 |
| Fix EM violations | Task 10 Step 1 |
| Fix FBT violations | Task 10 Step 2 |
| Fix TRY003 violations | Task 10 Step 3 |
| Fix BLE001 violations | Task 10 Step 4 |
| Fix C901 violations | Task 10 Step 5 |
| Fix TCH violations | Task 10 Step 6 |
| Verification gate: ruff check exits 0 | Task 10 Step 7 |
| Verification gate: nox lint | Task 11 Step 1 |
| Verification gate: nox type_check | Task 11 Step 2 |
| Verification gate: nox security | Task 11 Step 3 |
| Verification gate: qlty check | Task 11 Step 4 |

All spec requirements covered. No gaps found.

### Placeholder Check

No "TBD", "TODO", or vague instructions. Every code-change step shows the before/after code. Every verification step shows the exact command and the expected output. Conditional instructions ("if coverage still fails, run X") give the exact follow-up command, not a description of what to do.

### Type Consistency Check

- `database.py` docstring patterns use the exact parameter names and types from the actual file (`database_url: str | None`, `engine: Engine`, `session_factory: Callable[[], Session]`)
- `models.py` class names (`SecurityMaster`, `KuberaSheet`, `KuberaSection`, `KuberaHolding`, `HoldingComparison`) confirmed from the actual file
- `TCH` fix in Task 10 Step 6 uses `Callable` and `Generator` from `collections.abc`, which matches the actual imports in `database.py`
- `sa_exc.SQLAlchemyError` in Task 10 Step 4 Option B is the correct SQLAlchemy 2.x exception path
