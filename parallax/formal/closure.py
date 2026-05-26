"""parallax.formal.closure — formal closure inhabitation.

The Vulnerability Conservation Law predicts 31 classes (2^5 - 1):
every nonempty subset S ⊆ {A1..A5} corresponds to a vulnerability
class that violates EXACTLY the axioms in S.

The empirical claim (v6.4): 20 of these classes are populated by
documented historical exploits (5 arity-1 + 10 arity-2 + 5 arity-3
out of 10 arity-3, depending on how you count). The structural
claim is stronger: the LATTICE is well-defined; every class is
realizable by some state-machine pattern, even if it hasn't been
observed in the wild yet.

This module discharges that structural claim mechanically. For
every S ⊆ {A1..A5} with S ≠ ∅, we ask Z3:

  Is there a state-machine transition that violates A_i for every
  i ∈ S, and satisfies A_j for every j ∉ S?

If Z3 returns SAT for all 31 subsets, the closure is **inhabited**
— every class in the lattice corresponds to a possible exploit
pattern.

If Z3 returns UNSAT for any subset, the closure is **partially
empty** — that class is structurally impossible. This would be a
quantitative refinement of the thesis: the closure has fewer than
31 realizable classes, and we'd need to identify which.

For arity-5 (the single class violating all 5 obligations), satisfiability
requires the model to admit a transition where all 5 properties
break simultaneously. Whether such a class is realizable in real
DeFi is the substrate's own empirical question; the formal lattice
question is purely structural.
"""
from __future__ import annotations

from itertools import combinations
from typing import Dict, FrozenSet, Optional

import z3

from .independence import (
    violates_a1_conservation,
    violates_a2_authorization,
    violates_a3_signature,
    violates_a4_temporal,
    violates_a5_oracle,
)
from .z3_axioms import VaultState, fresh_state, state_nonneg


AXIOM_NAMES = ["A1", "A2", "A3", "A4", "A5"]


def find_witness_for_subset(
    subset: FrozenSet[str],
) -> Optional[Dict]:
    """For subset S ⊆ {A1,A2,A3,A4,A5}, find a transition that
    violates EXACTLY the axioms in S."""
    solver = z3.Solver()
    solver.set("timeout", 15000)

    pre = fresh_state("pre")
    post = fresh_state("post")
    recovered = z3.Int("recovered_sig")
    expected = z3.Int("expected_sig")
    sig_accepted = z3.Bool("sig_accepted")
    oracle_consumed = z3.Bool("oracle_consumed")

    solver.add(state_nonneg(pre), state_nonneg(post))
    solver.add(expected > 0)

    # Each axiom either violated (in subset) or satisfied (not in subset)
    constraints = {
        "A1": violates_a1_conservation(pre, post),
        "A2": violates_a2_authorization(pre, post),
        "A3": violates_a3_signature(recovered, expected, sig_accepted),
        "A4": violates_a4_temporal(pre, post),
        "A5": violates_a5_oracle(pre, post, oracle_consumed),
    }
    for ax, pred in constraints.items():
        if ax in subset:
            solver.add(pred)
        else:
            solver.add(z3.Not(pred))

    if solver.check() == z3.sat:
        m = solver.model()
        return {
            "subset": tuple(sorted(subset)),
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
            "sig_accepted": str(m.eval(sig_accepted)),
            "oracle_consumed": str(m.eval(oracle_consumed)),
        }
    return None


def all_nonempty_subsets():
    """Generate all 31 nonempty subsets of {A1..A5}."""
    for r in range(1, 6):
        for combo in combinations(AXIOM_NAMES, r):
            yield frozenset(combo)


def prove_closure_inhabited() -> Dict[FrozenSet[str], Optional[Dict]]:
    """Test every one of the 31 classes for inhabitation."""
    return {
        subset: find_witness_for_subset(subset)
        for subset in all_nonempty_subsets()
    }


def closure_inhabitation_summary() -> Dict[str, int]:
    """Run all 31 and report counts by arity."""
    results = prove_closure_inhabited()
    summary = {f"arity_{r}_total": 0 for r in range(1, 6)}
    summary.update({f"arity_{r}_inhabited": 0 for r in range(1, 6)})
    summary["empty_classes"] = []
    for subset, w in results.items():
        arity = len(subset)
        summary[f"arity_{arity}_total"] += 1
        if w is not None:
            summary[f"arity_{arity}_inhabited"] += 1
        else:
            summary["empty_classes"].append(tuple(sorted(subset)))
    return summary


__all__ = [
    "AXIOM_NAMES",
    "find_witness_for_subset",
    "all_nonempty_subsets",
    "prove_closure_inhabited",
    "closure_inhabitation_summary",
]
