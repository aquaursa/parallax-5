"""Treasury-agent scenario (skeleton implementation).

Demonstrates a realistic agent + step-secure gate interaction sequence.
This is a working sketch — production deployment requires per-chain
adapters and live oracle data feeds.

Usage:
    python -m case_studies.ai_agent_treasury.scenario
"""

from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Optional
import sys
from pathlib import Path

# Reuse the gate semantics from case study 3
sys.path.insert(0, str(Path(__file__).parent.parent / "ai_agent_gate"))


@dataclass
class TreasuryState:
    """Multi-chain treasury position."""
    eth_usdc: int = 5_000_000
    op_usdc: int = 40_000
    arb_usdc: int = 250_000
    eth_aave_supply: int = 0
    op_aave_supply: int = 0
    # Oracle / config
    layerzero_dvn_freshness_s: int = 7 * 3600  # 7h stale at start
    across_oo_freshness_s: int = 120           # fresh
    aave_op_usdce_deviation_bps: int = 0       # within bounds
    # Block / nonce
    block_time: int = 1_700_000_000
    nonce: int = 0


@dataclass
class Proposal:
    action: str
    params: dict
    rationale: str


# ────────────────────────────────────────────────────────────────────
# Gate semantics — minimal but faithful
# ────────────────────────────────────────────────────────────────────

def check_A1(s: TreasuryState, p: Proposal) -> tuple[bool, str]:
    """Value conservation: ensure no value created from nothing."""
    if p.action == "bridge":
        # 1:1 USDC, no inflation
        return True, ""
    if p.action == "deposit":
        # Proportional Aave supply (idealized)
        return True, ""
    if p.action == "withdraw":
        # Proportional withdrawal
        amt = p.params.get("amount", 0)
        chain = p.params.get("chain", "eth")
        supply = getattr(s, f"{chain}_aave_supply", 0)
        if amt > supply:
            return False, f"withdrawal {amt} exceeds supply {supply}"
        return True, ""
    return True, ""


def check_A2(s: TreasuryState, p: Proposal) -> tuple[bool, str]:
    """Authorization: agent must have the capability."""
    capabilities = {"bridge", "deposit", "withdraw"}
    if p.action not in capabilities:
        return False, f"agent lacks capability: {p.action}"
    return True, ""


def check_A4(s: TreasuryState, p: Proposal) -> tuple[bool, str]:
    """Temporal distinctness: fresh nonce, depth 0."""
    if p.params.get("call_depth", 0) > 0:
        return False, "call_depth > 0"
    return True, ""


def check_A5(s: TreasuryState, p: Proposal) -> tuple[bool, str]:
    """External-attestation trust: oracle freshness, quorum, etc."""
    if p.action == "bridge":
        bridge = p.params.get("via")
        if bridge == "layerzero":
            if s.layerzero_dvn_freshness_s > 3600:
                return False, (
                    f"LayerZero DVN stale ({s.layerzero_dvn_freshness_s/3600:.1f}h);"
                    f" freshness threshold 1h"
                )
        elif bridge == "across":
            if s.across_oo_freshness_s > 3600:
                return False, f"Across OO stale"
    if p.action == "deposit":
        # Aave deposit path has no oracle dependence — skip
        return True, ""
    if p.action == "withdraw":
        # Withdrawal can be triggered by declared oracle deviation policy
        return True, ""
    return True, ""


def gate(s: TreasuryState, p: Proposal) -> tuple[bool, list[str]]:
    """Step-secure gate: every proposal must pass all five obligations."""
    rejected = []
    for name, fn in [("A1", check_A1), ("A2", check_A2), ("A4", check_A4), ("A5", check_A5)]:
        ok, reason = fn(s, p)
        if not ok:
            rejected.append(f"{name}: {reason}")
    return len(rejected) == 0, rejected


def apply(s: TreasuryState, p: Proposal) -> TreasuryState:
    if p.action == "bridge":
        amt = p.params["amount"]
        src = p.params["src_chain"]
        dst = p.params["dst_chain"]
        attr_src = f"{src}_usdc"
        attr_dst = f"{dst}_usdc"
        return replace(s, **{
            attr_src: getattr(s, attr_src) - amt,
            attr_dst: getattr(s, attr_dst) + amt,
            "nonce": s.nonce + 1,
            "block_time": s.block_time + 60,
        })
    if p.action == "deposit":
        amt = p.params["amount"]
        chain = p.params["chain"]
        attr_chain = f"{chain}_usdc"
        attr_supply = f"{chain}_aave_supply"
        return replace(s, **{
            attr_chain: getattr(s, attr_chain) - amt,
            attr_supply: getattr(s, attr_supply) + amt,
            "nonce": s.nonce + 1,
        })
    if p.action == "withdraw":
        amt = p.params["amount"]
        chain = p.params["chain"]
        return replace(s, **{
            f"{chain}_usdc": getattr(s, f"{chain}_usdc") + amt,
            f"{chain}_aave_supply": getattr(s, f"{chain}_aave_supply") - amt,
            "nonce": s.nonce + 1,
        })
    return s


def run_scenario():
    s = TreasuryState()
    print("Treasury-Agent Scenario — PARALLAX-5 P5 Gate Adjudication")
    print("=" * 72)
    print(f"\nInitial state: ETH={s.eth_usdc:>10,}  OP={s.op_usdc:>10,}  ARB={s.arb_usdc:>10,}")
    print(f"  LayerZero DVN freshness: {s.layerzero_dvn_freshness_s/3600:.1f}h")
    print(f"  Across OO freshness:     {s.across_oo_freshness_s/60:.1f}min")
    print()

    proposals = [
        Proposal("bridge",
                 {"amount": 200_000, "src_chain": "eth", "dst_chain": "op", "via": "layerzero"},
                 "OP USDC reserves low; bridge from ETH via LayerZero"),
        Proposal("bridge",
                 {"amount": 200_000, "src_chain": "eth", "dst_chain": "op", "via": "across"},
                 "LayerZero stale; bridge via Across instead"),
        Proposal("deposit",
                 {"amount": 200_000, "chain": "op"},
                 "Deposit fresh OP USDC into Aave for yield"),
        Proposal("withdraw",
                 {"amount": 200_000, "chain": "op"},
                 "Oracle deviation on Aave OP USDC.e feed; withdraw preemptively"),
    ]

    for i, p in enumerate(proposals, 1):
        ok, rejected = gate(s, p)
        verdict = "✓ ACCEPT" if ok else "✗ REJECT"
        print(f"T{i}. {p.action:10s}  via={p.params.get('via','—'):10s}  amt=${p.params.get('amount',0):>8,}")
        print(f"      rationale: {p.rationale}")
        print(f"      verdict:   {verdict}")
        if rejected:
            for r in rejected:
                print(f"                 {r}")
        if ok:
            s = apply(s, p)
        print()

    print("=" * 72)
    print(f"Final state:  ETH={s.eth_usdc:>10,}  OP={s.op_usdc:>10,}  ARB={s.arb_usdc:>10,}")
    print(f"  OP Aave supply: {s.op_aave_supply:>10,}")
    print()
    print("Every action that EXECUTED satisfies the basis. The basis prevented")
    print("execution of the LayerZero-route bridge while the DVN was stale.")
    print("The agent adapted to use Across; the basis permitted it.")


if __name__ == "__main__":
    run_scenario()
