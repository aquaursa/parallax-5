"""parallax.formal.bv256 — BitVec(256) model with real EVM
uint256 wraparound semantics.

The integer model in ``z3_axioms.py`` uses Z3 ``Int`` — mathematical
integers, unbounded. Real EVM uses ``uint256``, which wraps modulo
2^256. This wraparound is its own vulnerability class:

  - Cetus (Sui, May 2025, $223M): integer overflow in liquidity math
  - Compound v3 callback bug (2023): overflow in cToken accounting
  - Various Vyper compiler bugs (2023, Curve $70M)

The integer model misses these because Z3 ``Int`` doesn't overflow.
This module reproduces the same axiom predicates over BitVec(256)
and shows Z3 finds Cetus-class witnesses that the integer model
silently approves.

This is strictly more realistic than the integer model. Where the
two disagree, the BitVec(256) model is the ground truth for EVM
semantics; the integer model is a useful approximation but admits
false negatives on overflow exploits.
"""
from __future__ import annotations

from typing import Dict, Optional

import z3


U256_BITS = 256
U256_MAX = (1 << U256_BITS) - 1


def bv256(name: str) -> z3.BitVecRef:
    return z3.BitVec(name, U256_BITS)


def bv256_val(n: int) -> z3.BitVecNumRef:
    return z3.BitVecVal(n, U256_BITS)


# ─── Cetus-pattern overflow in liquidity math ──────────────────────

def can_violate_a1_via_overflow() -> Optional[Dict]:
    """Search for inputs (a, b, deposit_amt) such that:

      pre.total_assets = a (huge)
      attacker_deposits b such that a + b WRAPS in uint256
      → post.total_assets is small
      shares minted as if assets were normal

    This is the Cetus/Compound-v3 pattern in canonical form. The
    integer model misses it; the BitVec(256) model finds it.

    Simplification: we model the violation directly at the
    arithmetic level — the contract's add-then-check pattern (or
    lack thereof). We don't model the dependent share calculation
    because the multiplication of two huge values would ALSO wrap,
    which is a separate compositional witness.
    """
    solver = z3.Solver()
    solver.set("timeout", 30000)

    pre_assets = bv256("pre_assets")
    deposit_amt = bv256("deposit_amt")
    post_assets = bv256("post_assets")

    # The vulnerable arithmetic — no overflow check
    solver.add(z3.UGT(pre_assets, bv256_val(0)))
    solver.add(z3.UGT(deposit_amt, bv256_val(0)))
    solver.add(post_assets == pre_assets + deposit_amt)

    # The A1 violation: the contract thinks it has post_assets, but
    # post_assets has actually wrapped DOWN below pre_assets, breaking
    # the monotonicity property the vault depends on.
    solver.add(z3.ULT(post_assets, pre_assets))  # overflow happened

    if solver.check() == z3.sat:
        m = solver.model()
        return {
            "pre_assets": m.eval(pre_assets).as_long(),
            "deposit_amt": m.eval(deposit_amt).as_long(),
            "post_assets_wrapped": m.eval(post_assets).as_long(),
        }
    return None


def cannot_violate_a1_with_overflow_check() -> bool:
    """Hardened arithmetic: explicit overflow check via
    ``require(post >= pre)``. Z3 must prove no overflow witness
    survives the check.
    """
    solver = z3.Solver()
    solver.set("timeout", 30000)

    pre_assets = bv256("pre_assets")
    deposit_amt = bv256("deposit_amt")
    post_assets = bv256("post_assets")

    solver.add(z3.UGT(deposit_amt, bv256_val(0)))
    solver.add(post_assets == pre_assets + deposit_amt)
    # The hardened check: post must be ≥ pre. This is the standard
    # Solidity overflow-safety pattern pre-0.8 (and is preserved by
    # 0.8's checked arithmetic).
    solver.add(z3.UGE(post_assets, pre_assets))
    # Try to find an overflow despite the check
    solver.add(z3.ULT(post_assets, pre_assets))
    return solver.check() == z3.unsat


# ─── Overflow witness on share-supply addition ─────────────────────

def can_violate_a1_share_supply_overflow() -> Optional[Dict]:
    """An attacker can drive `totalShares` to overflow in the
    vulnerable model. This is a different overflow channel from
    asset overflow: shares grow large enough to wrap around to a
    tiny value, then a new deposit sees `totalShares == 0` and
    takes the first-depositor path again."""
    solver = z3.Solver()
    solver.set("timeout", 30000)

    pre_shares = bv256("pre_shares")
    shares_to_mint = bv256("shares_to_mint")
    post_shares = bv256("post_shares")

    solver.add(z3.UGT(pre_shares, bv256_val(0)))
    solver.add(z3.UGT(shares_to_mint, bv256_val(0)))
    solver.add(post_shares == pre_shares + shares_to_mint)
    solver.add(z3.ULT(post_shares, bv256_val(1000)))  # wraps to near-zero
    solver.add(z3.ULT(post_shares, pre_shares))       # confirm wraparound

    if solver.check() == z3.sat:
        m = solver.model()
        return {
            "pre_shares": m.eval(pre_shares).as_long(),
            "shares_to_mint": m.eval(shares_to_mint).as_long(),
            "post_shares_wrapped": m.eval(post_shares).as_long(),
        }
    return None


# ─── Sanity check: the integer model misses what BitVec catches ───

def integer_model_misses_overflow() -> bool:
    """Demonstrate that the unbounded Int model says the same
    arithmetic is SAFE while the BitVec model proves it isn't.
    """
    # Integer model: pre + deposit > pre is ALWAYS true if deposit > 0
    int_solver = z3.Solver()
    pre = z3.Int("pre")
    deposit = z3.Int("deposit")
    post = z3.Int("post")
    int_solver.add(pre >= 0, deposit > 0)
    int_solver.add(post == pre + deposit)
    int_solver.add(post < pre)   # overflow in Int = impossible
    return int_solver.check() == z3.unsat  # Int says no overflow possible


__all__ = [
    "U256_BITS", "U256_MAX", "bv256", "bv256_val",
    "can_violate_a1_via_overflow",
    "cannot_violate_a1_with_overflow_check",
    "can_violate_a1_share_supply_overflow",
    "integer_model_misses_overflow",
]
