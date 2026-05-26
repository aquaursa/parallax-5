"""
Capability model for the PARALLAX-5 Coordinator.

A *capability* is what a tool can in principle establish about an
obligation, graded on a six-level evidence-depth scale:

  0  No coverage. Tool produces nothing relevant.
  1  Mention. Tool can report a code-level location that humans
     interpret. (Comment-grade evidence; not machine-checkable.)
  2  Static detector. Tool flags the issue via a pattern matcher.
     Sound up to detector calibration; false positives possible.
  3  Symbolic path. Tool produces a path-condition witness for
     the issue. Stronger than (2); restricted by exploration bounds.
  4  Formal property. Tool verifies a user-specified invariant by
     symbolic / bounded model checking. Requires invariant
     specification.
  5  Machine-checked theorem. The property is a theorem in an
     interactive proof assistant accepted by the kernel.

Depth is monotone: higher depth subsumes lower. A tool reporting at
depth 3 simultaneously establishes the (weaker) depth-1 and depth-2
claims.

The capability of a single tool is a function
    c_t : Obligation -> Depth
The joint capability of a set of tools is the pointwise max.

The five obligations are inherited from PARALLAX-5:
    A1  Value conservation
    A2  Authorization closure
    A3  Signature integrity
    A4  Temporal distinctness
    A5  External-attestation trust
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Iterable, Mapping, Tuple


class Depth(IntEnum):
    """Evidence depth, monotone ladder. Higher subsumes lower."""
    NONE              = 0   # No relevant capability
    MENTION           = 1   # Code-location report, comment-grade
    STATIC_DETECTOR   = 2   # Pattern match flagged
    SYMBOLIC_PATH     = 3   # Path-condition witness
    FORMAL_PROPERTY   = 4   # Invariant verified by checker
    MACHINE_THEOREM   = 5   # Kernel-accepted theorem


class Obligation(IntEnum):
    """The five PARALLAX-5 obligations."""
    A1 = 1   # Value conservation
    A2 = 2   # Authorization closure
    A3 = 3   # Signature integrity
    A4 = 4   # Temporal distinctness
    A5 = 5   # External-attestation trust


@dataclass(frozen=True)
class ToolCapability:
    """Capability of a single tool, expressed as a function from
    obligation to maximum achievable depth on that obligation."""
    tool_id: str
    version: str
    depth_by_obligation: Mapping[Obligation, Depth]
    notes: str = ""

    def depth(self, ob: Obligation) -> Depth:
        return self.depth_by_obligation.get(ob, Depth.NONE)

    def covered(self, ob: Obligation, min_depth: Depth) -> bool:
        return self.depth(ob) >= min_depth


@dataclass(frozen=True)
class JointCapability:
    """Pointwise max of a set of tool capabilities.

    Implements the Compositional Coverage Theorem operationally:
    the joint depth on any obligation equals the maximum depth
    achieved by any tool in the set.
    """
    tools: Tuple[ToolCapability, ...]

    def depth(self, ob: Obligation) -> Depth:
        if not self.tools:
            return Depth.NONE
        return Depth(max(t.depth(ob) for t in self.tools))

    def covered(self, ob: Obligation, min_depth: Depth) -> bool:
        return self.depth(ob) >= min_depth

    def coverage_vector(self) -> Dict[Obligation, Depth]:
        return {ob: self.depth(ob) for ob in Obligation}

    def evidence_sources(self, ob: Obligation) -> Tuple[str, ...]:
        """Return the tool ids that contribute to coverage at the
        current joint depth for the given obligation."""
        d = self.depth(ob)
        if d == Depth.NONE:
            return ()
        return tuple(t.tool_id for t in self.tools if t.depth(ob) == d)


# ─── P-level → required-depth table (PARALLAX-5 standard) ────────────
# This is the canonical mapping from compliance levels to the depth
# required on each obligation. P_0 is no requirement; P_5 requires
# machine-checked theorems for all five obligations.
P_LEVEL_REQUIREMENTS: Dict[int, Depth] = {
    0: Depth.NONE,
    1: Depth.MENTION,
    2: Depth.STATIC_DETECTOR,
    3: Depth.SYMBOLIC_PATH,
    4: Depth.FORMAL_PROPERTY,
    5: Depth.MACHINE_THEOREM,
}


def p_level(capability: JointCapability) -> int:
    """Maximum P-level satisfied by the joint capability.

    Implements the Certificate Monotonicity Theorem operationally:
    adding a tool to the set never lowers the P-level, because the
    joint depth is monotone under tool addition (pointwise max).
    """
    for level in range(5, -1, -1):
        required = P_LEVEL_REQUIREMENTS[level]
        if all(capability.depth(ob) >= required for ob in Obligation):
            return level
    return 0


def coverage_gaps(capability: JointCapability, target_level: int) -> Dict[Obligation, Depth]:
    """Obligations whose coverage falls below the requirement for the
    target P-level, with the deficit reported as the missing depth."""
    required = P_LEVEL_REQUIREMENTS[target_level]
    return {
        ob: Depth(required - capability.depth(ob))
        for ob in Obligation
        if capability.depth(ob) < required
    }


# ─── Capability matrix: documented per-tool capabilities ─────────────
# These values are derived from each tool's documentation and
# detector lists. Each entry is justified in the companion
# TOOL-MAPPING v1.0 document.

SLITHER_CAPABILITY = ToolCapability(
    tool_id="slither",
    version="0.10.x",
    depth_by_obligation={
        Obligation.A1: Depth.STATIC_DETECTOR,    # `arbitrary-send-eth`, `arbitrary-send-erc20`, `unused-return`
        Obligation.A2: Depth.STATIC_DETECTOR,    # `unprotected-upgrade`, `suicidal`, `unprotected-initialize`, `tx-origin`
        Obligation.A3: Depth.NONE,               # No primitive for signature verification adequacy
        Obligation.A4: Depth.STATIC_DETECTOR,    # `reentrancy-*` (eth, erc20, no-eth, events, unlimited-gas)
        Obligation.A5: Depth.NONE,               # No oracle staleness detector
    },
    notes=(
        "Slither's strength is syntactic-pattern detectors against documented "
        "vulnerability classes. Strong on A2 (multiple admin-protection detectors) "
        "and A4 (the reentrancy detector family). Weaker on A1 (arbitrary-send "
        "covers some but not all conservation violations). Does not reason about "
        "signatures (A3) or oracles (A5)."
    ),
)

MYTHRIL_CAPABILITY = ToolCapability(
    tool_id="mythril",
    version="0.24.x",
    depth_by_obligation={
        Obligation.A1: Depth.SYMBOLIC_PATH,      # SWC-105 unprotected ether withdrawal, path-conditional
        Obligation.A2: Depth.SYMBOLIC_PATH,      # SWC-105, SWC-106 self-destruct, path-conditional
        Obligation.A3: Depth.STATIC_DETECTOR,    # SWC-117 signature malleability (limited)
        Obligation.A4: Depth.SYMBOLIC_PATH,      # SWC-107 reentrancy via symbolic execution
        Obligation.A5: Depth.NONE,               # No oracle reasoning
    },
    notes=(
        "Mythril uses symbolic execution to produce path-condition witnesses, "
        "giving it depth-3 evidence where Slither has only depth-2 patterns. "
        "Some SWC categories (notably SWC-117 signature malleability) are "
        "detector-only. Path-exploration bounds limit completeness."
    ),
)

HALMOS_CAPABILITY = ToolCapability(
    tool_id="halmos",
    version="0.2.x",
    depth_by_obligation={
        Obligation.A1: Depth.FORMAL_PROPERTY,    # User-specified invariant via foundry-style property tests
        Obligation.A2: Depth.FORMAL_PROPERTY,    # User-specified
        Obligation.A3: Depth.FORMAL_PROPERTY,    # User-specified (ECDSA model imported)
        Obligation.A4: Depth.FORMAL_PROPERTY,    # User-specified
        Obligation.A5: Depth.FORMAL_PROPERTY,    # User-specified (oracle as symbolic input)
    },
    notes=(
        "Halmos achieves depth-4 (formal property) on any obligation FOR WHICH "
        "the user supplies a property. Coverage is therefore conditional on "
        "specification effort. Universally capable in principle; bottleneck is "
        "the human writing properties."
    ),
)

AXIOMSOL_CAPABILITY = ToolCapability(
    tool_id="obligationsol",
    version="parallax5-v6",
    depth_by_obligation={
        Obligation.A1: Depth.STATIC_DETECTOR,    # obligation-signature matching on conservation patterns
        Obligation.A2: Depth.STATIC_DETECTOR,    # Authorization-closure signature detection
        Obligation.A3: Depth.NONE,               # Delegated to ECDSA EUF-CMA, external to ObligationSol
        Obligation.A4: Depth.STATIC_DETECTOR,    # Reentrancy and call-depth tracking
        Obligation.A5: Depth.STATIC_DETECTOR,    # Oracle staleness, freshness windows
    },
    notes=(
        "ObligationSol provides obligation-signature matching across all four "
        "EVM-side obligations (A1, A2, A4, A5) at static-detector depth. "
        "A3 is delegated to the external ECDSA assumption and not "
        "addressed by ObligationSol directly. Distinguishing feature: A5 oracle "
        "obligations are detectable, which no other tool in the stack "
        "addresses natively."
    ),
)


KNOWN_TOOLS: Dict[str, ToolCapability] = {
    "slither":  SLITHER_CAPABILITY,
    "mythril":  MYTHRIL_CAPABILITY,
    "halmos":   HALMOS_CAPABILITY,
    "obligationsol": AXIOMSOL_CAPABILITY,
}


def capability_matrix_table() -> str:
    """Render the capability matrix as a human-readable table."""
    obs = list(Obligation)
    header = f"{'Tool':<12} | " + " | ".join(f"{ob.name}" for ob in obs)
    sep = "-" * len(header)
    rows = [header, sep]
    for tid, t in KNOWN_TOOLS.items():
        cells = [f"{t.depth(ob):d}" for ob in obs]
        rows.append(f"{tid:<12} | " + " | ".join(f"{c:<2}" for c in cells))
    rows.append(sep)
    joint = JointCapability(tuple(KNOWN_TOOLS.values()))
    cells = [f"{joint.depth(ob):d}" for ob in obs]
    rows.append(f"{'(joint)':<12} | " + " | ".join(f"{c:<2}" for c in cells))
    rows.append("")
    rows.append("Depth levels:")
    rows.append("  0 = no coverage")
    rows.append("  1 = mention (comment-grade)")
    rows.append("  2 = static detector")
    rows.append("  3 = symbolic-path witness")
    rows.append("  4 = formal property checker (user-spec)")
    rows.append("  5 = machine-checked theorem")
    return "\n".join(rows)
