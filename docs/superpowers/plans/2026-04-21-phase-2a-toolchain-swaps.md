# Phase 2a: Toolchain Swaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove Black and safety from the project, replacing them with `ruff format` and
pip-audit respectively, with no changes to formatted output and no loss of security scanning.

**Architecture:** Two independent tool swaps on a single branch (`feature/phase-2a-toolchain-swaps`).
Black and Ruff format produce identical output for standard Python, so the swap is transparent.
pip-audit is already installed alongside safety; removing safety eliminates redundancy. Each
swap lands in its own commit.

**Tech Stack:** Poetry (dep management), Ruff (formatter), pip-audit (vuln scanner),
Nox (task runner), Make (CLI shortcuts)

---

## File Structure

| File | Change |
|------|--------|
| `pyproject.toml` | Remove `black` dep (line 75), remove `safety` dep (line 81), remove `[tool.black]` section (lines 92-112), update E501 comment (line 166), add `[tool.ruff.format]` block (after line 192), keep isort profile as `"black"` (not changed) |
| `noxfile.py` | Replace `black --check` (line 190), replace `black` format (line 227), remove safety invocation and comment (lines 212-213) |
| `Makefile` | Replace `black --check` (line 45), replace `black` format (line 52), replace `safety check` (line 56) |

---

## Task 6: Remove Black, Wire Ruff Format

**Files:**
- Modify: `pyproject.toml:75,81,92-112,166,192-196`
- Modify: `noxfile.py:190,227`
- Modify: `Makefile:45,52`

- [ ] **Step 1: Create and switch to the feature branch**

```bash
git checkout main
git pull
git checkout -b feature/phase-2a-toolchain-swaps
```

Expected: branch created, working tree clean.

- [ ] **Step 2: Remove the `black` dependency from pyproject.toml**

In `pyproject.toml`, delete line 75:

```toml
# DELETE this line:
black = "24.10.0"
```

The file around that line should look like this after deletion (line numbers shift):

```toml
faker = ">=37.0.0"
ruff = "0.12.3"
mypy = "1.13.0"
```

- [ ] **Step 3: Remove the `[tool.black]` section from pyproject.toml**

Delete lines 92-112 in the original file (the section starts immediately after `isort = "^6.0.1"`
and ends with the closing triple-quote). The section to remove:

```toml
[tool.black]
line-length = 88
target-version = ['py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
(
  /(
      \.eggs
    | \.git
    | \.hg
    | \.mypy_cache
    | \.nox
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
  )/
)
'''
```

After deletion, `[tool.ruff]` should follow directly after the dev dependencies block.

- [ ] **Step 4: Fix the E501 ignore comment in pyproject.toml**

In `pyproject.toml`, in the `[tool.ruff.lint]` `ignore` list, change line 166 from:

```toml
    "E501",    # line too long (handled by black)
```

to:

```toml
    "E501",    # line too long (handled by ruff format)
```

- [ ] **Step 5: Add the `[tool.ruff.format]` config block to pyproject.toml**

Insert after the `[tool.ruff.lint.isort]` block (after the `known-first-party` line) and
before the `# Dedicated isort configuration` comment. The current lines in that area:

```toml
[tool.ruff.lint.isort]
known-first-party = ["src"]

# Dedicated isort configuration for import organization
[tool.isort]
```

After insertion:

```toml
[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

# Dedicated isort configuration for import organization
[tool.isort]
```

- [ ] **Step 6: Verify the isort profile in pyproject.toml**

In `pyproject.toml`, in the `[tool.isort]` section, keep the existing value:

```toml
profile = "black"
```

Do not change this to `"ruff"` -- `"ruff"` is not a valid isort profile value. The valid options are: black, django, pycharm, google, open_stack, plone, attrs, hug, wemake, appnexus. The `"black"` profile remains correct and compatible with ruff format.

- [ ] **Step 7: Replace the black invocation in the noxfile.py lint session**

In `noxfile.py`, in the `lint` session, change line 190 from:

```python
    session.run("black", "--check", *args)
```

to:

```python
    session.run("ruff", "format", "--check", *args)
```

The full lint session should look like this after the change:

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
```

- [ ] **Step 8: Replace the black invocation in the noxfile.py format_code session**

In `noxfile.py`, in the `format_code` session, change line 227 from:

```python
    session.run("black", *args)
```

to:

```python
    session.run("ruff", "format", *args)
```

The full format_code session should look like this after the change:

```python
@nox.session(python="3.11")
def format_code(session):
    """Format code."""
    args = session.posargs or SRC_LOCATIONS
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("ruff", "format", *args)
    session.run("ruff", "check", "--fix", *args)
```

- [ ] **Step 9: Replace the black invocations in the Makefile**

In `Makefile`, change the `lint` target (line 45) from:

```makefile
lint: ## Run linting checks
	$(POETRY) run black --check .
```

to:

```makefile
lint: ## Run linting checks
	$(POETRY) run ruff format --check .
```

Then change the `format` target (line 52) from:

```makefile
format: ## Format code
	$(POETRY) run black .
```

to:

```makefile
format: ## Format code
	$(POETRY) run ruff format .
```

- [ ] **Step 10: Sync dependencies to drop black**

```bash
poetry install --sync
```

Expected: Poetry resolves without `black`. Confirm `black` does not appear in output.
Run `poetry show black` to verify it is gone:

```bash
poetry show black
```

Expected: `Package black not found`

- [ ] **Step 11: Verify ruff format produces no diffs**

```bash
poetry run ruff format --check .
```

Expected: exit 0, no files reported as would-be-reformatted. If any files are reported,
run `poetry run ruff format .` to reformat them, then re-run the check.

- [ ] **Step 12: Verify the full lint session is green**

```bash
poetry run nox -s lint
```

Expected: all steps in the session exit 0, no `black` mentioned anywhere in output.

- [ ] **Step 13: Commit Task 6**

```bash
git add pyproject.toml noxfile.py Makefile
git commit -m "refactor(toolchain): replace black with ruff format

Remove black formatter and [tool.black] config. Wire ruff format
as the canonical formatter in noxfile.py lint and format_code
sessions, Makefile lint and format targets, and add [tool.ruff.format]
config block. Update isort profile from 'black' to 'ruff'. No output
change expected for already-formatted files."
```

---

## Task 8: Remove safety, Confirm pip-audit

**Files:**
- Modify: `pyproject.toml:81`
- Modify: `noxfile.py:212-213`
- Modify: `Makefile:56`

- [ ] **Step 1: Remove the `safety` dependency from pyproject.toml**

In `pyproject.toml`, delete line 81 (in original numbering; after Task 6 edits this line
will have shifted -- find it by content):

```toml
# DELETE this line:
safety = ">=3.0.1"
```

After deletion the block should read:

```toml
bandit = {extras = ["toml"], version = "1.7.7"}
detect-secrets = ">=1.5.0"
pre-commit = ">=4.0.0"
```

- [ ] **Step 2: Remove the safety invocation from noxfile.py**

In `noxfile.py`, in the `security` session, delete the two lines (comment + run call):

```python
    # Check for known vulnerabilities
    session.run("safety", "check", "--json")
```

The full security session should look like this after deletion:

```python
@nox.session(python="3.11")
def security(session):
    """Run security checks."""
    session.run("poetry", "install", "--with", "dev", external=True)

    # Run bandit for code security issues
    session.run("bandit", "-r", "src", "-ll")

    # Audit pip packages
    session.run("pip-audit")
```

- [ ] **Step 3: Replace safety in the Makefile security target**

In `Makefile`, change the `security` target (line 56) from:

```makefile
security: ## Run security checks
	$(POETRY) run safety check
	$(POETRY) run bandit -r src
```

to:

```makefile
security: ## Run security checks
	$(POETRY) run pip-audit
	$(POETRY) run bandit -r src
```

- [ ] **Step 4: Sync dependencies to drop safety**

```bash
poetry install --sync
```

Expected: Poetry resolves without `safety`. Confirm it is gone:

```bash
poetry show safety
```

Expected: `Package safety not found`

- [ ] **Step 5: Verify the security session runs bandit and pip-audit only**

```bash
poetry run nox -s security
```

Expected: session output shows `bandit` and `pip-audit` invocations, no `safety`
anywhere in output, session exits 0.

- [ ] **Step 6: Commit Task 8**

```bash
git add pyproject.toml noxfile.py Makefile
git commit -m "refactor(toolchain): remove safety, retain pip-audit

Remove safety vulnerability scanner (redundant with pip-audit which
is already installed and invoked). Remove safety from dev deps,
noxfile.py security session, and Makefile security target. pip-audit
remains as the sole vulnerability scanner."
```

---

## Phase 2a Verification Gate

Run these checks after both commits, before raising the PR:

- [ ] **Format check passes**

```bash
poetry run ruff format --check .
```

Expected: exit 0

- [ ] **Full nox suite is green**

```bash
poetry run nox
```

Expected: all sessions exit 0; `black` and `safety` must not appear in any session output

- [ ] **Security session shows correct tools only**

```bash
poetry run nox -s security
```

Expected: `bandit` and `pip-audit` appear; `safety` does not appear

- [ ] **black and safety are absent from the environment**

```bash
poetry show black && echo "FAIL: black still installed"
poetry show safety && echo "FAIL: safety still installed"
```

Expected: both commands print `Package X not found` (the echo lines must not appear)

- [ ] **Push branch and open PR**

```bash
git push -u origin feature/phase-2a-toolchain-swaps
```

Then open a PR targeting `main`. PR title: `refactor(toolchain): phase 2a -- replace black with ruff format, drop safety`

Do not open the Phase 2b PR until this PR merges.

---

## Self-Review Against Spec

Checked against `docs/superpowers/specs/2026-04-21-phase-2-toolchain-replacements-design.md`
Branch 2a section:

| Spec requirement | Covered |
|-----------------|---------|
| Remove `black = "24.10.0"` from dev deps | Task 6 Step 2 |
| Remove `safety = ">=3.0.1"` from dev deps | Task 8 Step 1 |
| Remove `[tool.black]` section | Task 6 Step 3 |
| Keep `isort.profile` as `"black"` (`"ruff"` is not valid) | Task 6 Step 6 |
| Remove `E501` comment referencing black | Task 6 Step 4 |
| Add `[tool.ruff.format]` config block | Task 6 Step 5 |
| Replace `black --check` in lint session | Task 6 Step 7 |
| Replace `black` in format session | Task 6 Step 8 |
| Remove `safety check --json` from security session | Task 8 Step 2 |
| Replace `black --check` in Makefile lint target | Task 6 Step 9 |
| Replace `black` in Makefile format target | Task 6 Step 9 |
| Replace `safety check` in Makefile security target | Task 8 Step 3 |
| Gate: `ruff format --check .` exits 0 | Verification Step 1 |
| Gate: `nox -s security` shows bandit + pip-audit only | Verification Step 3 |

No spec gaps found. No placeholder text present.
