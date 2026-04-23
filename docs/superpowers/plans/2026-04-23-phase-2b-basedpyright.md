# Phase 2b: BasedPyright Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace MyPy with BasedPyright in strict mode, fix all surfaced type errors module by module, and land a clean type-checked codebase with zero suppressions.

**Architecture:** Config swap in one commit (pyproject.toml, noxfile.py, Makefile), then type fixes committed per module in bottom-up dependency order (storage, patch, root). Each module commit is conditional -- skip if that module has zero errors. A cross-module commit handles any signature ripples across module boundaries. The branch does not close until `basedpyright` exits 0.

**Tech Stack:** Python 3.11+, Poetry, BasedPyright >=1.1.400, SQLAlchemy 2.0 (Mapped[] ORM), nox, Make

**Spec:** `docs/superpowers/specs/2026-04-21-phase-2-toolchain-replacements-design.md` (Branch 2b section)

**Prerequisite:** Branch `feature/phase-2a-toolchain-swaps` merged to main (PR #10, confirmed merged 2026-04-23).

---

## File Structure

| File | Change |
|------|--------|
| `pyproject.toml` | Remove `mypy`, `types-pyyaml`, `types-python-dateutil` deps (lines 76-78); add `basedpyright = ">=1.1.400"`; remove `[tool.mypy]`, `[[tool.mypy.overrides]]` x2, `[tool.pydantic-mypy]` sections (lines 191-224); add `[tool.basedpyright]` block after line 175 |
| `noxfile.py` | Update `type_check` session docstring + command (lines 202, 204) |
| `Makefile` | Update lint target mypy invocation (line 47) |
| `src/security_master/storage/*.py` | Fix all BasedPyright strict errors (count unknown until triage) |
| `src/security_master/patch/*.py` | Fix all BasedPyright strict errors (count unknown until triage) |
| `src/security_master/*.py` | Fix any errors in cli.py, utils.py, `__init__.py` |

---

## Task 1: Create branch and swap MyPy for BasedPyright

**Files:**
- Modify: `pyproject.toml` (lines 76-78, 175-176, 191-224)
- Modify: `noxfile.py` (lines 202, 204)
- Modify: `Makefile` (line 47)

- [ ] **Step 1: Create the feature branch**

```bash
git checkout main
git pull
git checkout -b feature/phase-2b-basedpyright
```

Expected: branch created, working tree clean.

- [ ] **Step 2: Record the MyPy baseline**

```bash
poetry run mypy src 2>&1 | tail -3
```

Note the final line (e.g., `Found N errors in M files`). This is the baseline. BasedPyright strict will surface more.

- [ ] **Step 3: Remove mypy and stubs from pyproject.toml dev dependencies**

In `pyproject.toml`, remove lines 76-78:

```toml
mypy = "1.13.0"
types-pyyaml = ">=6.0.12.12"
types-python-dateutil = ">=2.8.19.20240106"
```

After deletion the block around that area reads:

```toml
faker = ">=37.0.0"
ruff = "0.12.3"
bandit = {extras = ["toml"], version = "1.7.7"}
```

- [ ] **Step 4: Add basedpyright to dev dependencies**

In `pyproject.toml`, after `ruff = "0.12.3"` (now line 75 after the removal), add:

```toml
basedpyright = ">=1.1.400"
```

The block should now read:

```toml
ruff = "0.12.3"
basedpyright = ">=1.1.400"
bandit = {extras = ["toml"], version = "1.7.7"}
```

- [ ] **Step 5: Remove [tool.mypy] and related sections from pyproject.toml**

Delete the entire block from `[tool.mypy]` through the end of `[tool.pydantic-mypy]` (lines 191-224 in the original file -- find by content after the earlier edits shifted line numbers):

```toml
[tool.mypy]
python_version = "3.11"
mypy_path = "src"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = ["tests.*", "scripts.*", "noxfile"]
ignore_errors = true

[[tool.mypy.overrides]]
module = [
    "psycopg2.*",
    "alembic.*",
    "defusedxml.*",
]
ignore_missing_imports = true

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true
warn_untyped_fields = true
```

After deletion, `[tool.pytest.ini_options]` should follow directly after the `[tool.isort]` block.

- [ ] **Step 6: Add [tool.basedpyright] config to pyproject.toml**

Insert after the `[tool.ruff.format]` block (after `line-ending = "auto"` and before the `# Dedicated isort configuration` comment). The insertion point currently reads:

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

# Dedicated isort configuration for import organization
[tool.isort]
```

Change it to:

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.basedpyright]
pythonVersion = "3.11"
pythonPlatform = "All"
typeCheckingMode = "strict"
strictListInference = true
strictDictionaryInference = true
strictSetInference = true

# Dedicated isort configuration for import organization
[tool.isort]
```

- [ ] **Step 7: Update noxfile.py type_check session**

In `noxfile.py`, the `type_check` session currently reads (lines 200-204):

```python
@nox.session(python="3.11")
def type_check(session):
    """Run type checking with mypy."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("mypy", "src")
```

Change to:

```python
@nox.session(python="3.11")
def type_check(session):
    """Run type checking with basedpyright."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("basedpyright")
```

- [ ] **Step 8: Update Makefile lint target**

In `Makefile`, line 47, change:

```makefile
	$(POETRY) run mypy src
```

to:

```makefile
	$(POETRY) run basedpyright
```

The full lint target should now read:

```makefile
lint: ## Run linting checks
	$(POETRY) run ruff format --check .
	$(POETRY) run ruff check .
	$(POETRY) run basedpyright
	markdownlint **/*.md
	yamllint .
```

- [ ] **Step 9: Verify pyproject.toml is valid TOML**

```bash
python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" && echo "Valid TOML"
```

Expected: `Valid TOML`. If it fails, open `pyproject.toml` and look for an unclosed string or missing bracket near the edited sections.

- [ ] **Step 10: Sync dependencies**

```bash
poetry install --sync
```

Expected: Poetry resolves without `mypy`, `types-pyyaml`, or `types-python-dateutil`. Confirm:

```bash
poetry show mypy 2>&1 | head -1
poetry show basedpyright 2>&1 | head -1
```

Expected: `Package mypy not found` for the first, a version line for the second.

- [ ] **Step 11: Verify basedpyright is callable**

```bash
poetry run basedpyright --version
```

Expected: prints a version string such as `basedpyright 1.1.x`.

- [ ] **Step 12: Commit the config swap**

```bash
git add pyproject.toml noxfile.py Makefile
git commit -m "refactor(toolchain): replace MyPy with BasedPyright in strict mode (config only)

Remove mypy 1.13.0 and type stubs. Remove [tool.mypy] and [tool.pydantic-mypy]
config sections. Add basedpyright >=1.1.400 with strict typeCheckingMode.
Update noxfile.py type_check session and Makefile lint target.
Type error fixes follow in subsequent commits.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Triage basedpyright errors

**Files:** none (discovery only, no commit)

- [ ] **Step 1: Run full basedpyright and capture output**

```bash
poetry run basedpyright 2>&1 | tee /tmp/bp-full.txt
tail -5 /tmp/bp-full.txt
```

The last line reports the total: `X errors, Y warnings, Z informations`.

- [ ] **Step 2: Count errors per file**

```bash
grep " - error:" /tmp/bp-full.txt \
  | sed 's|.*/security_master/||' \
  | cut -d: -f1 \
  | sort | uniq -c | sort -rn
```

This shows which files have the most errors. Record the output -- it drives the ordering of Tasks 3-5.

- [ ] **Step 3: List distinct error rule codes**

```bash
grep " - error:" /tmp/bp-full.txt \
  | grep -oP '\(report\w+\)' \
  | sort | uniq -c | sort -rn
```

Common codes you will see in this codebase and what they mean:

| Code | Meaning | Fix pattern |
|------|---------|------------|
| `reportUnknownParameterType` | Parameter typed as bare `dict` or `list[dict]` | Add type params: `dict[str, Any]` |
| `reportUnknownVariableType` | Local variable type cannot be inferred | Add explicit annotation: `result: list[Model] = ...` |
| `reportUnknownMemberType` | Member access on `Unknown` type | Narrow with `isinstance` or explicit `cast()` |
| `reportMissingTypeArgument` | Generic used without type arguments | Add type args: `list[str]` not `list` |
| `reportReturnType` | Return value incompatible with declared type | Fix the declared type or the return expression |
| `reportOperatorIssue` | Operation on potentially `None` | Add `assert value is not None` or `if value is None: return` guard before use |

- [ ] **Step 4: If total errors exceed 50, plan sub-commits within each module**

If the error count for `storage/` exceeds 30, note the specific files (e.g., `models.py`, `views.py`) that need separate commits. The per-module tasks below are still correct; you will just need one commit per file instead of one per directory.

If error count is under 50, proceed with one commit per module as planned.

---

## Task 3: Fix type errors in storage/

**Files:**
- Modify: `src/security_master/storage/database.py`
- Modify: `src/security_master/storage/models.py`
- Modify: `src/security_master/storage/validators.py`
- Modify: `src/security_master/storage/mappers.py`
- Modify: `src/security_master/storage/transaction_models.py`
- Modify: `src/security_master/storage/pp_models.py`
- Modify: `src/security_master/storage/schema_export.py`
- Modify: `src/security_master/storage/views.py`

- [ ] **Step 1: Run basedpyright scoped to storage/**

```bash
poetry run basedpyright src/security_master/storage/ 2>&1 | tee /tmp/bp-storage.txt
grep -c " - error:" /tmp/bp-storage.txt || echo "0 errors"
```

If this prints `0 errors`, skip to Task 4. Do not create an empty commit.

- [ ] **Step 2: Fix each error reported in storage/**

Work through errors from `/tmp/bp-storage.txt` one file at a time. Apply these patterns:

**Pattern A -- bare `dict` parameter (confirmed in `mappers.py:205-206`):**

In `src/security_master/storage/mappers.py`, the `find_best_match` classmethod uses untyped dicts. Change:

```python
@classmethod
def find_best_match(
    cls,
    pp_security: dict,
    kubera_holdings: list[dict],
) -> dict | None:
```

to:

```python
@classmethod
def find_best_match(
    cls,
    pp_security: dict[str, Any],
    kubera_holdings: list[dict[str, Any]],
) -> dict[str, Any] | None:
```

Confirm `from typing import Any` is already at the top of `mappers.py` (line 1 -- it is). No new import needed.

**Pattern B -- `sessionmaker` return type in `database.py`:**

BasedPyright strict may flag `get_session_factory`'s return type `Callable[[], Session]` because `sessionmaker(...)` returns `sessionmaker[Session]`, which accepts keyword arguments. If flagged, change:

```python
def get_session_factory(engine: Engine) -> Callable[[], Session]:
    """Create session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

to:

```python
def get_session_factory(engine: Engine) -> "sessionmaker[Session]":
    """Create session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

Add `sessionmaker` to the import at the top of `database.py` if it is not already imported by name (it is -- line 5 imports `sessionmaker` from `sqlalchemy.orm`). Remove `Callable` from the import if it is no longer used elsewhere in the file.

**Pattern C -- SQLAlchemy `Unknown` return types:**

If `.query(Model).filter().first()` results are assigned without annotation and BasedPyright cannot infer the type, add an explicit annotation:

```python
# Before (BasedPyright sees Unknown)
result = self.session.query(KuberaSheet).filter_by(sheet_id=sheet_id).first()

# After (explicit Optional type)
result: KuberaSheet | None = (
    self.session.query(KuberaSheet).filter_by(sheet_id=sheet_id).first()
)
```

**Pattern D -- `Unknown` local variable:**

If a local variable has an inferred type of `Unknown` (e.g., from a third-party return), annotate it explicitly:

```python
# Before
data = defusedxml.ElementTree.parse(path)

# After
from xml.etree.ElementTree import ElementTree as ET
data: ET = defusedxml.ElementTree.parse(path)
```

- [ ] **Step 3: Re-run basedpyright on storage/ until clean**

```bash
poetry run basedpyright src/security_master/storage/
```

Repeat Step 2 for any remaining errors. Do not proceed until this exits with 0 errors.

- [ ] **Step 4: Confirm no ruff regressions**

```bash
poetry run ruff check src/security_master/storage/
```

Expected: 0 violations. If any appear from the type fix edits (e.g., an `Any` import that needs `TYPE_CHECKING`), fix them before committing.

- [ ] **Step 5: Commit storage fixes**

```bash
git add src/security_master/storage/
git commit -m "fix(types): resolve BasedPyright strict errors in storage/

Fixes reportUnknownParameterType in mappers.py find_best_match,
and any additional strict-mode errors surfaced in database.py,
models.py, validators.py, transaction_models.py, pp_models.py,
schema_export.py, and views.py.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Fix type errors in patch/

**Files:**
- Modify: `src/security_master/patch/pp_xml_export.py`

**Root cause (confirmed by pre-run):** `pp_xml_export.py` generates 95+ `reportAttributeAccessIssue` errors because it imports from `defusedxml` for XML *building*, but `defusedxml` has no type stubs. This is also architecturally wrong: `defusedxml` is a secure XML *parser* (prevents XXE attacks); it should not be used as a builder. The correct fix is replacing all `defusedxml` imports with the stdlib `xml.etree.ElementTree`, which has full type stubs.

- [ ] **Step 1: Run basedpyright scoped to patch/**

```bash
poetry run basedpyright src/security_master/patch/ 2>&1 | tee /tmp/bp-patch.txt
grep -c " - error:" /tmp/bp-patch.txt || echo "0 errors"
```

If this prints `0 errors`, skip to Task 5. Do not create an empty commit.

- [ ] **Step 2: Replace defusedxml imports with stdlib**

In `src/security_master/patch/pp_xml_export.py`, the current import block at lines 9-11 is:

```python
from defusedxml import ElementTree
from defusedxml import ElementTree as safe_ET
from defusedxml import minidom as safe_minidom
```

Replace those three lines with:

```python
import xml.etree.ElementTree as ET
from xml.dom import minidom
```

The `safe_ET` alias was used only in `validate_export` (one `safe_ET.fromstring()` call). The `safe_minidom` alias was used only in `_prettify_xml`. Both are covered by the replacements above.

- [ ] **Step 3: Update all call sites in pp_xml_export.py**

There are four name patterns to replace across the file (do not search/replace blindly -- verify each occurrence):

| Old name | New name | Count | Where used |
| -------- | -------- | ----- | ---------- |
| `ElementTree.Element(` | `ET.Element(` | 1 | `generate_complete_backup` root creation |
| `ElementTree.SubElement(` | `ET.SubElement(` | ~40 | Every section-builder method |
| `ElementTree.tostring(` | `ET.tostring(` | 1 | `_prettify_xml` |
| `safe_minidom.parseString(` | `minidom.parseString(` | 1 | `_prettify_xml` |
| `safe_ET.fromstring(` | `ET.fromstring(` | 1 | `validate_export` |
| `ElementTree.ParseError` | `ET.ParseError` | 1 | `validate_export` except clause |

To apply all replacements at once using sed (run from the worktree root):

```bash
sed -i \
  -e 's/ElementTree\.Element(/ET.Element(/g' \
  -e 's/ElementTree\.SubElement(/ET.SubElement(/g' \
  -e 's/ElementTree\.tostring(/ET.tostring(/g' \
  -e 's/safe_minidom\.parseString(/minidom.parseString(/g' \
  -e 's/safe_ET\.fromstring(/ET.fromstring(/g' \
  -e 's/ElementTree\.ParseError/ET.ParseError/g' \
  src/security_master/patch/pp_xml_export.py
```

After running sed, verify the file has no remaining references to `defusedxml`, `safe_ET`, `safe_minidom`, or bare `ElementTree.`:

```bash
grep -n "defusedxml\|safe_ET\|safe_minidom\|ElementTree\." \
  src/security_master/patch/pp_xml_export.py
```

Expected: no output (zero matches). If any remain, fix them manually.

- [ ] **Step 4: Verify the type annotation on _prettify_xml**

The `_prettify_xml` method takes an `ElementTree.Element` parameter. After the rename, the signature at line 437 should read:

```python
def _prettify_xml(self, elem: ET.Element) -> str:
```

Confirm this is correct in the file. The return type `ET.tostring(elem, "unicode")` returns `str`, and `minidom.parseString(rough_string)` takes a `str` -- both are typed correctly in stdlib.

- [ ] **Step 5: Re-run basedpyright on patch/ until clean**

```bash
poetry run basedpyright src/security_master/patch/
```

Expected: 0 errors. If any remain (e.g., SQLAlchemy Unknown types from `.query().all()` calls), add explicit type annotations:

```python
# Before (Unknown inferred type)
securities = self.session.query(SecurityMaster).all()

# After (explicit annotation)
securities: list[SecurityMaster] = self.session.query(SecurityMaster).all()
```

Repeat until `basedpyright src/security_master/patch/` exits 0.

- [ ] **Step 6: Confirm no ruff regressions**

```bash
poetry run ruff check src/security_master/patch/
```

Expected: 0 violations. If ruff flags the new `import xml.etree.ElementTree as ET` import order, run `ruff check --fix src/security_master/patch/` to auto-sort.

- [ ] **Step 7: Commit patch fixes**

```bash
git add src/security_master/patch/
git commit -m "fix(types): replace defusedxml with stdlib ET in pp_xml_export.py

defusedxml has no type stubs and is architecturally incorrect for an
XML builder (it is a secure parser). Replace with xml.etree.ElementTree
(stdlib, fully typed) and xml.dom.minidom. Resolves 95+ BasedPyright
reportAttributeAccessIssue errors in patch/.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Fix type errors in root-level src/ files

**Files:**
- Modify (if needed): `src/security_master/cli.py`
- Modify (if needed): `src/security_master/utils.py`
- Modify (if needed): `src/security_master/__init__.py`

- [ ] **Step 1: Run basedpyright on root-level src/ files**

```bash
poetry run basedpyright \
  src/security_master/cli.py \
  src/security_master/utils.py \
  src/security_master/__init__.py \
  2>&1 | tee /tmp/bp-root.txt
grep -c " - error:" /tmp/bp-root.txt || echo "0 errors"
```

`cli.py` and `utils.py` are currently 1-line stubs. This is likely 0 errors. If so, skip to Task 6.

- [ ] **Step 2: Fix any errors found**

Apply the same patterns from Tasks 3-4. For stub files with no content, BasedPyright has nothing to check.

- [ ] **Step 3: Re-run basedpyright on root-level files until clean**

```bash
poetry run basedpyright src/security_master/cli.py src/security_master/utils.py src/security_master/__init__.py
```

- [ ] **Step 4: Commit root-level fixes (skip if no changes)**

```bash
git diff --quiet src/security_master/cli.py src/security_master/utils.py src/security_master/__init__.py \
  || git add src/security_master/cli.py src/security_master/utils.py src/security_master/__init__.py \
  && git commit -m "fix(types): resolve BasedPyright strict errors in root src/ files

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Handle cross-module errors (conditional)

This task exists only if fixing one module exposed a type incompatibility in a module already committed. Example: changing a return type in `storage/mappers.py` breaks a call site in `patch/pp_xml_export.py`.

**Files:** whichever modules need follow-up after full-suite run

- [ ] **Step 1: Run full basedpyright suite**

```bash
poetry run basedpyright 2>&1 | tee /tmp/bp-final-check.txt
tail -3 /tmp/bp-final-check.txt
```

If the output reads `0 errors, 0 warnings`, skip to Task 7.

- [ ] **Step 2: Fix any cross-module errors**

For each remaining error, apply the fix in the file it appears in. These will be errors in modules already committed where a type change in a dependency caused a downstream mismatch.

Common cause: a function in `storage/` changed its return type from `X | None` to `X` (or vice versa) and call sites in `patch/` still treat the old type.

Fix: update the call site to match the new contract. Do not weaken the storage signature to silence the error.

- [ ] **Step 3: Commit cross-module fixes**

```bash
git add src/
git commit -m "fix(types): resolve cross-module BasedPyright errors after per-module fixes

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Verification gate and PR

**Files:** none (verification only, then PR)

- [ ] **Step 1: Run full basedpyright -- must exit 0**

```bash
poetry run basedpyright
```

Expected: final line reads `0 errors, 0 warnings, 0 informations` (or `0 errors` and some informational notes -- informations are not blocking). If any errors remain, go back and fix them before proceeding.

- [ ] **Step 2: Run the nox type_check session end-to-end**

```bash
poetry run nox -s type_check
```

Expected: exits 0. This confirms the session wiring in noxfile.py is correct.

- [ ] **Step 3: Run the full nox lint session**

```bash
poetry run nox -s lint
```

Expected: exits 0. Confirms that type-fix edits introduced no ruff violations. If ruff fails, fix violations and amend the relevant commit on the branch (or add a follow-up fix commit).

- [ ] **Step 4: Confirm mypy is gone**

```bash
poetry show mypy 2>&1 | head -1
```

Expected: `Package mypy not found`.

- [ ] **Step 5: Confirm no suppressions were introduced**

```bash
grep -rn "# type: ignore\|# pyright: ignore" src/ || echo "No suppressions -- clean"
```

Expected: `No suppressions -- clean`. If any appear, fix the underlying type error instead.

- [ ] **Step 6: Push branch and open PR**

```bash
git push -u origin feature/phase-2b-basedpyright
```

Open a PR targeting `main`. Use this title and body:

**Title:** `refactor(toolchain): replace MyPy with BasedPyright in strict mode`

**Body:**
```
## Summary

- Removes MyPy 1.13.0 and type stubs (pyyaml, python-dateutil)
- Removes [tool.mypy] and [tool.pydantic-mypy] config sections
- Adds BasedPyright >=1.1.400 with strict typeCheckingMode
- Fixes all type errors surfaced by strict mode (committed per module)
- Zero type: ignore suppressions introduced

## Verification

- `poetry run basedpyright` exits 0
- `poetry run nox -s type_check` passes
- `poetry run nox -s lint` passes

## Phase gate

Phase 2c (Tasks 9-11: darglint, interrogate, qlty, Ruff rule expansion)
does not begin until this PR merges.
```

---

## Self-Review

### Spec Coverage Check

| Spec requirement (Branch 2b section) | Covered by task |
|--------------------------------------|----------------|
| Remove `mypy = "1.13.0"` from dev deps | Task 1 Step 3 |
| Remove `types-pyyaml`, `types-python-dateutil` from dev deps | Task 1 Step 3 |
| Add `basedpyright = ">=1.1.400"` to dev deps | Task 1 Step 4 |
| Remove `[tool.mypy]` section | Task 1 Step 5 |
| Remove `[[tool.mypy.overrides]]` sections (x2) | Task 1 Step 5 |
| Remove `[tool.pydantic-mypy]` section | Task 1 Step 5 |
| Add `[tool.basedpyright]` config block | Task 1 Step 6 |
| Update noxfile.py `type_check` session | Task 1 Step 7 |
| Update Makefile `lint` target | Task 1 Step 8 |
| Fix all type errors (no suppressions) | Tasks 3-6 |
| Suppression policy: no `# type: ignore` | Task 7 Step 5 |
| Verification gate: `basedpyright` exits 0 | Task 7 Step 1 |
| Verification gate: `nox -s type_check` passes | Task 7 Step 2 |
| Branch does not close until 0 errors | Task 7 Step 1 |

All spec requirements covered. No gaps found.

### Placeholder Check

No TBD, TODO, or "fill in later" text in any step. Every code block contains actual content. Conditional skip instructions ("If 0 errors, skip to Task N") are explicit decisions, not deferred content.

### Type Consistency Check

`dict[str, Any]` is used consistently in Task 3 Pattern A for `mappers.py`. The `Any` import in `mappers.py` line 1 is already present -- no new import needed. `KuberaSheet | None` annotation pattern in Task 3 Pattern C matches the existing `-> KuberaSheet:` return type in the same file (confirmed in codebase). No naming inconsistencies across tasks.
