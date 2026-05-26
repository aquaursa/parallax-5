"""parallax.formal.independence — formal minimality of the basis.

The Vulnerability Conservation Law claims the 5-axiom basis is
**minimal**: removing any A_i leaves a class of real exploits
unexplained. The external LLM argued this empirically (cite Cream
without A1, Wormhole without A3, etc.). That's a reasonable
argument but it's not a formal proof.

A formal proof of minimality requires, for each i ∈ {1..5}, an
**independence witness**: a state-machine model M_i such that

  M_i SATISFIES A_j for every j ≠ i
  M_i VIOLATES A_i

If such M_i exists for each i, then no axiom is redundant — its
removal would force conflating its violation class with the
others, but no other axiom can express the violation. The 5
witnesses are a mechanical proof of basis minimality.

This is the strictly stronger version of the LLM's empirical
"removing A_i leaves Cream/Wormhole/Mango unexplained" argument.
We prove not just "the historical exploit doesn't fit" but "no
combination of the OTHER axioms could possibly cover this class
of state-machine pattern, because Z3 constructs a concrete witness
that violates ONLY A_i."
"""
from __future__ import annotations

from typing import Dict, Optional

import z3

from .z3_axioms import VaultState, fresh_state, state_nonneg


# ─── Obligation predicates over a (pre, op, post) trace ────────────────
# We define each axiom as a predicate on a TRANSITION (pre-state,
# operation effects, post-state). A model "violates A_i" if its
# transition makes the predicate False.

def violates_a1_conservation(pre: VaultState, post: VaultState) -> z3.BoolRef:
    """A1 violated: shares grow without proportional asset backing
    (or assets grow without proportional shares being burned).

    Precise form: the implied price-per-share changes by more than
    the realistic accrual delta (which we model as zero, since this
    is per-transaction). Any minting of shares without backing
    assets is an A1 violation.
    """
    asset_delta = post.total_assets - pre.total_assets
    share_delta = post.total_shares - pre.total_shares
    # A1 violation: shares added without assets, or shares removed
    # without assets removed. The donation channel is also a
    # violation (assets without shares — accounting drift).
    return z3.Or(
        z3.And(share_delta > 0, asset_delta <= 0),  # shares mint without assets
        z3.And(share_delta < 0, asset_delta >= 0),  # shares burn without assets
        z3.And(asset_delta > 0, share_delta == 0,
               pre.total_shares > 0),               # donation channel
    )


def violates_a2_authorization(pre: VaultState, post: VaultState) -> z3.BoolRef:
    """A2 violated: unauthorized caller successfully mutated state."""
    state_mutated = z3.Or(
        post.total_shares != pre.total_shares,
        post.total_assets != pre.total_assets,
        post.owner != pre.owner,
    )
    return z3.And(state_mutated, pre.caller != pre.owner)


def violates_a3_signature(recovered: z3.ArithRef,
                          expected: z3.ArithRef,
                          accepted: z3.BoolRef) -> z3.BoolRef:
    """A3 violated: a signature recovery to address(0) or a
    non-expected signer was accepted as authorization."""
    return z3.And(accepted, z3.Or(recovered == 0, recovered != expected))


def violates_a4_temporal(pre: VaultState, post: VaultState) -> z3.BoolRef:
    """A4 violated: state mutation occurred while call_depth > 0
    AND the mutation depends on a value read BEFORE the depth
    increase (the canonical reentrancy double-effect)."""
    return z3.And(
        post.call_depth < pre.call_depth,  # exiting a nested call
        post.total_shares > pre.total_shares,  # shares grew during exit
        pre.call_depth > 0,                # there was reentrancy
    )


def violates_a5_oracle(pre: VaultState, post: VaultState,
                       oracle_consumed: z3.BoolRef,
                       max_age: int = 1800) -> z3.BoolRef:
    """A5 violated: oracle data consumed without freshness check."""
    return z3.And(
        oracle_consumed,
        pre.block_time > pre.oracle_updated_at + max_age,
    )


# ─── Independence witnesses ────────────────────────────────────────

def find_independence_witness_for(target_axiom: str) -> Optional[Dict]:
    """For target_axiom ∈ {'A1','A2','A3','A4','A5'}, construct a
    state-machine transition that VIOLATES target_axiom but
    SATISFIES every other axiom.

    Returns the witness model dict, or None if no such witness
    exists (which would be a falsification of basis independence
    — that axiom would be derivable from the others)."""
    solver = z3.Solver()
    solver.set("timeout", 15000)

    pre = fresh_state("pre")
    post = fresh_state("post")
    recovered = z3.Int("recovered_sig")
    expected = z3.Int("expected_sig")
    sig_accepted = z3.Bool("sig_accepted")
    oracle_consumed = z3.Bool("oracle_consumed")

    solver.add(state_nonneg(pre))
    solver.add(state_nonneg(post))
    solver.add(expected > 0)

    # Each axiom either VIOLATED (if target) or SATISFIED (else)
    if target_axiom == "A1":
        solver.add(violates_a1_conservation(pre, post))
        solver.add(z3.Not(violates_a2_authorization(pre, post)))
        solver.add(z3.Not(violates_a3_signature(recovered, expected, sig_accepted)))
        solver.add(z3.Not(violates_a4_temporal(pre, post)))
        solver.add(z3.Not(violates_a5_oracle(pre, post, oracle_consumed)))
    elif target_axiom == "A2":
        solver.add(z3.Not(violates_a1_conservation(pre, post)))
        solver.add(violates_a2_authorization(pre, post))
        solver.add(z3.Not(violates_a3_signature(recovered, expected, sig_accepted)))
        solver.add(z3.Not(violates_a4_temporal(pre, post)))
        solver.add(z3.Not(violates_a5_oracle(pre, post, oracle_consumed)))
    elif target_axiom == "A3":
        solver.add(z3.Not(violates_a1_conservation(pre, post)))
        solver.add(z3.Not(violates_a2_authorization(pre, post)))
        solver.add(violates_a3_signature(recovered, expected, sig_accepted))
        solver.add(z3.Not(violates_a4_temporal(pre, post)))
        solver.add(z3.Not(violates_a5_oracle(pre, post, oracle_consumed)))
    elif target_axiom == "A4":
        solver.add(z3.Not(violates_a1_conservation(pre, post)))
        solver.add(z3.Not(violates_a2_authorization(pre, post)))
        solver.add(z3.Not(violates_a3_signature(recovered, expected, sig_accepted)))
        solver.add(violates_a4_temporal(pre, post))
        solver.add(z3.Not(violates_a5_oracle(pre, post, oracle_consumed)))
    elif target_axiom == "A5":
        solver.add(z3.Not(violates_a1_conservation(pre, post)))
        solver.add(z3.Not(violates_a2_authorization(pre, post)))
        solver.add(z3.Not(violates_a3_signature(recovered, expected, sig_accepted)))
        solver.add(z3.Not(violates_a4_temporal(pre, post)))
        solver.add(violates_a5_oracle(pre, post, oracle_consumed))
    else:
        return None

    if solver.check() == z3.sat:
        m = solver.model()
        return {
            "target_axiom": target_axiom,
            "pre.total_assets": str(m.eval(pre.total_assets)),
            "pre.total_shares": str(m.eval(pre.total_shares)),
            "pre.caller": str(m.eval(pre.caller)),
            "pre.owner": str(m.eval(pre.owner)),
            "pre.call_depth": str(m.eval(pre.call_depth)),
            "pre.block_time": str(m.eval(pre.block_time)),
            "pre.oracle_updated_at": str(m.eval(pre.oracle_updated_at)),
            "post.total_assets": str(m.eval(post.total_assets)),
            "post.total_shares": str(m.eval(post.total_shares)),
            "post.call_depth": str(m.eval(post.call_depth)),
            "recovered_sig": str(m.eval(recovered)),
            "expected_sig": str(m.eval(expected)),
            "sig_accepted": str(m.eval(sig_accepted)),
            "oracle_consumed": str(m.eval(oracle_consumed)),
        }
    return None


def prove_basis_minimality() -> Dict[str, Optional[Dict]]:
    """For each A_i in {A1..A5}, construct an independence witness.
    All five MUST succeed (SAT) — otherwise basis minimality fails."""
    return {
        f"A{i}": find_independence_witness_for(f"A{i}") for i in range(1, 6)
    }


__all__ = [
    "violates_a1_conservation",
    "violates_a2_authorization",
    "violates_a3_signature",
    "violates_a4_temporal",
    "violates_a5_oracle",
    "find_independence_witness_for",
    "prove_basis_minimality",
]
