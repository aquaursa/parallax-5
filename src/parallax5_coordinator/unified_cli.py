"""Unified parallax5 CLI dispatcher.

Routes subcommands to the appropriate handler:
  - v8 subcommands (init, doctor, quote, score, audit-import, challenge):
    go to parallax5_cli (click-based)
  - v9 subcommands (registry, certify, mapping, capability, analyze, theorems,
    and validate against the canonical schema): go to parallax5_coordinator.cli
    (argparse-based)

The dispatcher uses sys.argv[1] to route. Unknown subcommands and --help
default to v9 (the current substrate's primary CLI).
"""
from __future__ import annotations
import sys

# Practical commands (insurance quoting, doctor, audit import, etc.)
V8_SUBCOMMANDS = frozenset({
    "init", "doctor", "quote", "score", "audit-import", "challenge",
})

# v9 commands: the coordinator surface (schema validation, registry, etc.)
V9_SUBCOMMANDS = frozenset({
    "registry", "certify", "mapping", "capability", "analyze", "theorems", "validate",
})


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        # Show a combined help banner, then defer to v9 for the standard help
        _print_combined_help()
        sys.exit(0)

    cmd = sys.argv[1]

    # Special-case validate: auto-detect cert format and dispatch
    if cmd == "validate" and len(sys.argv) >= 3:
        cert_path = sys.argv[2]
        try:
            import json, pathlib
            cert = json.loads(pathlib.Path(cert_path).read_text())
            # v9 (Phase I) schema fields are top-level
            is_v9 = "obligation_coverage" in cert or "crops_vector" in cert
            if is_v9:
                from parallax5_coordinator.cli import main as v9_main
                v9_main()
                return
            # Otherwise v8 (legacy schema with compliance_level / obligation_map)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        # Fall through to v8 for legacy certs
        try:
            from parallax5_cli.__main__ import cli
        except ImportError as e:
            print(f"ERROR: parallax5_cli package not installed: {e}", file=sys.stderr)
            sys.exit(2)
        cli()
        return

    if cmd in V8_SUBCOMMANDS:
        try:
            from parallax5_cli.__main__ import cli
        except ImportError as e:
            print(f"ERROR: parallax5_cli package not installed: {e}", file=sys.stderr)
            sys.exit(2)
        cli()
    else:
        # v9 (or unknown, which will fall through to v9's argparse error)
        from parallax5_coordinator.cli import main as v9_main
        v9_main()


def _print_combined_help() -> None:
    print("PARALLAX-5 unified CLI")
    print()
    print("Usage: parallax5 <subcommand> [options]")
    print()
    print("Coordinator subcommands:")
    print("  validate      Validate a v1.0 certificate against the schema")
    print("  certify       Produce a certificate from a parallax.yaml spec")
    print("  registry      submit | state — interact with the onchain registry")
    print("  capability    Show the per-tool capability matrix")
    print("  mapping       Show the TOOL-MAPPING calibration")
    print("  analyze       Run the coordinator's full tool stack on a contract")
    print("  theorems      Run the 2,152 compositional theorem checks")
    print()
    print("Practical subcommands:")
    print("  init          Author a baseline v8-schema certificate")
    print("  doctor        Inspect a repo for compliance gaps")
    print("  quote         Compute an indicative insurance premium")
    print("  score         Run Slither against a contract, emit a P2 certificate")
    print("  audit-import  Convert a structured audit report to a certificate")
    print("  challenge     Submit a basis-counterexample challenge")
    print()
    print("For per-subcommand help, run:")
    print("  parallax5 <subcommand> --help")
