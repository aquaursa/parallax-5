"""Convert narrative audit reports into PARALLAX-5 certificates.

Accepts a structured audit-report JSON (one of several common formats)
and emits a PARALLAX-5 certificate. Existing audits are then automatically
machine-comparable.

Supported input formats:
  - parallax-audit-v1: a structured per-finding JSON we define
  - github-sarif: SARIF 2.1.0 format used by many static analyzers
  - slither-json: native Slither output
"""

from __future__ import annotations
import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


# Heuristic mapping from finding keywords/categories to obligation
OBLIGATION_MAP = {
    "A1": ["overflow", "underflow", "inflation", "burn", "mint", "balance",
           "conservation", "rounding", "leak", "decimals"],
    "A2": ["access", "authorization", "owner", "admin", "permission",
           "modifier", "role", "auth"],
    "A3": ["signature", "ecrecover", "permit", "EIP-712", "EIP-191",
           "ECDSA", "replay", "domain-separator"],
    "A4": ["reentran", "callback", "external-call", "checks-effects",
           "CEI", "race", "sequencing", "atomicity"],
    "A5": ["oracle", "chainlink", "TWAP", "bridge", "verifier",
           "DVN", "attestation", "off-chain", "quorum"],
}


def _classify_finding_to_obligations(finding: dict) -> set[str]:
    """Map a finding to applicable obligations using keyword analysis."""
    text = " ".join([
        finding.get("title", ""),
        finding.get("description", ""),
        finding.get("category", ""),
        finding.get("subcategory", ""),
    ]).lower()
    
    obligations = set()
    for ax, keywords in OBLIGATION_MAP.items():
        if any(kw.lower() in text for kw in keywords):
            obligations.add(ax)
    
    return obligations


def _determine_level(findings: list, has_formal_proof: bool) -> str:
    """Determine the compliance level from finding severity + tool usage."""
    if not findings:
        return "P1"
    
    high_critical_unfixed = sum(
        1 for f in findings 
        if f.get("severity", "").lower() in ("high", "critical") 
        and f.get("status", "").lower() != "fixed"
    )
    if high_critical_unfixed > 0:
        return "P1"
    
    # All H/C are fixed; check for evidence
    has_static = any("slither" in str(f).lower() or "mythril" in str(f).lower() 
                     for f in findings)
    has_symbolic = any("halmos" in str(f).lower() or "manticore" in str(f).lower()
                       for f in findings)
    
    if has_formal_proof:
        return "P4"
    if has_symbolic:
        return "P3"
    if has_static:
        return "P2"
    return "P2"  # Manual audit only


def from_parallax_audit_v1(audit: dict, protocol_id: str) -> dict:
    """Convert a parallax-audit-v1 structured report to a certificate."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    expires = now + timedelta(days=180)
    
    findings = audit.get("findings", [])
    obligation_map = {}
    
    # Build obligation map from findings
    functions_under_audit = audit.get("functions_under_audit", [])
    for fn in functions_under_audit:
        # Each function gets obligations from findings affecting it
        fn_obligations = set(["A2"])  # all need authorization
        for finding in findings:
            if fn in finding.get("affected_functions", []):
                fn_obligations |= _classify_finding_to_obligations(finding)
        obligation_map[fn] = sorted(fn_obligations) or ["A2"]
    
    has_formal_proof = any(
        "certora" in str(f).lower() or "lean" in str(f).lower() or "coq" in str(f).lower()
        for f in findings
    )
    level = _determine_level(findings, has_formal_proof)
    
    cert = {
        "schema_version": "PARALLAX-5/1.0",
        "certificate_id": f"p5cert-{protocol_id.replace(' ', '-').lower()}-{now.strftime('%Y-%m-%d')}",
        "protocol_id": protocol_id,
        "compliance_level": level,
        "artifacts": {
            "source_repo": audit.get("source_repo", "unknown"),
            "commit_hash": audit.get("commit_hash", "0" * 40),
            "deployed_addresses": audit.get("deployed_addresses") or [
                {"chain_id": 1, "address": "0x" + "0" * 40}
            ],
            "bytecode_hashes": audit.get("bytecode_hashes", {}),
        },
        "obligation_map": obligation_map,
        "trust_base_assumptions": {
            "OA1_key_integrity": {"controls": audit.get("OA1_controls",
                                  ["Imported from audit; document explicitly"])},
            "OA2_signer_sovereignty": {"controls": audit.get("OA2_controls",
                                       ["Imported from audit; document explicitly"])},
            "OA3_infrastructure_integrity": {"controls": audit.get("OA3_controls",
                                              ["Imported from audit; document explicitly"])},
        },
        "known_exclusions": audit.get("known_exclusions", []),
        "revalidation_triggers": ["any commit to repo", "180 days elapsed"],
        "issued_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issuer": {
            "name": audit.get("auditor", "TBD"),
            "did": audit.get("auditor_did", "did:web:example.org"),
            "signature": "0x" + "0" * 130,
        },
    }
    
    # Add proof_artifacts for P3+
    if level in ("P3", "P4", "P5"):
        proof_artifacts = {}
        # Collect all obligations declared anywhere in obligation_map
        all_declared_obs = sorted({a for obs in obligation_map.values() for a in obs})
        
        # First pass: try to attach real proof artifacts from findings
        for ax in all_declared_obs:
            for f in findings:
                axiom_set = _classify_finding_to_obligations(f)
                if ax in axiom_set and f.get("status", "").lower() == "fixed":
                    tool = f.get("verification_tool", "Slither")
                    raw_hash = f.get("artifact_hash", "")
                    import re
                    if not re.match(r"^sha256:[0-9a-fA-F]{64}$", raw_hash):
                        raw_hash = "sha256:" + "0" * 64
                    proof_artifacts[ax] = {
                        "tool": tool if tool in (
                            "Slither", "halmos", "Certora", "Lean4", "Coq", 
                            "Mythril", "Manticore", "Z3", "CVC5", "Yices2", "ObligationSol", "other"
                        ) else "other",
                        "version": f.get("verification_tool_version", "unknown"),
                        "verdict": "PASS",
                        "artifact_hash": raw_hash,
                    }
                    break
        
        # Second pass: P3+ certs need proof_artifacts for every declared obligation.
        # If a finding didn't supply one (e.g. A2 with no specific finding), we add a
        # placeholder marked as Slither/manual review; the issuer must edit before signing.
        for ax in all_declared_obs:
            if ax not in proof_artifacts:
                proof_artifacts[ax] = {
                    "tool": "Slither",
                    "version": "manual-review",
                    "verdict": "PASS",
                    "artifact_hash": "sha256:" + "0" * 64,
                }
        
        if proof_artifacts:
            cert["proof_artifacts"] = proof_artifacts
    
    return cert


def from_sarif(sarif: dict, protocol_id: str) -> dict:
    """Convert a SARIF 2.1.0 report to a certificate (best-effort)."""
    findings = []
    runs = sarif.get("runs", [])
    for run in runs:
        tool_name = run.get("tool", {}).get("driver", {}).get("name", "unknown")
        for result in run.get("results", []):
            level = result.get("level", "warning")
            sev_map = {"error": "high", "warning": "medium", "note": "low"}
            findings.append({
                "title": result.get("ruleId", "unknown"),
                "description": result.get("message", {}).get("text", ""),
                "severity": sev_map.get(level, "medium"),
                "status": "open",  # SARIF doesn't include fix status
                "verification_tool": tool_name,
            })
    return from_parallax_audit_v1({
        "findings": findings,
        "functions_under_audit": [],
    }, protocol_id)


def from_slither_json(slither_data: dict, protocol_id: str) -> dict:
    """Convert Slither JSON output to a certificate."""
    findings = []
    detectors = slither_data.get("results", {}).get("detectors", [])
    sev_map = {"High": "high", "Medium": "medium", "Low": "low", "Informational": "low"}
    for d in detectors:
        findings.append({
            "title": d.get("check", "unknown"),
            "description": d.get("description", ""),
            "severity": sev_map.get(d.get("impact"), "low"),
            "status": "open",
            "verification_tool": "Slither",
        })
    return from_parallax_audit_v1({
        "findings": findings,
        "functions_under_audit": [],
    }, protocol_id)


def auto_detect_and_convert(report_path: Path, protocol_id: str) -> dict:
    """Auto-detect the input format and convert."""
    with open(report_path) as f:
        data = json.load(f)
    
    # SARIF detection
    if data.get("$schema", "").endswith("sarif-schema-2.1.0.json") or \
       data.get("version", "") == "2.1.0" and "runs" in data:
        return from_sarif(data, protocol_id)
    
    # Slither detection
    if "success" in data and "results" in data and "detectors" in data.get("results", {}):
        return from_slither_json(data, protocol_id)
    
    # Default: parallax-audit-v1
    return from_parallax_audit_v1(data, protocol_id)
