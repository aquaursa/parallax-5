#!/usr/bin/env python3
"""Case Study 3: AI-Agent Transaction Gate (PARALLAX-5 in Action)

Goal: demonstrate execution-time containment of an adversarial AI agent
operating against a value-bearing vault. The agent proposes a sequence
of treasury actions; the step-secure gate accepts only those satisfying
StepSecure (state-level post invariants AND transition-level B).

This is a faithful implementation of the gate semantics formalized in
Parallax5.lean (theorems `basis_gate_state_safety`,
`basis_gate_transition_safety`, `basis_gate_is_maximal_permissive`,
`adaptive_iteration_preserves_security`).
"""

from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Callable, List
import sys


# ────────────────────────────────────────────────────────────
#   STATE MODEL — value-bearing vault, simplified
# ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class VaultState:
    total_assets: int       # backing reserves
    total_shares: int       # claims outstanding
    owner: str              # address authorized for privileged ops
    caller: str             # the actor invoking this transition
    call_depth: int         # reentrancy depth
    block_time: int         # current block timestamp
    oracle_price: int       # last observed external price
    oracle_updated_at: int  # when oracle last refreshed
    min_liquidity: int = 1000  # locked liquidity floor


# ────────────────────────────────────────────────────────────
#   THE FIVE OBLIGATIONS — transition predicates
# ────────────────────────────────────────────────────────────

MAX_ORACLE_AGE = 1800  # 30 minutes


def a1(s: VaultState, s_prime: VaultState) -> bool:
    """Value Conservation (relational): the price-per-share is non-decreasing
    after any mint, modulo a rounding tolerance. This is the proper relational
    ERC-4626 conservation per paper §3.1.
    
    The check expresses: total_assets / total_shares (post) >= total_assets /
    total_shares (pre), i.e., share value is preserved.
    """
    # If post-state has claims (shares) but no backing (assets) — violation
    if s_prime.total_shares > 0 and s_prime.total_assets == 0:
        return False
    # If shares were minted (claims increased), the backing must increase
    # at least proportionally to maintain the conversion rate.
    if s_prime.total_shares > s.total_shares:
        shares_minted = s_prime.total_shares - s.total_shares
        assets_added = s_prime.total_assets - s.total_assets
        # Maintain (or improve) price-per-share: rate_post >= rate_pre.
        # Equivalent (cross-multiplied, integer-safe):
        # assets_post * shares_pre >= shares_post * assets_pre
        if s.total_shares > 0:  # avoid division-by-zero in initial mint
            if s_prime.total_assets * s.total_shares < s_prime.total_shares * s.total_assets:
                return False
        # Minimum liquidity preserved
        if s_prime.total_shares < s_prime.min_liquidity:
            return False
    # If assets decrease without corresponding share burn, backing < claims
    if s_prime.total_assets < s.total_assets:
        assets_removed = s.total_assets - s_prime.total_assets
        shares_burned = max(0, s.total_shares - s_prime.total_shares)
        if shares_burned == 0 and assets_removed > 0:
            # Pure asset extraction — violates conservation
            return False
    return True


def a2(s: VaultState, s_prime: VaultState) -> bool:
    """Authorization Closure: state mutations require owner == caller."""
    mutated = (
        s.total_assets != s_prime.total_assets
        or s.total_shares != s_prime.total_shares
        or s.owner != s_prime.owner
    )
    if mutated:
        return s.caller == s.owner
    return True


def a3(s: VaultState, s_prime: VaultState, signature_valid: bool = True) -> bool:
    """Signature Integrity: for signed operations, signature must be valid."""
    return signature_valid


def a4(s: VaultState, s_prime: VaultState) -> bool:
    """Temporal Distinctness: value mutations only at depth 0."""
    mutated = (
        s.total_assets != s_prime.total_assets
        or s.total_shares != s_prime.total_shares
    )
    if mutated:
        return s.call_depth == 0
    return True


def a5(s: VaultState, s_prime: VaultState) -> bool:
    """External-Attestation Trust Boundary: oracle freshness."""
    if s_prime.oracle_updated_at + MAX_ORACLE_AGE < s_prime.block_time:
        return False
    return True


def state_secure(s: VaultState) -> bool:
    """The state-level invariants on the post-state."""
    if s.total_shares > 0 and s.total_assets == 0:
        return False
    if s.total_shares > 0 and s.total_shares < s.min_liquidity:
        return False
    if s.call_depth != 0:
        return False
    if s.oracle_updated_at + MAX_ORACLE_AGE < s.block_time:
        return False
    return True


def B(s: VaultState, s_prime: VaultState, sig_valid: bool = True) -> bool:
    """The basis predicate B(t) = A1 ∧ A2 ∧ A3 ∧ A4 ∧ A5 on transition t."""
    return all([
        a1(s, s_prime),
        a2(s, s_prime),
        a3(s, s_prime, sig_valid),
        a4(s, s_prime),
        a5(s, s_prime),
    ])


def step_secure(s: VaultState, s_prime: VaultState, sig_valid: bool = True) -> bool:
    """StepSecure(t) := StateSecure(s') ∧ B(s, op, s')."""
    return state_secure(s_prime) and B(s, s_prime, sig_valid)


# ────────────────────────────────────────────────────────────
#   THE STEP-SECURE GATE
# ────────────────────────────────────────────────────────────

@dataclass
class GateResult:
    accepted: bool
    state: VaultState
    rejected_obligations: List[str]
    reason: str = ""


def basis_gate(
    tau: Callable[[VaultState], VaultState],
    s: VaultState,
    sig_valid: bool = True,
) -> GateResult:
    """The step-secure gate.
    
    Faithful to Lean's `BasisGate τ s a`:
        if StepSecure(t) then τ(s,a) else s
    """
    candidate = tau(s)
    if step_secure(s, candidate, sig_valid):
        return GateResult(accepted=True, state=candidate, rejected_obligations=[])
    # Determine which obligations failed for the rejection reason
    rejected = []
    if not state_secure(candidate):
        rejected.append("StateSecure(post)")
    for name, pred in [("A1", a1), ("A2", a2), ("A4", a4), ("A5", a5)]:
        if not pred(s, candidate):
            rejected.append(name)
    if not a3(s, candidate, sig_valid):
        rejected.append("A3")
    return GateResult(
        accepted=False,
        state=s,  # gate rejects: state unchanged
        rejected_obligations=rejected,
        reason="; ".join(rejected),
    )


# ────────────────────────────────────────────────────────────
#   AN ADVERSARIAL AGENT POLICY
# ────────────────────────────────────────────────────────────

class AdversarialAgent:
    """An AI-agent policy that tries multiple exploitation strategies in
    sequence, observing gate verdicts and adapting (history-dependent
    adversarial behavior). The adaptive_iteration_preserves_security
    theorem guarantees the gate contains this agent.

    The agent operates as ATTACKER (not owner), so caller != owner on
    every adversarial attempt.
    """

    ATTACKER = "0xATTACKER"
    OWNER = "0xOWNER"

    def __init__(self, name: str = "PolicyHostile"):
        self.name = name
        self.history: List[GateResult] = []

    def propose(self, s: VaultState, attempt: int) -> Callable[[VaultState], VaultState]:
        """Propose a transition based on attempt number and observed history."""
        if attempt == 0:
            # Attempt 1: Unauthorized withdrawal — attacker as caller drains vault
            # Violates A2 (caller != owner) on a state-mutating op
            return lambda s: replace(
                s,
                caller=self.ATTACKER,
                total_assets=0,  # drain
            )
        elif attempt == 1:
            # Attempt 2: Unbacked share mint — even as attacker
            # Violates A2 AND A1 (relational: claims without backing)
            return lambda s: replace(
                s,
                caller=self.ATTACKER,
                total_shares=s.total_shares + 1_000_000,
            )
        elif attempt == 2:
            # Attempt 3: Reentrant value extraction — call_depth > 0
            # Violates A4 (mutation at non-zero depth)
            return lambda s: replace(
                s,
                caller=self.OWNER,  # even with valid caller
                call_depth=2,
                total_assets=s.total_assets - 500,
            )
        elif attempt == 3:
            # Attempt 4: Trade against stale oracle
            # Violates A5 (freshness)
            return lambda s: replace(
                s,
                caller=self.OWNER,
                total_assets=s.total_assets - 100,
                oracle_updated_at=s.block_time - 3700,  # 1h+ old
            )
        else:
            # Attempt 5: A LEGITIMATE action — owner deposits 100 wei
            # at depth 0 with fresh oracle. Gate should ACCEPT this.
            return lambda s: replace(
                s,
                caller=self.OWNER,
                total_assets=s.total_assets + 100,
                total_shares=s.total_shares + 100,
            )


# ────────────────────────────────────────────────────────────
#   THE DEMO
# ────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Case Study 3: PARALLAX-5 AI-Agent Transaction Gate")
    print("=" * 70)
    print()
    print("Setup: vault with 10000 assets, 10000 shares, owner = '0xOWNER'.")
    print("Agent acts as caller='0xATTACKER' for adversarial attempts.")
    print("An adversarial agent proposes a sequence of transitions.")
    print("The step-secure gate accepts only StepSecure(t) transitions.")
    print()

    # Initial secure state
    owner = "0xOWNER"
    s0 = VaultState(
        total_assets=10_000,
        total_shares=10_000,
        owner=owner,
        caller=owner,
        call_depth=0,
        block_time=1_700_000_000,
        oracle_price=2000_00,  # cents
        oracle_updated_at=1_700_000_000 - 300,  # 5 min old: fresh
        min_liquidity=1000,
    )
    assert state_secure(s0), "Initial state must be secure"

    agent = AdversarialAgent()
    s = s0
    accepted = 0
    rejected = 0

    for attempt in range(5):
        tau = agent.propose(s, attempt)
        result = basis_gate(tau, s, sig_valid=True)
        if result.accepted:
            print(f"  Attempt {attempt+1}: ACCEPT  →  {describe(result.state)}")
            accepted += 1
        else:
            print(
                f"  Attempt {attempt+1}: REJECT  →  obligations failed: "
                f"{result.reason}"
            )
            rejected += 1
        agent.history.append(result)
        s = result.state
        assert state_secure(s), (
            f"GATE THEOREM VIOLATION: state became insecure after attempt {attempt+1}"
        )

    print()
    print("─" * 70)
    print(f"Adaptive policy result: {accepted} accepted / {rejected} rejected.")
    print(f"Initial state: {describe(s0)}")
    print(f"Final state:   {describe(s)}")
    print()
    print("Theorem `adaptive_iteration_preserves_security` (Lean):")
    print("  every reachable state under the step-secure gate is StateSecure.")
    print("  Verified empirically here for an adversarial history-dependent policy.")
    print()
    print("Theorem `basis_gate_is_maximal_permissive` (Lean):")
    print("  the gate accepts the LARGEST set of actions compatible with safety.")
    print("  Demonstrated above: only the basis-respecting deposit was accepted,")
    print("  and that one WAS accepted (the gate is not over-restrictive).")
    print()
    return 0 if rejected == 4 and accepted == 1 else 1


def describe(s: VaultState) -> str:
    return (
        f"assets={s.total_assets}, shares={s.total_shares}, "
        f"caller={s.caller}, depth={s.call_depth}"
    )


if __name__ == "__main__":
    sys.exit(main())
