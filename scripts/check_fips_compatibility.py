#!/usr/bin/env python3
"""FIPS 140-2/140-3 compatibility check (Phase 1 stub).

This is a minimal placeholder so the `FIPS Compatibility` workflow can run
during Phase 1 of the CI modernization. It emits the JSON shape consumed
by `.github/workflows/fips-compatibility.yml` (a `summary` object with
`errors`, `warnings`, and `info` integer counts) and always exits 0.

Real FIPS scanning, fix-hint generation, and strict-mode promotion are
deferred until the application code lands in a later phase.
"""

from __future__ import annotations

import argparse
import json
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FIPS 140-2/140-3 compatibility check (Phase 1 stub).",
    )
    parser.add_argument(
        "--fix-hints",
        action="store_true",
        help="Print hints to remediate flagged usages (no-op in the Phase 1 stub).",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include tests/ in the scan (no-op in the Phase 1 stub).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (no-op in the Phase 1 stub).",
    )
    parser.add_argument(
        "--json",
        dest="emit_json",
        action="store_true",
        help="Emit a machine-readable JSON report on stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    summary = {"errors": 0, "warnings": 0, "info": 0}
    report = {"summary": summary, "findings": []}

    if args.emit_json:
        json.dump(report, sys.stdout)
        sys.stdout.write("\n")
    else:
        print("FIPS compatibility check (Phase 1 stub): no findings.")
        if args.fix_hints:
            print("No fix hints to emit; the stub does not perform analysis.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
