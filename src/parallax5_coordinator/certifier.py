"""
Certifier: produces a PARALLAX-5 P-level certificate from mapped findings.

Given a set of findings F = {f_1, ..., f_n} (each mapped to an
obligation and a depth), the certifier:

  1. Aggregates findings by obligation
  2. Computes per-obligation joint depth (pointwise max)
  3. Determines the maximum P-level satisfied
  4. Records the audit trail: which findings contributed to which
     obligation at which depth, from which tool

The output is a structured certificate object that can be serialized
to JSON for downstream consumers (insurers, CI workflows, public
records). The certificate is designed to be human-auditable: every
non-zero coverage claim is justified by at least one specific
finding from a specific tool.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Iterable
import hashlib
import json

from .capability import (
    Obligation, Depth, P_LEVEL_REQUIREMENTS, p_level, coverage_gaps,
    JointCapability, ToolCapability,
)
from .findings import Finding, findings_to_json


@dataclass
class ObligationEvidence:
    """Evidence supporting a single obligation's coverage claim."""
    obligation: Obligation
    achieved_depth: Depth
    contributing_findings: List[Finding] = field(default_factory=list)
    contributing_tools: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.achieved_depth == Depth.NONE:
            return f"{self.obligation.name}: depth=0 (no evidence)"
        return (f"{self.obligation.name}: depth={int(self.achieved_depth)} "
                f"from {len(self.contributing_findings)} finding(s) "
                f"across {len(self.contributing_tools)} tool(s)")


@dataclass
class Certificate:
    """A PARALLAX-5 P-level certificate with full audit trail."""
    certificate_version: str
    contract_id: str
    issued_at: str
    tools_run: List[str]
    coverage: Dict[str, ObligationEvidence]
    p_level: int
    gaps: Dict[str, int]                # obligation_name -> missing depth for next P-level
    unmapped_findings: List[Finding] = field(default_factory=list)
    notes: str = ""

    def to_json_dict(self) -> Dict:
        """JSON-serializable representation."""
        return {
            "certificate_version": self.certificate_version,
            "contract_id": self.contract_id,
            "issued_at": self.issued_at,
            "tools_run": self.tools_run,
            "p_level": self.p_level,
            "p_level_meaning": _p_level_description(self.p_level),
            "coverage": {
                ob_name: {
                    "obligation": ob_name,
                    "achieved_depth": int(ev.achieved_depth),
                    "depth_meaning": _depth_description(ev.achieved_depth),
                    "contributing_tools": ev.contributing_tools,
                    "contributing_findings": findings_to_json(ev.contributing_findings),
                }
                for ob_name, ev in self.coverage.items()
            },
            "gaps_to_next_p_level": self.gaps,
            "unmapped_findings": findings_to_json(self.unmapped_findings),
            "notes": self.notes,
            "fingerprint": self.fingerprint(),
        }

    def fingerprint(self) -> str:
        """SHA-256 over a canonical body of the certificate.

        Excludes the fingerprint itself and the timestamp. Stable
        across re-issuance from the same inputs.
        """
        body = {
            "certificate_version": self.certificate_version,
            "contract_id": self.contract_id,
            "tools_run": sorted(self.tools_run),
            "coverage": {
                ob_name: {
                    "achieved_depth": int(ev.achieved_depth),
                    "contributing_tools": sorted(ev.contributing_tools),
                    "contributing_finding_ids": sorted(
                        f.finding_id for f in ev.contributing_findings
                    ),
                }
                for ob_name, ev in sorted(self.coverage.items())
            },
            "p_level": self.p_level,
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _p_level_description(level: int) -> str:
    table = {
        0: "No machine-checked coverage.",
        1: "Mention-grade evidence on all obligations (comments/docs).",
        2: "Static-detector coverage of all five obligations.",
        3: "Symbolic-path or stronger evidence on all obligations.",
        4: "Formal-property checking on all obligations (invariants verified).",
        5: "Machine-checked theorem on all obligations (kernel-accepted).",
    }
    return table.get(level, "unknown")


def _depth_description(d: Depth) -> str:
    table = {
        Depth.NONE: "no coverage",
        Depth.MENTION: "mention-grade",
        Depth.STATIC_DETECTOR: "static detector",
        Depth.SYMBOLIC_PATH: "symbolic-path witness",
        Depth.FORMAL_PROPERTY: "formal property verified",
        Depth.MACHINE_THEOREM: "machine-checked theorem",
    }
    return table.get(d, "unknown")


def certify(
    contract_id: str,
    mapped_findings: Iterable[Finding],
    tools_run: List[str],
    notes: str = "",
) -> Certificate:
    """Build a Certificate from the mapped findings.

    Mapped findings are findings that have been through `map_finding`
    and therefore have populated `obligation` and `depth` fields.
    Unmapped findings (tool emitted a finding type we don't have in
    TOOL-MAPPING v1.0) are preserved separately in the audit trail.
    """
    coverage: Dict[Obligation, ObligationEvidence] = {
        ob: ObligationEvidence(obligation=ob, achieved_depth=Depth.NONE)
        for ob in Obligation
    }
    unmapped: List[Finding] = []

    for f in mapped_findings:
        if not f.is_mapped():
            unmapped.append(f)
            continue
        ev = coverage[f.obligation]
        ev.contributing_findings.append(f)
        if f.tool_id not in ev.contributing_tools:
            ev.contributing_tools.append(f.tool_id)
        if f.depth > ev.achieved_depth:
            ev.achieved_depth = f.depth

    # Joint capability from observed coverage
    joint = _joint_from_coverage({ob: ev.achieved_depth for ob, ev in coverage.items()})
    level = p_level(joint)
    gaps_dict = coverage_gaps(joint, target_level=level + 1) if level < 5 else {}

    return Certificate(
        certificate_version="parallax5-cert-v1.0",
        contract_id=contract_id,
        issued_at=datetime.now(timezone.utc).isoformat(),
        tools_run=sorted(tools_run),
        coverage={ob.name: ev for ob, ev in coverage.items()},
        p_level=level,
        gaps={ob.name: int(d) for ob, d in gaps_dict.items()},
        unmapped_findings=unmapped,
        notes=notes,
    )


def _joint_from_coverage(observed: Dict[Obligation, Depth]) -> JointCapability:
    """Build a JointCapability with a single synthetic tool whose
    capability mirrors the observed coverage. Used to drive the
    p_level and coverage_gaps functions."""
    synthetic = ToolCapability(
        tool_id="observed",
        version="empirical",
        depth_by_obligation=observed,
    )
    return JointCapability((synthetic,))


def explain(cert: Certificate) -> str:
    """Human-readable explanation of the certificate."""
    out = []
    out.append("=" * 72)
    out.append(f"PARALLAX-5 Certificate v{cert.certificate_version}")
    out.append("=" * 72)
    out.append(f"  Contract:      {cert.contract_id}")
    out.append(f"  Issued:        {cert.issued_at}")
    out.append(f"  Tools run:     {', '.join(cert.tools_run)}")
    out.append(f"  P-level:       P{cert.p_level} — {_p_level_description(cert.p_level)}")
    out.append(f"  Fingerprint:   {cert.fingerprint()[:24]}...")
    out.append("")
    out.append("Per-obligation coverage:")
    for ob_name in ("A1", "A2", "A3", "A4", "A5"):
        ev = cert.coverage[ob_name]
        if ev.achieved_depth == Depth.NONE:
            out.append(f"  {ob_name}: depth=0  (NO COVERAGE)")
        else:
            tools_str = ", ".join(ev.contributing_tools)
            out.append(f"  {ob_name}: depth={int(ev.achieved_depth)}  "
                       f"({_depth_description(ev.achieved_depth)})")
            out.append(f"       from: {tools_str}")
            for f in ev.contributing_findings:
                out.append(f"         - {f.tool_id}:{f.finding_id}")
    out.append("")
    if cert.gaps:
        out.append(f"Gaps to reach P{cert.p_level + 1}:")
        for ob_name, missing_depth in cert.gaps.items():
            out.append(f"  {ob_name}: need +{missing_depth} depth")
    else:
        if cert.p_level == 5:
            out.append("Maximum P-level (P5) achieved.")
        else:
            out.append("No gaps below currently-achieved P-level.")
    if cert.unmapped_findings:
        out.append("")
        out.append(f"Unmapped findings ({len(cert.unmapped_findings)}):")
        for f in cert.unmapped_findings[:5]:
            out.append(f"  - {f.tool_id}:{f.finding_id} (no TOOL-MAPPING entry)")
        if len(cert.unmapped_findings) > 5:
            out.append(f"  ... and {len(cert.unmapped_findings) - 5} more")
    out.append("=" * 72)
    return "\n".join(out)
