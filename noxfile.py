"""Nox sessions for testing, linting, and security checks."""

import nox

# Python versions to test
PYTHON_VERSIONS = ["3.11", "3.12"]

# Source locations
SRC_LOCATIONS = ["src", "tests", "noxfile.py"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run the full test suite (all layers)."""
    args = session.posargs or [
        "--cov",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
    ]
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("pytest", *args)


# ==========================================
# LAYERED TESTING SESSIONS (Test Pyramid)
# ==========================================


@nox.session(python=PYTHON_VERSIONS)
def unit(session):
    """Run unit tests only (fast development cycle)."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "-m",
        "not component and not contract and not integration and not e2e and not perf "
        "and not chaos and not slow",
        "--cov=src",
        "--cov-branch",
        "--cov-fail-under=80",
        "-v",
        *session.posargs,
    )


@nox.session
def component(session):
    """Run component tests (with mocks)."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "-m",
        "component",
        "--cov=src",
        "--cov-branch",
        "--cov-fail-under=75",
        "-v",
        *session.posargs,
    )


@nox.session
def db_tests(session):
    """Run database tests (PostgreSQL integration)."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "-m",
        "database",
        "--cov=src/security_master/storage",
        "--cov-branch",
        "--cov-fail-under=75",
        "-v",
        *session.posargs,
    )


@nox.session
def classifier_tests(session):
    """Run classification engine tests."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "-m",
        "classifier",
        "--cov=src/security_master/classifier",
        "--cov-branch",
        "--cov-fail-under=85",
        "-v",
        *session.posargs,
    )


@nox.session
def extractor_tests(session):
    """Run broker file extraction tests."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "-m",
        "extractor",
        "--cov=src/security_master/extractor",
        "--cov-branch",
        "--cov-fail-under=85",
        "-v",
        *session.posargs,
    )


@nox.session
def fast(session):
    """Fast development loop - exclude slow tests."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "-m",
        "not slow",
        "--cov=src",
        "--cov-branch",
        "--cov-fail-under=75",  # Slightly lower for fast feedback
        "--maxfail=5",
        "-v",
        *session.posargs,
    )


@nox.session
def security_tests(session):
    """Run security assertion tests."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "-m",
        "security",
        "-v",
        *session.posargs,
    )


@nox.session
def integration(session):
    """Run integration tests (slower, real services)."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "-m",
        "integration",
        "--cov=src",
        "--cov-branch",
        "-v",
        *session.posargs,
    )


@nox.session
def e2e(session):
    """Run end-to-end tests (full user journeys)."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "-m",
        "e2e",
        "-v",
        "--tb=short",
        *session.posargs,
    )


@nox.session
def perf(session):
    """Run performance and load tests."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "-m",
        "perf or performance",  # Include legacy marker
        "-v",
        "--tb=short",
        "--durations=10",
        *session.posargs,
    )


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


@nox.session(python="3.11")
def type_check(session):
    """Run type checking with basedpyright."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("basedpyright")


@nox.session(python="3.11")
def security(session):
    """Run security checks."""
    session.run("poetry", "install", "--with", "dev", external=True)

    # Run bandit for code security issues
    session.run("bandit", "-r", "src", "-ll")

    # Audit pip packages
    # Accepted unfixable CVEs documented in docs/known-vulnerabilities.md
    session.run(
        "pip-audit",
        "--ignore-vuln",
        "GHSA-4xh5-x5gv-qwph",  # pip 25.2 -- system pip, outside project control
        "--ignore-vuln",
        "GHSA-6vgw-5pg2-w6jp",  # pip 25.2 -- system pip, outside project control
        "--ignore-vuln",
        "PYSEC-2022-42969",  # py 1.11.0 -- transitive via interrogate, ReDoS not triggered
    )


@nox.session(python="3.11")
def format_code(session):
    """Format code."""
    args = session.posargs or SRC_LOCATIONS
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("ruff", "format", *args)
    session.run("ruff", "check", "--fix", *args)


@nox.session(python="3.11")
def pre_commit(session):
    """Run pre-commit on all files."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("pre-commit", "run", "--all-files")
