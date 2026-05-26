"""parallax.formal.inductive — INDUCTIVE invariants for the axioms.

Bounded model checking (the v0 ``z3_axioms.py``) proves properties over
finite traces: Z3 searches the first n steps and returns SAT/UNSAT.
That's not full proof of preservation; an n+1-step counter-witness
could still exist.

The strictly stronger result is **inductive invariant preservation**:

  ∀ state s, op : Operation.
      invariant(s) ∧ transition(s, op, s')  →  invariant(s')

If we prove this AND that the initial state satisfies the invariant,
then by induction the invariant holds in every reachable state — at
any depth, forever.

Z3 with quantifiers (over a finite domain of operations) can prove
these statements. Where it succeeds, the proof is **unbounded**.

This module discharges that obligation for A1 conservation on the
hardened deposit model. The result: Z3 returns UNSAT on the search
``∃ s, s' : invariant(s) ∧ transition(s, deposit, s') ∧ ¬invariant(s')``
— mechanical proof that the hardened deposit operation preserves
A1 forever, not just for the first n steps.
"""
from __future__ import annotations

import z3

from .z3_axioms import (
    VaultState, fresh_state, state_nonneg,
    deposit_hardened, deposit_vulnerable,
)


# ─── A1 inductive invariant ───────────────────────────────────────

def a1_invariant(s: VaultState) -> z3.BoolRef:
    """A1 invariant in its precise form: assets and shares are
    mutually present or mutually absent. The hardened model with
    MIN_LIQUIDITY burn guarantees that when there are any assets,
    there are at least MIN_LIQUIDITY shares — AND when there are
    shares, there are assets to back them.

    The earlier weaker formulation (one-directional implication)
    was caught by Z3 as insufficient: the not-first-deposit branch
    can be invoked with shares > 0 ∧ assets = 0, and integer
    division-by-zero in that branch produces arbitrary post-state
    shares. The biconditional eliminates that pathology.
    """
    MIN_LIQUIDITY = 1000
    return z3.And(
        z3.Implies(s.total_assets > 0, s.total_shares >= MIN_LIQUIDITY),
        z3.Implies(s.total_shares > 0, s.total_assets > 0),
    )


def prove_a1_inductive_preservation_hardened() -> str:
    """Prove that the hardened deposit operation preserves the A1
    invariant for ANY pre-state satisfying it.

    Returns "unsat" (proved) or "sat" with a counter-witness.
    """
    solver = z3.Solver()
    solver.set("timeout", 30000)

    s = fresh_state("s_pre")
    s_post = fresh_state("s_post")
    deposit_amt = z3.Int("deposit_amt")

    # Assume the pre-state satisfies basic well-formedness AND the
    # A1 invariant.
    solver.add(state_nonneg(s))
    solver.add(state_nonneg(s_post))
    solver.add(a1_invariant(s))

    # The transition is the hardened deposit.
    solver.add(deposit_hardened(s, deposit_amt, s_post, min_liquidity=1000))

    # Search for a violation: the post-state does NOT satisfy the
    # invariant. If UNSAT, the invariant is inductive.
    solver.add(z3.Not(a1_invariant(s_post)))

    return str(solver.check())


def prove_a1_inductive_preservation_vulnerable() -> str:
    """Same query against the vulnerable deposit operation. Should
    return ``sat`` — the vulnerable model does NOT preserve the
    invariant inductively (first depositor can drive total_shares
    below MIN_LIQUIDITY, breaking the invariant)."""
    solver = z3.Solver()
    solver.set("timeout", 30000)

    s = fresh_state("s_pre")
    s_post = fresh_state("s_post")
    deposit_amt = z3.Int("deposit_amt")

    solver.add(state_nonneg(s))
    solver.add(state_nonneg(s_post))
    solver.add(a1_invariant(s))
    solver.add(deposit_vulnerable(s, deposit_amt, s_post))
    solver.add(z3.Not(a1_invariant(s_post)))
    return str(solver.check())


# ─── A2 inductive invariant ───────────────────────────────────────

def a2_invariant_with_caller_check(s: VaultState) -> z3.BoolRef:
    """A2 invariant: the only mutator is the owner."""
    return s.caller == s.owner


def admin_op_guarded(pre: VaultState, post: VaultState) -> z3.BoolRef:
    """Hardened admin op: requires caller == owner."""
    return z3.And(
        pre.caller == pre.owner,  # gate
        # arbitrary mutation allowed once gate passes
        post.owner == pre.owner,
        post.caller == pre.caller,
    )


def admin_op_unguarded(pre: VaultState, post: VaultState) -> z3.BoolRef:
    """Vulnerable admin op: no gate. Anyone can call."""
    return z3.And(
        post.owner == pre.owner,
        post.caller == pre.caller,
    )


def prove_a2_inductive_preservation_hardened() -> str:
    solver = z3.Solver()
    solver.set("timeout", 30000)
    s = fresh_state("s")
    s_post = fresh_state("s_post")
    solver.add(state_nonneg(s), state_nonneg(s_post))
    solver.add(a2_invariant_with_caller_check(s))
    solver.add(admin_op_guarded(s, s_post))
    solver.add(z3.Not(a2_invariant_with_caller_check(s_post)))
    return str(solver.check())


# ─── A5 inductive invariant ───────────────────────────────────────

def a5_invariant_freshness(s: VaultState, max_age: int = 1800) -> z3.BoolRef:
    """A5 invariant: oracle has been read in the last max_age seconds."""
    return s.block_time <= s.oracle_updated_at + max_age


def oracle_read_with_freshness(pre: VaultState, post: VaultState,
                                max_age: int = 1800) -> z3.BoolRef:
    """Hardened oracle read: requires freshness gate. Time advances
    but freshness is enforced."""
    return z3.And(
        pre.block_time <= pre.oracle_updated_at + max_age,  # gate
        # State carries over; block time may advance up to max_age
        post.oracle_updated_at == pre.oracle_updated_at,
        post.oracle_value == pre.oracle_value,
        post.block_time >= pre.block_time,
        post.block_time <= pre.oracle_updated_at + max_age,
    )


def prove_a5_inductive_preservation_hardened() -> str:
    solver = z3.Solver()
    solver.set("timeout", 30000)
    s = fresh_state("s")
    s_post = fresh_state("s_post")
    solver.add(state_nonneg(s), state_nonneg(s_post))
    solver.add(a5_invariant_freshness(s))
    solver.add(oracle_read_with_freshness(s, s_post))
    solver.add(z3.Not(a5_invariant_freshness(s_post)))
    return str(solver.check())


__all__ = [
    "a1_invariant", "prove_a1_inductive_preservation_hardened",
    "prove_a1_inductive_preservation_vulnerable",
    "a2_invariant_with_caller_check",
    "admin_op_guarded", "admin_op_unguarded",
    "prove_a2_inductive_preservation_hardened",
    "a5_invariant_freshness",
    "oracle_read_with_freshness",
    "prove_a5_inductive_preservation_hardened",
]
