"""PARALLAX-5 Observation-Set-Parameterized Basis-Observability.

The original definition — "a transition is basis-observable iff a sound
gate would reject it" — is too coarse, as external reviewers correctly
observed. A monitor's reach depends on what it can SEE. Different
classes of observations yield different reach.

This module defines four canonical observation sets and the parameterized
basis-observability predicate. It then re-classifies each catalog entry
under each observation set.

Observation sets (cumulative):

    Ω_chain  ⊂  Ω_config  ⊂  Ω_intent  ⊂  Ω_infra

  Ω_chain   :  on-chain state and transaction data only
              (what a contract running inside the EVM sees)

  Ω_config  :  + declared protocol configuration
              (verifier quorum, oracle source set, risk parameters,
               admin-role membership)

  Ω_intent  :  + signer intent, governance proposal metadata,
                wallet UI context, off-chain co-signed pre-images

  Ω_infra   :  + external infrastructure state
              (KMS integrity, RPC compromise, DNS status,
               validator-node health)

Drift Protocol illustrates the distinction:
  - Ω_chain-unobservable   (admin properly authorized to whitelist)
  - Ω_config-observable    (CVT whitelisted without standard onboarding delay)
  - Ω_intent-observable    (signer didn't intend to whitelist CVT for theft)
  - Ω_infra-observable     (DPRK social engineering — but outside basis)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet


class Omega(str, Enum):
    """The four canonical observation sets."""
    CHAIN = "chain"        # on-chain state + tx data only
    CONFIG = "config"      # + declared protocol configuration
    INTENT = "intent"      # + signer intent, proposal metadata
    INFRA = "infra"        # + external infrastructure state


# Cumulative ordering: each set contains all observations of the previous
OMEGA_ORDER = [Omega.CHAIN, Omega.CONFIG, Omega.INTENT, Omega.INFRA]


def omega_contains(larger: Omega, smaller: Omega) -> bool:
    """Whether `larger` observation set contains `smaller`."""
    return OMEGA_ORDER.index(larger) >= OMEGA_ORDER.index(smaller)


@dataclass(frozen=True)
class ObservabilityProfile:
    """Per-incident observability classification under each Ω."""
    # Smallest Ω under which this transition is basis-observable
    min_observable_omega: Omega
    # If Ω_infra-unobservable, the transition is genuinely irreducible
    is_basis_observable_under_any: bool = True
    # Brief rationale
    rationale: str = ""

    def observable_under(self, omega: Omega) -> bool:
        """Is this transition basis-observable under observation set Ω?"""
        if not self.is_basis_observable_under_any:
            return False
        return omega_contains(omega, self.min_observable_omega)


# ────────────────────────────────────────────────────────────────
# Re-classification of catalog entries under the parameterized scheme
# ────────────────────────────────────────────────────────────────
#
# Each entry maps a (protocol, year, loss_usd) tuple to its observability
# profile. The minimum Ω required for observability gives the precise
# information requirement the monitor must satisfy.

CATALOG_OBSERVABILITY: dict[tuple[str, str], ObservabilityProfile] = {
    # === Pure on-chain code bugs: Ω_chain-observable ===
    ("Cream Finance (1st)", "2021-08-30"): ObservabilityProfile(
        min_observable_omega=Omega.CHAIN,
        rationale="A1 violation visible from on-chain reserves/shares ratio"
    ),
    ("Cream Finance (2nd)", "2021-10-27"): ObservabilityProfile(
        min_observable_omega=Omega.CHAIN,
        rationale="A1 + flash-loan-induced oracle deviation on-chain"
    ),
    ("Beanstalk", "2022-04-17"): ObservabilityProfile(
        min_observable_omega=Omega.CHAIN,
        rationale="A2: flash-loan governance, no time-locked authorization"
    ),
    ("DAO (The)", "2016-06-17"): ObservabilityProfile(
        min_observable_omega=Omega.CHAIN,
        rationale="A4: reentrancy at non-zero call depth"
    ),
    ("Truebit", "2026-01-08"): ObservabilityProfile(
        min_observable_omega=Omega.CHAIN,
        rationale="A1: integer overflow in mint pricing, visible on-chain"
    ),

    # === Config-level vulnerabilities: require Ω_config ===
    # Kelp DAO: 1-of-1 verifier is a config-level violation observable
    # to a monitor that knows the declared quorum requirement
    ("Kelp DAO / LayerZero", "2026-04-18"): ObservabilityProfile(
        min_observable_omega=Omega.CONFIG,
        rationale="A5: 1-of-1 DVN configuration violates q-of-n requirement at deploy time"
    ),
    # Drift Protocol: collateral whitelist without standard onboarding delay
    # is observable to a monitor that knows the declared listing policy
    ("Drift Protocol", "2026-04-01"): ObservabilityProfile(
        min_observable_omega=Omega.CONFIG,
        rationale="A5/A2: new collateral listing without quorum/delay; observable to monitor that knows declared collateral-onboarding policy. The on-chain action looks like an authorized admin call (Ω_chain-unobservable), but the declared listing process requires multi-stage review (Ω_config-observable)."
    ),
    # Mango Markets: oracle manipulation observable in config (TWAP, deviation bounds)
    ("Mango Markets", "2022-10-11"): ObservabilityProfile(
        min_observable_omega=Omega.CONFIG,
        rationale="A5: oracle deviation beyond declared bounds"
    ),

    # === Intent-level: require Ω_intent ===
    # Resolv: signer compromised; the malicious mint looks legit on-chain
    # but the signer's INTENT didn't include this. Requires intent-aware
    # monitoring (e.g., session-keys with declared spending policy).
    ("Resolv Labs", "2026-03-01"): ObservabilityProfile(
        min_observable_omega=Omega.INTENT,
        rationale="A1: unbacked mint. Observable to an intent-aware monitor "
                  "with declared session-policy on minting authority. On-chain "
                  "alone, the mint authority was valid; the discrepancy is in "
                  "the signer's intended scope."
    ),
    ("Step Finance", "2026-01-31"): ObservabilityProfile(
        min_observable_omega=Omega.INTENT,
        rationale="A2: stolen multisig key; the on-chain transfer was authorized. "
                  "Observable to a monitor with declared transfer-frequency/destination "
                  "policy (intent layer)."
    ),

    # === Infra-level: TRUE basis-unobservable (cannot be helped by any monitor) ===
    ("CoW Swap", "2026-04-14"): ObservabilityProfile(
        min_observable_omega=Omega.INFRA,
        is_basis_observable_under_any=False,
        rationale="DNS hijack; victim signs legitimately. Monitor cannot distinguish "
                  "intended vs. tricked transactions even at Ω_infra without breaking "
                  "trust-base assumptions about DNS itself."
    ),
    ("Ronin Bridge", "2022-03-23"): ObservabilityProfile(
        min_observable_omega=Omega.CONFIG,
        rationale="5-of-9 validator quorum compromised; observable as 1-of-N rather "
                  "than k-diverse-of-N at config layer."
    ),

    # ... (sketch; full mapping is in the catalog CSV)
}


def get_observability(protocol: str, date: str, basis_observable_field: str) -> ObservabilityProfile:
    """Get the observability profile for a catalog entry.
    
    Uses CATALOG_OBSERVABILITY where explicit; otherwise infers from the
    catalog's basis_observable field:
      - "yes" → Ω_chain (default for confirmed on-chain code bugs)
      - "no"  → Ω_infra, not basis-observable under any (irreducible)
      - "ambiguous" → Ω_config (config-level required)
    """
    key = (protocol, date)
    if key in CATALOG_OBSERVABILITY:
        return CATALOG_OBSERVABILITY[key]
    if basis_observable_field == "yes":
        return ObservabilityProfile(
            min_observable_omega=Omega.CHAIN,
            rationale="Default: on-chain observable per catalog field"
        )
    if basis_observable_field == "ambiguous":
        return ObservabilityProfile(
            min_observable_omega=Omega.CONFIG,
            rationale="Default for ambiguous: requires config-level observation"
        )
    return ObservabilityProfile(
        min_observable_omega=Omega.INFRA,
        is_basis_observable_under_any=False,
        rationale="Default for basis-unobservable: irreducible"
    )


def summarize_by_omega() -> dict:
    """Aggregate loss by minimum required observation set."""
    from parallax.formal.exploit_catalog import CATALOG
    by_omega = {o: {"count": 0, "loss_usd": 0.0} for o in Omega}
    irreducible = {"count": 0, "loss_usd": 0.0}
    classified = 0
    for entry in CATALOG:
        profile = get_observability(entry.protocol, entry.date, entry.basis_observable)
        if profile.is_basis_observable_under_any:
            by_omega[profile.min_observable_omega]["count"] += 1
            by_omega[profile.min_observable_omega]["loss_usd"] += entry.loss_usd
        else:
            irreducible["count"] += 1
            irreducible["loss_usd"] += entry.loss_usd
        classified += 1
    return {
        "classified": classified,
        "by_min_omega": by_omega,
        "irreducible_at_infra": irreducible,
    }


def render() -> str:
    s = summarize_by_omega()
    lines = []
    lines.append("PARALLAX-5 Observation-Set-Parameterized Basis-Observability")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"  Classified entries: {s['classified']}")
    lines.append("")
    lines.append("  Minimum observation set required for basis-observability:")
    for omega in Omega:
        d = s["by_min_omega"][omega]
        lines.append(f"    {omega.value:<8s}  {d['count']:>3d} entries  ${d['loss_usd']/1e6:>9,.1f}M")
    lines.append("")
    lines.append("  Truly irreducible (Ω_infra-unobservable):")
    d = s["irreducible_at_infra"]
    lines.append(f"    infra-   {d['count']:>3d} entries  ${d['loss_usd']/1e6:>9,.1f}M")
    lines.append("")
    lines.append("  Implication: a monitor with observation set Ω is sound w.r.t.")
    lines.append("  basis-observability iff Ω contains the minimum required set.")
    lines.append("  Most off-chain-rooted incidents are Ω_config or Ω_intent")
    lines.append("  observable — NOT outside-the-basis. CoW Swap-style DNS hijacks")
    lines.append("  are genuinely irreducible (cannot be helped by any monitor).")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
