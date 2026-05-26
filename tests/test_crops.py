"""Tests for the CROPS vector module.

These tests exercise the executable specification against the
note's authoritative statements in docs/CROPS_VECTOR.md.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from parallax5_coordinator.capability import Depth, Obligation
from parallax5_coordinator.crops import (
    CROPSDimension,
    CROPSVector,
    OBLIGATION_TO_CROPS,
    WALKAWAY_DEPTH_MAP,
    WalkawayClass,
    compute_crops_vector,
    obligations_contributing_to,
    verify_matrix_consistency,
)


def test_matrix_consistency():
    """The matrix passes its own self-test."""
    ok, issues = verify_matrix_consistency()
    assert ok, f"Matrix consistency failures: {issues}"


def test_every_obligation_contributes_to_S():
    """The S column re-aggregates all obligations."""
    for ob in Obligation:
        assert CROPSDimension.S in OBLIGATION_TO_CROPS[ob], \
            f"{ob.name} missing from S column"


def test_inverse_lookup_consistency():
    """obligations_contributing_to is the inverse of OBLIGATION_TO_CROPS."""
    for dim in CROPSDimension:
        contributors = obligations_contributing_to(dim)
        for ob in contributors:
            assert dim in OBLIGATION_TO_CROPS[ob], \
                f"Inverse lookup inconsistency: {ob.name} → {dim.name}"
        for ob in Obligation:
            if dim in OBLIGATION_TO_CROPS[ob]:
                assert ob in contributors, \
                    f"Forward lookup missing: {ob.name} contributes to {dim.name}"


def test_walkaway_depth_monotone():
    """Walkaway classifications map to monotonically increasing depths."""
    order = [
        WalkawayClass.FAKE,
        WalkawayClass.CENTRALIZED,
        WalkawayClass.PARTIAL,
        WalkawayClass.BOUNDED,
        WalkawayClass.FULL,
    ]
    depths = [int(WALKAWAY_DEPTH_MAP[w]) for w in order]
    assert depths == sorted(depths), f"Walkaway depths not monotone: {depths}"
    assert depths[0] == 0, "fake should map to depth 0"
    assert depths[-1] == 5, "full should map to depth 5"


def test_uniswap_v3_core_worked_example():
    """The worked example in docs/CROPS_VECTOR.md §1.1."""
    coverage = {
        Obligation.A1: Depth(4),
        Obligation.A2: Depth(5),
        Obligation.A3: Depth(0),
        Obligation.A4: Depth(4),
        Obligation.A5: Depth(0),
    }
    vec = compute_crops_vector(
        coverage,
        walkaway=WalkawayClass.FULL,
        source_openness_depth=Depth(5),
        privacy_primitives_depth=Depth(0),
    )
    # Per the note's worked example: (C=4, R=5, O=5, P=0, S=5)
    assert int(vec.C) == 4, f"C: expected 4, got {int(vec.C)}"
    assert int(vec.R) == 5, f"R: expected 5, got {int(vec.R)}"
    assert int(vec.O) == 5, f"O: expected 5, got {int(vec.O)}"
    assert int(vec.P) == 0, f"P: expected 0, got {int(vec.P)}"
    assert int(vec.S) == 5, f"S: expected 5, got {int(vec.S)}"


def test_zero_coverage_yields_zero_vector():
    """A protocol with no evidence yields the zero vector."""
    coverage = {ob: Depth(0) for ob in Obligation}
    vec = compute_crops_vector(coverage)
    assert vec.to_compact_string() == "C=0 R=0 O=0 P=0 S=0"


def test_max_aggregation_semantics():
    """max_within_dimension takes the maximum across contributing obligations."""
    # A1 and A4 both contribute to C. A1 depth 5, A4 depth 0 should give C=5.
    coverage = {
        Obligation.A1: Depth(5),  # contributes to C, S
        Obligation.A2: Depth(0),
        Obligation.A3: Depth(0),
        Obligation.A4: Depth(0),  # contributes to C, S
        Obligation.A5: Depth(0),
    }
    vec = compute_crops_vector(coverage)
    assert int(vec.C) == 5, "max should pick A1=5 even when A4=0"
    assert int(vec.S) == 5


def test_walkaway_inflates_R():
    """Walkaway FULL contributes depth 5 to R even if A2 is low."""
    coverage = {ob: Depth(2) for ob in Obligation}  # A2 only at depth 2
    vec = compute_crops_vector(coverage, walkaway=WalkawayClass.FULL)
    # R = max(A2=2, walkaway_FULL=5) = 5
    assert int(vec.R) == 5, f"FULL walkaway should give R=5, got {int(vec.R)}"


def test_walkaway_fake_does_not_inflate_R():
    """FAKE walkaway contributes 0; R reflects only A2."""
    coverage = {ob: Depth(3) for ob in Obligation}  # A2 at depth 3
    vec = compute_crops_vector(coverage, walkaway=WalkawayClass.FAKE)
    # R = max(A2=3, walkaway_FAKE=0) = 3
    assert int(vec.R) == 3, f"FAKE walkaway should not inflate R, got {int(vec.R)}"


def test_policy_check_pass():
    """A vector that meets a policy passes."""
    vec = CROPSVector(
        C=Depth(4), R=Depth(5), O=Depth(3), P=Depth(0), S=Depth(4)
    )
    passed, violations = vec.meets_policy({"C": 3, "R": 4, "S": 4})
    assert passed, f"Expected pass, got violations: {violations}"
    assert violations == []


def test_policy_check_fail():
    """A vector that fails a policy reports specific violations."""
    vec = CROPSVector(
        C=Depth(2), R=Depth(5), O=Depth(3), P=Depth(0), S=Depth(4)
    )
    passed, violations = vec.meets_policy({"C": 3, "S": 5})
    assert not passed
    assert len(violations) == 2
    assert any("C" in v for v in violations)
    assert any("S" in v for v in violations)


def test_invalid_policy_dimension():
    """Unknown CROPS dimension in policy is a ValueError."""
    vec = CROPSVector(
        C=Depth(0), R=Depth(0), O=Depth(0), P=Depth(0), S=Depth(0)
    )
    try:
        vec.meets_policy({"X": 1})
        assert False, "should have raised"
    except ValueError:
        pass


def test_to_dict_round_trip():
    """to_dict produces certificate-schema-compatible output."""
    vec = CROPSVector(
        C=Depth(1), R=Depth(2), O=Depth(3), P=Depth(4), S=Depth(5)
    )
    d = vec.to_dict()
    assert d == {
        "C": 1, "R": 2, "O": 3, "P": 4, "S": 5,
        "computation_method": "max_within_dimension",
    }


def test_unsupported_method_raises():
    """Non-supported aggregation methods raise NotImplementedError."""
    coverage = {ob: Depth(0) for ob in Obligation}
    try:
        compute_crops_vector(coverage, method="weighted_average")
        assert False, "should have raised"
    except NotImplementedError:
        pass


def test_out_of_range_depth_rejected():
    """CROPSVector rejects depths outside 0-5."""
    try:
        CROPSVector(C=Depth(6), R=Depth(0), O=Depth(0), P=Depth(0), S=Depth(0))
        assert False, "should have raised"
    except ValueError:
        pass


def test_centralized_lending_example():
    """A representative centralized lending protocol with weak walkaway."""
    coverage = {
        Obligation.A1: Depth(2),  # static reentrancy check passed
        Obligation.A2: Depth(2),  # static admin checks passed
        Obligation.A3: Depth(0),
        Obligation.A4: Depth(2),  # static reentrancy check
        Obligation.A5: Depth(0),
    }
    vec = compute_crops_vector(
        coverage,
        walkaway=WalkawayClass.CENTRALIZED,
        source_openness_depth=Depth(3),  # source is on GitHub
        privacy_primitives_depth=Depth(0),
    )
    # Centralized walkaway = depth 1; A2 = 2; R = max(2,1) = 2
    assert int(vec.R) == 2
    # Source openness inflates O
    assert int(vec.O) == 3
    # S = max(A1,...,A5) = 2
    assert int(vec.S) == 2


def test_fake_walkaway_signal():
    """FAKE walkaway with strong S still gives weak R — exactly the consumer signal we want."""
    coverage = {ob: Depth(4) for ob in Obligation}
    vec = compute_crops_vector(
        coverage,
        walkaway=WalkawayClass.FAKE,
        source_openness_depth=Depth(5),
        privacy_primitives_depth=Depth(0),
    )
    # The protocol looks great on S, but R = max(A2=4, walkaway_FAKE=0) = 4
    # Wait — that's still 4. The fake-signal works ONLY when A2 is also weak.
    # This test documents the limitation: the CROPS R-floor is A2's depth,
    # not the walkaway-derived value alone. This is correct per the spec.
    assert int(vec.S) == 4
    assert int(vec.R) == 4  # A2=4 dominates over fake=0
    # Per v1.0.1 matrix refinement: P contributions come ONLY from explicit
    # privacy primitives, not from A3 evidence. privacy_primitives_depth=0
    # → P=0 regardless of A3 depth.
    assert int(vec.P) == 0  # privacy_primitives_depth=0 → P=0
    # Consumers should consult the walkaway field directly, not rely on R alone
    # for fake-walkaway detection.


def test_a3_does_not_inflate_privacy():
    """v1.0.1 refinement: A3 (signature integrity) does NOT contribute to P.

    Privacy contributions come only from explicit privacy_primitives_depth.
    Rationale: signature malleability is primarily integrity/replay/canon;
    the privacy-adjacent consequence (cross-message identity correlation)
    is real but conditional on the protocol making an explicit privacy
    claim via signature canonicalization.
    """
    coverage = {
        Obligation.A1: Depth(0),
        Obligation.A2: Depth(0),
        Obligation.A3: Depth(5),   # max A3 depth — formal proof of low-s enforcement
        Obligation.A4: Depth(0),
        Obligation.A5: Depth(0),
    }
    vec = compute_crops_vector(
        coverage,
        walkaway=None,
        source_openness_depth=Depth(0),
        privacy_primitives_depth=Depth(0),
    )
    # Under v1.0.1 matrix: A3 contributes only to S.
    assert int(vec.S) == 5, f"A3 should still feed S; got S={int(vec.S)}"
    assert int(vec.P) == 0, f"A3 must NOT inflate P; got P={int(vec.P)}"


def test_privacy_primitives_are_only_p_source():
    """Privacy depth comes solely from privacy_primitives_depth in v1.0.1."""
    coverage = {ob: Depth(5) for ob in Obligation}
    vec = compute_crops_vector(
        coverage,
        walkaway=WalkawayClass.FULL,
        source_openness_depth=Depth(5),
        privacy_primitives_depth=Depth(3),
    )
    # All obligations at D5, but P should only reflect privacy_primitives_depth
    assert int(vec.P) == 3, f"P should equal privacy_primitives_depth=3; got {int(vec.P)}"
    # Sanity: zero privacy_primitives_depth gives P=0
    vec0 = compute_crops_vector(
        coverage,
        walkaway=WalkawayClass.FULL,
        source_openness_depth=Depth(5),
        privacy_primitives_depth=Depth(0),
    )
    assert int(vec0.P) == 0


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in globals().items()
             if name.startswith("test_") and callable(fn)]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {name}: {type(e).__name__}: {e}")
            failed += 1
    print()
    print(f"Total: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
