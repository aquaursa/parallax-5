"""parallax.obligations.obligations — the five atomic axioms.

The AXIOM thesis: every vulnerability class in a deterministic state
machine under adversarial input is the violation of some combination
of a small set of structural axioms. These five are the candidates.

Each axiom is:
* Named (canonical identifier for citations)
* Stated formally enough to be checked against a target
* Accompanied by the violation predicate that makes it actionable

The closure of these five under combination (A1 × A2, A1 × A4, etc.)
enumerates the lattice of vulnerability classes. About 600 classes
have ever been empirically observed; the lattice contains ~3400. The
unobserved classes are predictions that PARALLAX detects prospectively.

This module is the load-bearing piece of OMEGA. If the AXIOM thesis is
right, everything downstream is engineering. If it's wrong (no axiom
set unifies the empirical genomes), the whole substrate framing is
shelved and PARALLAX continues as a tool, not infrastructure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class ObligationId(str, Enum):
    SHARE_ASSET_CONSERVATION = "A1"
    AUTHORIZATION_CLOSURE = "A2"
    SIGNATURE_INTEGRITY = "A3"
    TEMPORAL_DISTINCTNESS = "A4"
    ORACLE_TRUST_BOUNDARY = "A5"


@dataclass
class Obligation:
    id: ObligationId
    name: str
    """Human-readable canonical name."""
    formal_statement: str
    """The mathematical claim, in prose precise enough to check."""
    violation_predicate: str
    """The structural predicate whose truth = a violation."""
    citation: str = ""
    """Where this axiom comes from in mathematical literature, if applicable."""


# ─────────────────────────────────────────────────────────────────
# The five atomic axioms
# ─────────────────────────────────────────────────────────────────

A1_SHARE_ASSET_CONSERVATION = Obligation(
    id=ObligationId.SHARE_ASSET_CONSERVATION,
    name="Share-Asset Conservation",
    formal_statement=(
        "For any vault-like contract V with internal accounting of shares S "
        "and assets A, the exchange rate ER = A/S is monotonically "
        "non-decreasing under user-initiated mints and burns (modulo fees). "
        "ER may decrease only on operations explicitly authorized to do so "
        "(rebalancing losses, slashing, fee distribution to non-shareholders). "
        "Unauthorized ER decrease is a violation."
    ),
    violation_predicate=(
        "There exists an externally-callable operation op such that op "
        "decreases ER, op is not in the explicit-decrease whitelist, and "
        "op does not require admin authorization."
    ),
    citation=(
        "Reformulation of the OpenZeppelin ERC-4626 virtual-shares argument; "
        "originally formalized via the Cream/Harvest 2020 post-mortems."
    ),
)


A2_AUTHORIZATION_CLOSURE = Obligation(
    id=ObligationId.AUTHORIZATION_CLOSURE,
    name="Authorization Closure",
    formal_statement=(
        "For any contract C and any privileged operation P, the set of "
        "addresses with P-membership AUTH(P) is a closed set: (1) it has "
        "a defined initial value at deployment, (2) it can be modified "
        "only by current members of AUTH(P) (the closure property), (3) "
        "every callable function that performs P-equivalent state changes "
        "must check that msg.sender ∈ AUTH(P). Functions that perform P-"
        "equivalent state changes without the membership check violate."
    ),
    violation_predicate=(
        "There exists an externally-callable function f such that f "
        "performs state changes equivalent to a privileged operation P, "
        "and f does not require msg.sender ∈ AUTH(P)."
    ),
    citation=(
        "Formalization of the principle-of-least-privilege as applied to "
        "smart contract authorization; abstracted from Ronin/Multichain/"
        "Nomad-class incidents."
    ),
)


A3_SIGNATURE_INTEGRITY = Obligation(
    id=ObligationId.SIGNATURE_INTEGRITY,
    name="Signature Integrity",
    formal_statement=(
        "For any contract C accepting a signed message m with signature σ "
        "from a designated signer set Σ: (1) σ must be a valid ECDSA "
        "signature of m by some s ∈ Σ (validity), (2) σ must not have "
        "been previously accepted by C (replay protection), (3) m must "
        "have a canonical encoding such that two distinct semantic "
        "messages have distinct hashes (encoding uniqueness)."
    ),
    violation_predicate=(
        "There exists a signed-message path in C such that EITHER (a) "
        "Σ is incompletely initialized at the time of signature check, "
        "OR (b) C lacks a nonce/hash tracking for σ enabling replay, "
        "OR (c) m's encoding admits aliasing (two semantic messages "
        "hashing identically)."
    ),
    citation=(
        "Compendium of EIP-712 best practices + Wormhole/Nomad signature-"
        "bypass post-mortems."
    ),
)


A4_TEMPORAL_DISTINCTNESS = Obligation(
    id=ObligationId.TEMPORAL_DISTINCTNESS,
    name="Temporal Distinctness",
    formal_statement=(
        "For any state transition T that depends on per-actor accumulated "
        "state X (voting weight, stake, lending position, liquidity "
        "contribution): the X value used in evaluating T must come from "
        "a block strictly earlier than the block in which T is recorded. "
        "Equivalently: per-actor accumulated state requires checkpointing "
        "or snapshotting BEFORE it can be used in decision-making."
    ),
    violation_predicate=(
        "There exists a state transition T such that T reads accumulated "
        "state X without snapshotting, AND X can be increased by msg.sender "
        "via a same-block-callable function."
    ),
    citation=(
        "Generalization of Compound/Aave checkpoint patterns; explicit "
        "in Beanstalk 2022 post-mortem."
    ),
)


A5_ORACLE_TRUST_BOUNDARY = Obligation(
    id=ObligationId.ORACLE_TRUST_BOUNDARY,
    name="Oracle Trust Boundary",
    formal_statement=(
        "For any contract C consuming external data D used as input to a "
        "safety-critical decision (collateralization, liquidation, share "
        "pricing, settlement): the cost of manipulating D's source must "
        "exceed the value at stake in the decision, by a margin sufficient "
        "to make manipulation economically infeasible. Sources with low "
        "manipulation cost relative to value-at-stake violate."
    ),
    violation_predicate=(
        "There exists an external read R from source S, used in a "
        "decision affecting value V, such that the cost of moving S's "
        "value by an amount X that materially changes the decision is "
        "substantially less than V."
    ),
    citation=(
        "Synthesis of the Mango Markets, bZx, Harvest, and Compound "
        "post-mortems; formalized via the depth-vs-value-at-stake "
        "argument from the Uniswap V3 oracle docs."
    ),
)


ALL_OBLIGATIONS: List[Obligation] = [
    A1_SHARE_ASSET_CONSERVATION,
    A2_AUTHORIZATION_CLOSURE,
    A3_SIGNATURE_INTEGRITY,
    A4_TEMPORAL_DISTINCTNESS,
    A5_ORACLE_TRUST_BOUNDARY,
]

OBLIGATION_BY_ID: Dict[ObligationId, Obligation] = {a.id: a for a in ALL_OBLIGATIONS}


def obligation_lookup(axiom_id) -> Obligation:
    """Resolve an axiom by id (string or enum)."""
    if isinstance(axiom_id, str):
        axiom_id = ObligationId(axiom_id)
    return OBLIGATION_BY_ID[axiom_id]


__all__ = [
    "ObligationId", "Obligation", "ALL_OBLIGATIONS", "OBLIGATION_BY_ID", "obligation_lookup",
    "A1_SHARE_ASSET_CONSERVATION",
    "A2_AUTHORIZATION_CLOSURE",
    "A3_SIGNATURE_INTEGRITY",
    "A4_TEMPORAL_DISTINCTNESS",
    "A5_ORACLE_TRUST_BOUNDARY",
]
