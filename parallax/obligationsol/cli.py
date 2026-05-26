"""parallax.obligationsol.cli — CLI front-end."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from .checker import ObligationCheckReport, check_obligations


def check_file(path: str, contract_name: Optional[str] = None) -> ObligationCheckReport:
    """Check a .sol file and return a report. Exits with non-zero
    status if any obligation is violated."""
    source = Path(path).read_text()
    name = contract_name or Path(path).stem
    return check_obligations(source, contract_name=name)


def _print_report(report: ObligationCheckReport, verbose: bool = True) -> int:
    """Pretty-print the check report. Return exit code: 0=pass, 1=fail."""
    print(report.summary())
    if not report.results:
        print("  (no @axioms-annotated functions found)")
        return 0
    for ann, res in report.results:
        flag = {"satisfied": "✓",
                "violated": "✗",
                "indeterminate": "?"}.get(res.verdict, "?")
        print(f"  {flag} {ann.function_name}() · {res.obligation}: {res.verdict}")
        if verbose and res.verdict != "satisfied":
            print(f"      {res.explanation}")
            for ln, src in res.evidence_lines[:2]:
                print(f"      L{ln}: {src}")
    print()
    if report.compiles:
        print("✓ ObligationSol check PASSED — contract compiles.")
        return 0
    else:
        print(f"✗ ObligationSol check FAILED — {len(report.violations)} obligation(s) violated. REJECTING compilation.")
        return 1


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: parallax obligationsol-check <file.sol> [--contract NAME]")
        return 0
    path = argv[0]
    cname = None
    if "--contract" in argv:
        cname = argv[argv.index("--contract") + 1]
    report = check_file(path, contract_name=cname)
    return _print_report(report, verbose=True)


if __name__ == "__main__":
    sys.exit(main())
