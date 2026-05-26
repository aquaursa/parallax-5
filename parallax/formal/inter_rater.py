"""Inter-rater classification agreement harness for the PARALLAX-5 catalog.

External review §6 asks for two independent classifiers and Cohen's κ.
Real human recruitment is required for genuine inter-rater validation,
but this module provides the infrastructure:

  1. A codebook-driven structured classifier (rule-based, deterministic)
  2. A complementary heuristic classifier (different reasoning order)
  3. Cohen's κ computation on the dual classifications
  4. Per-incident disagreement reporting

The two classifiers operate on different evidence: classifier A relies
on the root-cause keyword; classifier B relies on the obligation signature.
Where they agree, the classification is robust to reasoning order.
Where they disagree, we publish the disagreement for human adjudication.

This is NOT a substitute for human inter-rater validation, which the
review correctly identifies as the next external step. It IS a
disciplined sanity check that the codebook is internally applicable.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from parallax.formal.exploit_catalog import CATALOG, ExploitEntry


@dataclass
class Classification:
    """Output of a classifier on one incident."""
    incident_id: str
    basis_observable: str        # "yes" | "ambiguous" | "no"
    root_cause: str              # "on-chain" | "off-chain-key" | etc.
    rationale: str = ""


def classifier_A_by_root_cause(entry: ExploitEntry) -> Classification:
    """Classifier A: starts from the root cause and infers observability.

    Reasoning order:
      1. Is the root on-chain? → likely basis-observable
      2. Off-chain key/signer? → likely ambiguous or basis-observable
                                 (depends on whether the on-chain action
                                 was authorized at chain layer)
      3. Off-chain infrastructure? → likely basis-unobservable unless
                                     bridge/oracle config exposes it
    """
    rc = entry.root_cause_class.lower()
    sig = ",".join(sorted(entry.obligation_violations))

    if "on-chain" in rc and "off-chain" not in rc:
        bo = "yes"
        rationale = "On-chain root → basis-observable by default"
    elif "off-chain-key" in rc or "off-chain-signer" in rc:
        # Authorized on-chain action; depends whether config layer catches it
        if "A5" in sig or "A1" in sig:
            bo = "yes"
            rationale = "Off-chain root with A1/A5 signature → observable at config"
        else:
            bo = "ambiguous"
            rationale = "Off-chain root, A2-only → monitor-design-dependent"
    elif "off-chain-infra" in rc:
        if "A5" in sig:
            bo = "yes"
            rationale = "Bridge/oracle config violation visible at deploy"
        else:
            bo = "no"
            rationale = "Pure infra (DNS, RPC) → outside basis"
    elif "mixed" in rc:
        bo = "ambiguous"
        rationale = "Mixed root → classification depends on dominant root"
    else:
        bo = "ambiguous"
        rationale = "Unrecognized root pattern"

    return Classification(
        incident_id=f"{entry.protocol}|{entry.date}",
        basis_observable=bo,
        root_cause=entry.root_cause_class,
        rationale=rationale,
    )


def classifier_B_by_signature(entry: ExploitEntry) -> Classification:
    """Classifier B: starts from the obligation signature and infers observability.

    Reasoning order:
      1. A1, A2, A4 violations are on-chain detectable in principle → "yes"
      2. A3 violations (signature forgery) are also on-chain detectable
         given a sound verifier → "yes"
      3. A5-only violations may require config-layer monitoring → "yes" if
         config-visible, else "ambiguous"
      4. No obligation signature listed → "no" (no violation = no basis hit)
    """
    sig = entry.obligation_violations
    rc = entry.root_cause_class.lower()

    if not sig:
        return Classification(
            incident_id=f"{entry.protocol}|{entry.date}",
            basis_observable="no",
            root_cause=entry.root_cause_class,
            rationale="No axiom violations → no basis hit"
        )

    has_a1_a2_a4 = bool(sig & {"A1", "A2", "A4"})
    has_a3 = "A3" in sig
    has_a5 = "A5" in sig

    if has_a1_a2_a4 or has_a3:
        # On-chain action with detectable violation
        if "off-chain-infra" in rc and not has_a5:
            bo = "no"
            rationale = "Pure infra root masks the on-chain action"
        else:
            bo = "yes"
            rationale = f"Signature {sorted(sig)} detectable at chain or config layer"
    elif has_a5 and not has_a1_a2_a4:
        # Pure A5: depends on config-visibility
        if "config" in rc or "verifier" in rc or "oracle" in rc:
            bo = "yes"
            rationale = "A5 violation visible at config layer"
        else:
            bo = "ambiguous"
            rationale = "A5 violation; config-visibility unclear"
    else:
        bo = "ambiguous"
        rationale = f"Unrecognized signature {sorted(sig)}"

    return Classification(
        incident_id=f"{entry.protocol}|{entry.date}",
        basis_observable=bo,
        root_cause=entry.root_cause_class,
        rationale=rationale,
    )


def cohen_kappa(labels_A: list, labels_B: list) -> float:
    """Cohen's kappa for two raters.

    κ = (p_o - p_e) / (1 - p_e)
      p_o = observed agreement
      p_e = expected agreement by chance
    """
    assert len(labels_A) == len(labels_B), "rater label lists must align"
    n = len(labels_A)
    if n == 0:
        return 0.0

    # Categories
    categories = set(labels_A) | set(labels_B)

    # Observed agreement
    agreements = sum(1 for a, b in zip(labels_A, labels_B) if a == b)
    p_o = agreements / n

    # Expected agreement by chance: sum over categories of P(A=c) * P(B=c)
    p_e = 0.0
    for c in categories:
        p_a = sum(1 for a in labels_A if a == c) / n
        p_b = sum(1 for b in labels_B if b == c) / n
        p_e += p_a * p_b

    if p_e == 1.0:
        return 1.0  # all same category, perfect agreement

    return (p_o - p_e) / (1.0 - p_e)


def percent_agreement(labels_A: list, labels_B: list) -> float:
    """Simple proportion of agreement."""
    if not labels_A:
        return 0.0
    return sum(1 for a, b in zip(labels_A, labels_B) if a == b) / len(labels_A)


def interpret_kappa(kappa: float) -> str:
    """Landis & Koch (1977) interpretation."""
    if kappa < 0.0: return "poor"
    if kappa < 0.20: return "slight"
    if kappa < 0.40: return "fair"
    if kappa < 0.60: return "moderate"
    if kappa < 0.80: return "substantial"
    return "almost perfect"


def run_inter_rater() -> dict:
    """Run both classifiers on the catalog and report agreement."""
    classifications_A = [classifier_A_by_root_cause(e) for e in CATALOG]
    classifications_B = [classifier_B_by_signature(e) for e in CATALOG]

    labels_A = [c.basis_observable for c in classifications_A]
    labels_B = [c.basis_observable for c in classifications_B]

    # Also pull the catalog's authoritative labels for comparison
    labels_catalog = [e.basis_observable for e in CATALOG]

    # Disagreements between A and B
    disagreements_AB = []
    for ca, cb in zip(classifications_A, classifications_B):
        if ca.basis_observable != cb.basis_observable:
            disagreements_AB.append({
                "incident_id": ca.incident_id,
                "A_says": ca.basis_observable,
                "A_reason": ca.rationale,
                "B_says": cb.basis_observable,
                "B_reason": cb.rationale,
            })

    return {
        "n": len(CATALOG),
        "kappa_A_vs_B": cohen_kappa(labels_A, labels_B),
        "kappa_A_vs_catalog": cohen_kappa(labels_A, labels_catalog),
        "kappa_B_vs_catalog": cohen_kappa(labels_B, labels_catalog),
        "percent_agreement_A_vs_B": percent_agreement(labels_A, labels_B),
        "percent_agreement_A_vs_catalog": percent_agreement(labels_A, labels_catalog),
        "percent_agreement_B_vs_catalog": percent_agreement(labels_B, labels_catalog),
        "disagreements_A_vs_B": disagreements_AB,
        "classifications_A": classifications_A,
        "classifications_B": classifications_B,
    }


def render(result: dict) -> str:
    lines = []
    lines.append("PARALLAX-5 Inter-Rater Agreement (codebook-driven simulation)")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"  n = {result['n']} incidents")
    lines.append("")
    lines.append("  Classifier A: root-cause-first reasoning")
    lines.append("  Classifier B: obligation-signature-first reasoning")
    lines.append("  Catalog:      authoritative labels (the codebook author)")
    lines.append("")
    lines.append("  Cohen's κ:")
    for k, label in [
        ("kappa_A_vs_B", "A vs B (independent reasoning orders)"),
        ("kappa_A_vs_catalog", "A vs catalog"),
        ("kappa_B_vs_catalog", "B vs catalog"),
    ]:
        kappa = result[k]
        agree_key = "percent_" + k.replace("kappa", "agreement")
        pct = result.get(agree_key, 0)
        lines.append(f"    {label:<40s}  κ = {kappa:.3f}  ({interpret_kappa(kappa)})")
    lines.append("")
    lines.append("  Percent agreement:")
    for k, label in [
        ("percent_agreement_A_vs_B", "A vs B"),
        ("percent_agreement_A_vs_catalog", "A vs catalog"),
        ("percent_agreement_B_vs_catalog", "B vs catalog"),
    ]:
        pct = result[k]
        lines.append(f"    {label:<25s}  {pct*100:>5.1f}%")
    lines.append("")
    lines.append(f"  Disagreements (A vs B): {len(result['disagreements_A_vs_B'])}")
    if result['disagreements_A_vs_B']:
        lines.append("")
        lines.append("    Top disagreements (first 10):")
        for d in result['disagreements_A_vs_B'][:10]:
            lines.append(f"      {d['incident_id'][:45]:<45s}  A→{d['A_says']:<10s} B→{d['B_says']}")
    lines.append("")
    lines.append("─" * 72)
    lines.append("Interpretation:")
    lines.append("  • κ between classifiers A and B is a within-codebook reliability check.")
    lines.append("  • κ vs catalog measures how well each automated classifier")
    lines.append("    recovers the author's classifications using only the codebook rules.")
    lines.append("  • For genuine inter-rater validation, recruit independent human")
    lines.append("    classifiers per CLASSIFICATION_CODEBOOK.md; this harness is")
    lines.append("    a defensible internal lower bound, not a substitute.")
    return "\n".join(lines)


if __name__ == "__main__":
    result = run_inter_rater()
    print(render(result))
