"""parallax.obligations.fire_tests — A1-A5 vocabulary fire tests.

Run with: python -m parallax.obligations.fire_tests
Each fire test is a sanity check that the obligation vocabulary's
contracts hold.
"""
from __future__ import annotations

import sys
import time

from . import (
    ALL_OBLIGATIONS, ObligationId,
)


def test_five_atomic_obligations_present():
    """The PARALLAX-5 substrate consists of exactly five primitive obligations."""
    assert len(ALL_OBLIGATIONS) == 5, f"expected 5 obligations, got {len(ALL_OBLIGATIONS)}"
    ids = {a.id for a in ALL_OBLIGATIONS}
    expected = {
        ObligationId.SHARE_ASSET_CONSERVATION,
        ObligationId.AUTHORIZATION_CLOSURE,
        ObligationId.SIGNATURE_INTEGRITY,
        ObligationId.TEMPORAL_DISTINCTNESS,
        ObligationId.ORACLE_TRUST_BOUNDARY,
    }
    assert ids == expected, f"obligation set mismatch: {ids ^ expected}"


def test_obligation_ids_are_named_consistently():
    """Each obligation has a stable id, label, and predicate description."""
    for ob in ALL_OBLIGATIONS:
        assert ob.id is not None
        assert ob.name and len(ob.name) > 3
        assert ob.formal_statement and len(ob.formal_statement) > 5
        assert ob.violation_predicate and len(ob.violation_predicate) > 5


def test_obligation_lookup_is_total():
    """Every ObligationId resolves to exactly one Obligation."""
    from . import OBLIGATION_BY_ID, obligation_lookup
    for oid in ObligationId:
        assert oid in OBLIGATION_BY_ID
        assert obligation_lookup(oid).id == oid


ALL_TESTS = [
    test_five_atomic_obligations_present,
    test_obligation_ids_are_named_consistently,
    test_obligation_lookup_is_total,
]


def main() -> int:
    t0 = time.perf_counter()
    failures: list[tuple[str, str]] = []
    for t in ALL_TESTS:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except AssertionError as e:
            print(f"  ✗ {t.__name__}: {e}")
            failures.append((t.__name__, str(e)))
    elapsed = time.perf_counter() - t0
    print(f"\ntotal: {elapsed:.2f}s  ({len(ALL_TESTS) - len(failures)}/{len(ALL_TESTS)} passed)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
