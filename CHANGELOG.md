# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Replace `black` formatter with `ruff format` across `noxfile.py`, `Makefile`, and CI workflow
- Replace `safety` vulnerability scanner with `pip-audit` in `noxfile.py`, `Makefile`, and CI workflow
- Fix CI `Run linting` step to call `ruff format --check` instead of removed `black` binary
- Correct `[tool.ruff.lint.isort]` `known-first-party` from `"src"` to `"security_master"` (actual importable package name)
- Correct planning docs: `"ruff"` is not a valid isort profile; keep `profile = "black"` in `[tool.isort]`
