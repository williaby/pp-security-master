# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Replace `mypy` with `basedpyright` in strict mode across `pyproject.toml`, `noxfile.py`, `Makefile`, and `.github/workflows/ci.yml`
- Remove `[tool.mypy]`, `[[tool.mypy.overrides]]`, and `[tool.pydantic-mypy]` config blocks from `pyproject.toml`; add `[tool.basedpyright]` block with `typeCheckingMode = "strict"`
- Replace `datetime.utcnow` (deprecated) with `lambda: datetime.now(UTC).replace(tzinfo=None)` across all model `server_default` fields in `models.py`, `pp_models.py`, and `transaction_models.py`
- Upgrade to SQLAlchemy 2.x `create_mock_engine` in `schema_export.py`; add `checkfirst=False` to `Base.metadata.create_all` so mock engine emits all CREATE TABLE statements
- Tighten type annotations in `mappers.py` (bare `dict` and `list[dict]` to `dict[str, Any]` / `list[dict[str, Any]]`) and `validators.py` (`list[str]` annotations on local variables)
- Switch XML generation in `pp_xml_export.py` to stdlib `xml.etree.ElementTree` while keeping `defusedxml` for all parsing operations
- Replace `black` formatter with `ruff format` across `noxfile.py`, `Makefile`, and CI workflow
- Replace `safety` vulnerability scanner with `pip-audit` in `noxfile.py`, `Makefile`, and CI workflow
- Fix CI `Run linting` step to call `ruff format --check` instead of removed `black` binary
- Correct `[tool.ruff.lint.isort]` `known-first-party` from `"src"` to `"security_master"` (actual importable package name)
- Correct planning docs: `"ruff"` is not a valid isort profile; keep `profile = "black"` in `[tool.isort]`
- Add `COM812` to `lint.ignore`; ruff format and COM812 conflict by design (ruff's own warning)

### Fixed

- Broaden `except` clause in `PPXMLExportService.validate_export` to catch `defusedxml.DefusedXmlException` in addition to `ET.ParseError`; defusedxml security violations do not inherit from `ParseError`
- Add `try/except defusedxml.DefusedXmlException` around `defused_minidom.parseString()` in `_prettify_xml` to convert XML security violations to `ValueError` instead of propagating unhandled

