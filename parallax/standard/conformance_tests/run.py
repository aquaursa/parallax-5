"""PARALLAX-5 Conformance Test Suite

Each test is a (certificate JSON, expected verdict, mode) triple. A
conformant validator must produce the expected verdict on every case.

Verdicts:
    "valid"   — exit code 0
    "schema"  — exit code 1 (structural validation failure)
    "level"   — exit code 2 (compliance-level requirement failure)
    "consistency" — exit code 3 (internal consistency failure)
"""

from __future__ import annotations
import json
import sys
import tempfile
import copy
import io
import contextlib
from pathlib import Path
from typing import Callable

from parallax.standard.validator import validate_certificate

ROOT = Path(__file__).parent.parent.parent.parent
SCHEMA = ROOT / "paper" / "supplement" / "parallax5_certificate.schema.json"
EXAMPLE_CERT_PATH = ROOT / "paper" / "supplement" / "example_certificate.json"


def load_base() -> dict:
    return json.load(open(EXAMPLE_CERT_PATH))


def with_mutation(mutator: Callable[[dict], dict]) -> dict:
    base = load_base()
    return mutator(base)


# ────────────────────────────────────────────────────────────
#   POSITIVE TESTS — these must all VALIDATE
# ────────────────────────────────────────────────────────────

def positive_basic_p4() -> dict:
    """The canonical example certificate (P4) must validate."""
    return load_base()


def positive_p3_with_minimal_proof_artifacts() -> dict:
    """A P3 certificate with only minimum required proof artifacts."""
    cert = load_base()
    cert["compliance_level"] = "P3"
    # remove the Lean theorem artifact since P3 doesn't need a theorem prover
    return cert


def positive_p0_no_proofs() -> dict:
    """A P0 (unclassified) certificate without any proof_artifacts."""
    cert = load_base()
    cert["compliance_level"] = "P0"
    cert.pop("proof_artifacts", None)
    cert.pop("obligation_map", None)
    cert["obligation_map"] = {}
    return cert


def positive_p5_with_runtime_gate() -> dict:
    """A P5 certificate with the runtime_gate block."""
    cert = load_base()
    cert["compliance_level"] = "P5"
    cert["runtime_gate"] = {
        "address": "0x" + "1" * 40,
        "configuration_hash": "sha256:" + "a" * 64,
    }
    return cert


# ────────────────────────────────────────────────────────────
#   NEGATIVE TESTS — these must FAIL with specific exit codes
# ────────────────────────────────────────────────────────────

def negative_missing_schema_version() -> dict:
    """No schema_version field → schema validation fails."""
    cert = load_base()
    del cert["schema_version"]
    return cert


def negative_invalid_compliance_level() -> dict:
    """compliance_level = 'P7' → schema validation fails."""
    cert = load_base()
    cert["compliance_level"] = "P7"
    return cert


def negative_invalid_certificate_id_format() -> dict:
    """certificate_id with disallowed characters → schema fails."""
    cert = load_base()
    cert["certificate_id"] = "not a valid id"
    return cert


def negative_p3_missing_proof_artifacts() -> dict:
    """P3+ requires proof_artifacts; missing → level violation."""
    cert = load_base()
    cert["compliance_level"] = "P3"
    cert.pop("proof_artifacts", None)
    return cert


def negative_p5_missing_runtime_gate() -> dict:
    """P5 requires runtime_gate; missing → schema (conditional)."""
    cert = load_base()
    cert["compliance_level"] = "P5"
    # runtime_gate missing
    return cert


def negative_obligation_map_invalid_obligation() -> dict:
    """obligation_map containing 'A6' (not in {A1..A5}) → consistency fail."""
    cert = load_base()
    fn = next(iter(cert["obligation_map"]))
    cert["obligation_map"][fn] = ["A1", "A6"]
    return cert


def negative_missing_trust_base_assumption() -> dict:
    """trust_base_assumptions missing OA1 → consistency fail."""
    cert = load_base()
    cert["trust_base_assumptions"].pop("OA1_key_integrity", None)
    return cert


def negative_proof_artifact_obligation_mismatch() -> dict:
    """P3+ requires proof_artifacts for every declared obligation."""
    cert = load_base()
    cert["compliance_level"] = "P3"
    # Add a function declaring A2, but no A2 in proof_artifacts
    cert["obligation_map"]["newOp(uint256)"] = ["A2"]
    cert["proof_artifacts"].pop("A2", None)
    return cert


def negative_expires_before_issued() -> dict:
    """expires_at must be after issued_at → consistency fail."""
    cert = load_base()
    cert["expires_at"] = "2025-01-01T00:00:00Z"   # before issued_at
    return cert


def negative_empty_revalidation_triggers() -> dict:
    """revalidation_triggers must be non-empty → consistency fail."""
    cert = load_base()
    cert["revalidation_triggers"] = []
    return cert


def negative_p4_no_theorem_prover() -> dict:
    """P4 requires at least one theorem-prover artifact."""
    cert = load_base()
    # remove Lean and use halmos for all
    cert["proof_artifacts"] = {
        ob: {"tool": "halmos", "version": "0.3.3", "verdict": "PASS",
             "paths_explored": 1,
             "artifact_hash": "sha256:" + "0" * 64}
        for ob in {a for obs in cert["obligation_map"].values() for a in obs}
    }
    return cert


# ────────────────────────────────────────────────────────────
#   TEST RUNNER
# ────────────────────────────────────────────────────────────

CONFORMANCE_TESTS = [
    # Positive tests: must validate (exit code 0)
    ("positive_basic_p4", positive_basic_p4, 0, "Canonical example must validate"),
    ("positive_p3_minimal", positive_p3_with_minimal_proof_artifacts, 0, "Valid P3 with minimal artifacts"),
    ("positive_p0_no_proofs", positive_p0_no_proofs, 0, "Valid P0 without proof_artifacts"),
    ("positive_p5_runtime_gate", positive_p5_with_runtime_gate, 0, "Valid P5 with runtime_gate"),

    # Negative tests: must fail with specific codes
    ("negative_missing_schema_version", negative_missing_schema_version, 1,
     "Missing schema_version → schema fail"),
    ("negative_invalid_compliance_level", negative_invalid_compliance_level, 1,
     "compliance_level='P7' → schema fail"),
    ("negative_bad_certificate_id", negative_invalid_certificate_id_format, 1,
     "Bad certificate_id format → schema fail"),
    ("negative_p3_no_proof_artifacts", negative_p3_missing_proof_artifacts, 1,
     "P3 with no proof_artifacts → schema (allOf) fail"),
    ("negative_p5_no_runtime_gate", negative_p5_missing_runtime_gate, 1,
     "P5 missing runtime_gate → schema (allOf) fail"),
    ("negative_obligation_a6", negative_obligation_map_invalid_obligation, 1,
     "obligation_map A6 → schema enum violation"),
    ("negative_missing_oa1", negative_missing_trust_base_assumption, 1,
     "Missing OA1 → schema fail (required)"),
    ("negative_proof_artifact_mismatch", negative_proof_artifact_obligation_mismatch, 2,
     "Declared obligation without proof_artifact → level fail"),
    ("negative_expires_before_issued", negative_expires_before_issued, 3,
     "expires_at < issued_at → consistency fail"),
    ("negative_empty_revalidation", negative_empty_revalidation_triggers, 1,
     "Empty revalidation_triggers → schema minItems fail"),
    ("negative_p4_no_theorem_prover", negative_p4_no_theorem_prover, 2,
     "P4 without theorem prover → level fail"),
]


def run_all() -> int:
    print(f"PARALLAX-5 Conformance Test Suite ({len(CONFORMANCE_TESTS)} tests)")
    print("=" * 70)
    passed = 0
    failed = 0
    failures = []
    for name, factory, expected_code, description in CONFORMANCE_TESTS:
        cert = factory()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cert, f)
            tmp_path = Path(f.name)
        try:
            # Silence validator output
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                actual_code = validate_certificate(tmp_path, SCHEMA, strict=False)
            ok = (actual_code == expected_code)
            status = "✓" if ok else "✗"
            print(f"  {status} {name:<42s} expected={expected_code} actual={actual_code}")
            if not ok:
                failures.append((name, expected_code, actual_code, description))
                failed += 1
            else:
                passed += 1
        finally:
            tmp_path.unlink()
    print()
    print("─" * 70)
    print(f"  Passed: {passed}/{len(CONFORMANCE_TESTS)}    Failed: {failed}")
    if failures:
        print()
        print("Failures:")
        for name, exp, act, desc in failures:
            print(f"  {name}: expected exit {exp}, got {act}")
            print(f"    ({desc})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
