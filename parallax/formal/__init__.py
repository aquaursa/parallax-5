"""parallax.formal — actual Z3-based formal verification of the
5 PARALLAX axioms.

This module exists because the external Lean attempts produced
machine-uncheckable artifacts (sorry-stubbed theorems, ellipsis
placeholders, vacuous helper definitions). Z3 is a real SMT solver;
its UNSAT verdicts are proofs and its SAT witnesses are concrete
counter-models.

Reasonable formal-verification claim from this module:

  * The axioms admit a precise SMT formulation over a simplified
    vault state-machine.
  * For each axiom, there exists a vulnerable variant where Z3
    finds a counter-witness, and a hardened variant where Z3
    proves no witness exists (bounded UNSAT).
  * This is bounded model checking, not full completeness. Full
    EVM verification requires KEVM / Yul-Lean.

What this module is NOT:

  * Not a proof that the 5-axiom basis is complete.
  * Not a substitute for halmos symbolic execution of real Solidity.
  * Not a substitute for runtime detection (ObligationSol, the
    homology engine, the Agent Substrate).

It IS the level of rigor that the Vulnerability Conservation Law
thesis would need to back its strongest claims with mechanical
evidence.
"""
from .z3_axioms import (
    VaultState, fresh_state, state_nonneg,
    deposit_vulnerable, deposit_hardened,
    can_violate_a1_first_depositor,
    can_violate_a4_reentrancy,
    can_violate_a5_no_freshness_check,
    cannot_violate_a5_with_freshness_check,
    can_violate_a2_no_caller_check,
    cannot_violate_a2_with_caller_check,
    can_violate_a3_no_zero_check,
    cannot_violate_a3_with_both_checks,
)

__all__ = [
    "VaultState", "fresh_state", "state_nonneg",
    "deposit_vulnerable", "deposit_hardened",
    "can_violate_a1_first_depositor",
    "can_violate_a4_reentrancy",
    "can_violate_a5_no_freshness_check",
    "cannot_violate_a5_with_freshness_check",
    "can_violate_a2_no_caller_check",
    "cannot_violate_a2_with_caller_check",
    "can_violate_a3_no_zero_check",
    "cannot_violate_a3_with_both_checks",
]
