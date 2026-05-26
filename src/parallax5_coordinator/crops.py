"""
CROPS Vector — multi-dimensional trust-surface rating for PARALLAX-5.

This module implements the CROPS extension specified in docs/CROPS_VECTOR.md:
extending the security-only P-level into a five-dimensional vector
(Censorship-resistance, capture-Resistance, Openness, Privacy, Security).

The implementation is the executable specification of the contribution
matrix (Section 2 of the note). Any divergence between this code and
the note is a bug in this code; the note is authoritative.

License: Apache-2.0
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from .capability import Depth, Obligation


class CROPSDimension(Enum):
    """The five CROPS dimensions, in canonical order."""
    C = "censorship_resistance"
    R = "capture_resistance"
    O = "openness"
    P = "privacy"
    S = "security"

    @property
    def short_name(self) -> str:
        return self.name

    @property
    def long_name(self) -> str:
        return self.value.replace("_", " ").title()


class WalkawayClass(Enum):
    """The five walkaway classifications from the Walkaway Theorem."""
    FULL = "full"
    BOUNDED = "bounded"
    PARTIAL = "partial"
    CENTRALIZED = "centralized"
    FAKE = "fake"


# Walkaway class → depth contribution to the R dimension
# (per docs/WALKAWAY_THEOREM.md §10)
WALKAWAY_DEPTH_MAP: Dict[WalkawayClass, Depth] = {
    WalkawayClass.FULL: Depth(5),
    WalkawayClass.BOUNDED: Depth(4),
    WalkawayClass.PARTIAL: Depth(3),
    WalkawayClass.CENTRALIZED: Depth(1),
    WalkawayClass.FAKE: Depth(0),
}


# The CROPS Contribution Matrix
# Executable form of docs/CROPS_VECTOR.md §2.
# Each obligation maps to the set of CROPS dimensions it contributes to.
#
# Note (v1.0.1 refinement): A3 was previously mapped to {P, S}. This was
# revised to {S} after external review observed that signature malleability
# is primarily a signature-integrity/replay/canonicalization issue, not a
# privacy issue: the privacy-adjacent consequence (cross-message identity
# correlation by an attacker) is real but conditional on the protocol making
# an explicit privacy claim via signature canonicalization. Honest reporting
# of P requires that privacy contributions come from explicit privacy
# primitives declared in the spec, not from incidental properties of A3
# evidence. The matrix below reflects this clarification.
OBLIGATION_TO_CROPS: Dict[Obligation, Set[CROPSDimension]] = {
    Obligation.A1: {CROPSDimension.C, CROPSDimension.S},
    Obligation.A2: {CROPSDimension.R, CROPSDimension.S},
    Obligation.A3: {CROPSDimension.S},
    Obligation.A4: {CROPSDimension.C, CROPSDimension.S},
    Obligation.A5: {CROPSDimension.C, CROPSDimension.O, CROPSDimension.S},
}


def obligations_contributing_to(dim: CROPSDimension) -> Set[Obligation]:
    """Return the set of obligations that contribute to dimension `dim`."""
    return {ob for ob, dims in OBLIGATION_TO_CROPS.items() if dim in dims}


@dataclass(frozen=True)
class CROPSVector:
    """A five-component CROPS rating. Each component is on the D0–D5 depth scale."""
    C: Depth
    R: Depth
    O: Depth
    P: Depth
    S: Depth
    computation_method: str = "max_within_dimension"

    def __post_init__(self):
        for name in ("C", "R", "O", "P", "S"):
            val = getattr(self, name)
            if not isinstance(val, Depth):
                raise TypeError(f"CROPS component {name} must be a Depth, got {type(val).__name__}")
            if int(val) < 0 or int(val) > 5:
                raise ValueError(f"CROPS component {name} must be in 0..5, got {int(val)}")

    def to_dict(self) -> dict:
        return {
            "C": int(self.C),
            "R": int(self.R),
            "O": int(self.O),
            "P": int(self.P),
            "S": int(self.S),
            "computation_method": self.computation_method,
        }

    def to_compact_string(self) -> str:
        return f"C={int(self.C)} R={int(self.R)} O={int(self.O)} P={int(self.P)} S={int(self.S)}"

    def meets_policy(self, minimums: Dict[str, int]) -> Tuple[bool, List[str]]:
        violations = []
        for dim_name, minimum in minimums.items():
            if dim_name not in ("C", "R", "O", "P", "S"):
                raise ValueError(f"Unknown CROPS dimension: {dim_name}")
            actual = int(getattr(self, dim_name))
            if actual < minimum:
                violations.append(f"{dim_name}: required >= {minimum}, got {actual}")
        return (len(violations) == 0, violations)


def compute_crops_vector(
    obligation_depths: Dict[Obligation, Depth],
    walkaway: Optional[WalkawayClass] = None,
    source_openness_depth: Depth = Depth(0),
    privacy_primitives_depth: Depth = Depth(0),
    method: str = "max_within_dimension",
) -> CROPSVector:
    """Compute a CROPS vector per docs/CROPS_VECTOR.md §3."""
    if method != "max_within_dimension":
        raise NotImplementedError(f"Only 'max_within_dimension' is supported; got '{method}'")

    def max_for(dim: CROPSDimension, extras: List[Depth] = ()) -> Depth:
        candidates = [int(obligation_depths.get(ob, Depth(0))) for ob in obligations_contributing_to(dim)]
        candidates.extend(int(d) for d in extras)
        return Depth(max(candidates) if candidates else 0)

    extras_R: List[Depth] = []
    if walkaway is not None:
        extras_R.append(WALKAWAY_DEPTH_MAP[walkaway])

    return CROPSVector(
        C=max_for(CROPSDimension.C),
        R=max_for(CROPSDimension.R, extras_R),
        O=max_for(CROPSDimension.O, [source_openness_depth]),
        P=max_for(CROPSDimension.P, [privacy_primitives_depth]),
        S=max_for(CROPSDimension.S),
        computation_method=method,
    )


def matrix_table() -> str:
    """Pretty-print the contribution matrix as a Markdown table."""
    lines = [
        "| Obligation                          |  C  |  R  |  O  |  P  |  S  |",
        "|-------------------------------------|:---:|:---:|:---:|:---:|:---:|",
    ]
    descriptions = {
        Obligation.A1: "Value conservation",
        Obligation.A2: "Authorization closure",
        Obligation.A3: "Signature integrity",
        Obligation.A4: "Temporal distinctness",
        Obligation.A5: "External-attestation trust",
    }
    for ob in [Obligation.A1, Obligation.A2, Obligation.A3, Obligation.A4, Obligation.A5]:
        contributes = OBLIGATION_TO_CROPS[ob]
        label = f"**{ob.name}** {descriptions[ob]}"
        cells = []
        for dim in [CROPSDimension.C, CROPSDimension.R, CROPSDimension.O,
                    CROPSDimension.P, CROPSDimension.S]:
            cells.append(" ✓ " if dim in contributes else " — ")
        lines.append(f"| {label:<35s} |{'|'.join(cells)}|")
    lines.append("| (derived) Walkaway                  | — | ✓ | — | — | — |")
    lines.append("| (derived) Source openness           | — | — | ✓ | — | — |")
    lines.append("| (derived) Privacy primitives        | — | — | — | ✓ | — |")
    lines.append("|                                     |   |   |   |   |   |")
    lines.append("| Note: P contributions come ONLY from explicit privacy primitives.   |")
    lines.append("| Signature integrity (A3) does not contribute to P unless the        |")
    lines.append("| protocol makes an explicit privacy claim via signature              |")
    lines.append("| canonicalization (e.g., ring signatures, blinded signatures).       |")
    return "\n".join(lines)


def verify_matrix_consistency() -> Tuple[bool, List[str]]:
    """Self-test for the contribution matrix and walkaway depth map."""
    issues = []
    # Every obligation contributes to S
    for ob in Obligation:
        if CROPSDimension.S not in OBLIGATION_TO_CROPS.get(ob, set()):
            issues.append(f"Obligation {ob.name} does not contribute to S column")
    # Spot-check matrix matches the note
    expected = {
        Obligation.A1: {CROPSDimension.C, CROPSDimension.S},
        Obligation.A2: {CROPSDimension.R, CROPSDimension.S},
        Obligation.A3: {CROPSDimension.S},
        Obligation.A4: {CROPSDimension.C, CROPSDimension.S},
        Obligation.A5: {CROPSDimension.C, CROPSDimension.O, CROPSDimension.S},
    }
    for ob, expected_dims in expected.items():
        if OBLIGATION_TO_CROPS.get(ob, set()) != expected_dims:
            issues.append(f"Obligation {ob.name}: expected {expected_dims}, got {OBLIGATION_TO_CROPS.get(ob)}")
    # Walkaway depth map monotonicity
    order = [WalkawayClass.FAKE, WalkawayClass.CENTRALIZED, WalkawayClass.PARTIAL,
             WalkawayClass.BOUNDED, WalkawayClass.FULL]
    prev_depth = -1
    for wc in order:
        d = int(WALKAWAY_DEPTH_MAP[wc])
        if d < prev_depth:
            issues.append(f"WALKAWAY_DEPTH_MAP non-monotone at {wc.value}")
        prev_depth = d
    return (len(issues) == 0, issues)


if __name__ == "__main__":
    print("PARALLAX-5 CROPS Vector — contribution matrix")
    print()
    print(matrix_table())
    print()
    ok, issues = verify_matrix_consistency()
    print(f"Matrix consistency self-test: {'PASS' if ok else 'FAIL'}")
    if not ok:
        for issue in issues:
            print(f"  - {issue}")
        import sys
        sys.exit(1)
    print()
    print("─── Worked example: Uniswap V3 Core ───")
    print()
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
    print(f"  Coverage: {{A1: 4, A2: 5, A3: 0, A4: 4, A5: 0}}")
    print(f"  Walkaway: FULL  Source openness: 5  Privacy primitives: 0")
    print(f"  Result:   {vec.to_compact_string()}")
    print()
    policy = {"C": 3, "R": 4, "O": 3, "S": 4}
    passed, violations = vec.meets_policy(policy)
    print(f"  Policy check (C>=3 R>=4 O>=3 S>=4): {'PASS' if passed else 'FAIL'}")
    for v in violations:
        print(f"    - {v}")
