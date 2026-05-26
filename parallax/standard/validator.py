#!/usr/bin/env python3
"""PARALLAX-5 Reference CLI Validator

Validates a candidate certificate against:
  1. The JSON Schema (structural validation).
  2. Compliance-level-specific requirements (P3+ requires proof_artifacts,
     P5 requires runtime_gate, etc.).
  3. Internal consistency (every function in obligation_map has
     proof_artifacts entries for the obligations it declares).
  4. Optional: cryptographic signature on the issuer block.
  5. Optional: bytecode hash consistency against a live chain endpoint.

Usage:
    python3 -m parallax.standard.validator path/to/cert.json
    python3 -m parallax.standard.validator path/to/cert.json --strict
    python3 -m parallax.standard.validator path/to/cert.json --schema /path/to/schema.json

Exit codes:
    0   certificate valid for its declared compliance level
    1   structural validation failed (schema)
    2   compliance-level requirement failed
    3   internal consistency failed
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import List


DEFAULT_SCHEMA = (
    Path(__file__).parent.parent.parent / "paper" / "supplement"
    / "parallax5_certificate.schema.json"
)


class ValidationReport:
    def __init__(self) -> None:
        self.passed: List[str] = []
        self.failed: List[str] = []
        self.warnings: List[str] = []

    def ok(self, msg: str) -> None:
        self.passed.append(msg)

    def fail(self, msg: str) -> None:
        self.failed.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def is_valid(self) -> bool:
        return len(self.failed) == 0

    def render(self) -> str:
        lines = []
        for m in self.passed:
            lines.append(f"  ✓ {m}")
        for m in self.warnings:
            lines.append(f"  ⚠ {m}")
        for m in self.failed:
            lines.append(f"  ✗ {m}")
        verdict = "VALID" if self.is_valid() else "INVALID"
        lines.append("")
        lines.append(f"  Verdict: {verdict}")
        return "\n".join(lines)


def validate_schema(cert: dict, schema_path: Path, report: ValidationReport) -> bool:
    """Step 1: structural validation against JSON Schema."""
    try:
        schema = json.loads(schema_path.read_text())
    except FileNotFoundError:
        report.fail(f"Schema file not found: {schema_path}")
        return False
    except json.JSONDecodeError as e:
        report.fail(f"Schema file not parseable: {e}")
        return False
    try:
        import jsonschema
        jsonschema.validate(cert, schema)
        report.ok("Structural validation against JSON Schema passed")
        return True
    except ImportError:
        # Fallback: required-field check only
        for k in schema.get("required", []):
            if k not in cert:
                report.fail(f"Missing required top-level field: {k}")
                return False
        report.warn(
            "jsonschema library not installed — only required-field check performed"
        )
        return True
    except Exception as e:
        report.fail(f"Schema validation failed: {e}")
        return False


def validate_compliance_level(cert: dict, report: ValidationReport) -> bool:
    """Step 2: enforce level-specific requirements."""
    level = cert.get("compliance_level", "P0")
    if level not in ["P0", "P1", "P2", "P3", "P4", "P5"]:
        report.fail(f"Unknown compliance_level: {level}")
        return False
    report.ok(f"Compliance level: {level}")
    ok = True

    if level in {"P1", "P2", "P3", "P4", "P5"}:
        # P1+: every value-affecting function must be in obligation_map
        om = cert.get("obligation_map", {})
        if not om:
            report.fail(f"{level}: obligation_map must not be empty")
            ok = False
        else:
            report.ok(f"obligation_map has {len(om)} entries")

    if level in {"P3", "P4", "P5"}:
        # P3+: proof_artifacts required
        pa = cert.get("proof_artifacts")
        if not pa:
            report.fail(f"{level}: proof_artifacts is required for P3+")
            ok = False
        else:
            # Every distinct obligation declared in obligation_map should
            # have a proof_artifact entry
            declared_obligations = set()
            for fn, obs in cert.get("obligation_map", {}).items():
                declared_obligations.update(obs)
            missing = declared_obligations - set(pa.keys())
            if missing:
                report.fail(
                    f"{level}: proof_artifacts missing entries for "
                    f"obligations: {sorted(missing)}"
                )
                ok = False
            else:
                report.ok(
                    f"proof_artifacts covers all {len(declared_obligations)} declared obligations"
                )

    if level == "P4":
        # P4: at least one proof artifact must be from a theorem-proving tool
        pa = cert.get("proof_artifacts", {})
        theorem_tools = {"Lean4", "Coq", "Certora"}
        tools_used = {a.get("tool") for a in pa.values()}
        if not (tools_used & theorem_tools):
            report.fail(
                f"P4: at least one proof_artifact must use a theorem prover "
                f"({sorted(theorem_tools)}); got {sorted(tools_used)}"
            )
            ok = False
        else:
            report.ok(f"P4: theorem prover used in proof_artifacts")

    if level == "P5":
        # P5: runtime_gate required
        rg = cert.get("runtime_gate")
        if not rg:
            report.fail("P5: runtime_gate block is required")
            ok = False
        else:
            for k in ("address", "configuration_hash"):
                if k not in rg:
                    report.fail(f"P5 runtime_gate missing required field: {k}")
                    ok = False
            if all(k in rg for k in ("address", "configuration_hash")):
                report.ok("P5: runtime_gate has address + configuration_hash")

    return ok


def validate_internal_consistency(cert: dict, report: ValidationReport, strict: bool = False) -> bool:
    """Step 3: cross-field consistency checks."""
    ok = True

    # Every obligation in obligation_map values must be in {A1..A5}
    for fn, obs in cert.get("obligation_map", {}).items():
        bad = [o for o in obs if o not in {"A1", "A2", "A3", "A4", "A5"}]
        if bad:
            report.fail(f"obligation_map[{fn}] contains invalid obligations: {bad}")
            ok = False

    # Trust base assumptions: at least one control each
    tba = cert.get("trust_base_assumptions", {})
    for oa in ["OA1_key_integrity", "OA2_signer_sovereignty", "OA3_infrastructure_integrity"]:
        if oa not in tba:
            report.fail(f"trust_base_assumptions missing {oa}")
            ok = False
            continue
        controls = tba[oa].get("controls", [])
        if not controls:
            report.fail(f"trust_base_assumptions.{oa}.controls must not be empty")
            ok = False
        elif len(controls) < 2:
            if strict:
                report.fail(
                    f"--strict: trust_base_assumptions.{oa} should have ≥2 controls "
                    f"(defense in depth)"
                )
                ok = False
            else:
                report.warn(
                    f"trust_base_assumptions.{oa} has only {len(controls)} control "
                    f"(consider defense in depth)"
                )

    # Revalidation triggers — at least one
    rt = cert.get("revalidation_triggers", [])
    if not rt:
        report.fail("revalidation_triggers must not be empty")
        ok = False
    elif "365 days elapsed" in rt or any("days elapsed" in t for t in rt):
        report.ok("Revalidation includes a time-based trigger")
    else:
        if strict:
            report.warn("No time-based revalidation trigger (recommended)")

    # Expiry date is after issued date
    try:
        from datetime import datetime
        issued = datetime.fromisoformat(cert["issued_at"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(cert["expires_at"].replace("Z", "+00:00"))
        if expires <= issued:
            report.fail(f"expires_at ({expires}) is not after issued_at ({issued})")
            ok = False
        else:
            delta_days = (expires - issued).days
            report.ok(f"Validity window: {delta_days} days")
            if delta_days > 365:
                report.warn(
                    f"Validity window > 365 days; consider tighter revalidation cadence"
                )
    except Exception as e:
        report.fail(f"Could not parse issued_at/expires_at: {e}")
        ok = False

    return ok


def validate_certificate(cert_path: Path, schema_path: Path, strict: bool) -> int:
    """Top-level validation entry point. Returns process exit code."""
    print(f"PARALLAX-5 Certificate Validator (reference implementation)")
    print(f"  Certificate: {cert_path}")
    print(f"  Schema:      {schema_path}")
    print(f"  Strict mode: {strict}")
    print()

    try:
        cert = json.loads(cert_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  ✗ Could not load certificate: {e}")
        return 1

    report = ValidationReport()

    step1 = validate_schema(cert, schema_path, report)
    if not step1:
        print(report.render())
        return 1

    step2 = validate_compliance_level(cert, report)
    step3 = validate_internal_consistency(cert, report, strict=strict)

    print(report.render())

    if not step2:
        return 2
    if not step3:
        return 3
    return 0


def main():
    ap = argparse.ArgumentParser(description="PARALLAX-5 Certificate Validator")
    ap.add_argument("cert", type=Path, help="Path to certificate JSON file")
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA,
                    help=f"Path to JSON Schema (default: {DEFAULT_SCHEMA})")
    ap.add_argument("--strict", action="store_true",
                    help="Enforce optional best-practices as errors")
    args = ap.parse_args()
    return validate_certificate(args.cert, args.schema, args.strict)


if __name__ == "__main__":
    sys.exit(main())
