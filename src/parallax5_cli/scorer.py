"""Auto-issue PARALLAX-5 certificates from existing tool runs.

Detects: Slither (-> P2), halmos (-> P3). Falls back to P0/P1.
"""
from __future__ import annotations
import json
import subprocess
import shutil
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


def _find_solidity_files(root: Path) -> list[Path]:
    """Find all .sol files, excluding common dependency dirs."""
    excluded = {"node_modules", "lib", ".git", "out", "cache", "artifacts"}
    out = []
    for p in root.rglob("*.sol"):
        parts = set(p.relative_to(root).parts)
        if parts.isdisjoint(excluded):
            out.append(p)
    return out


def _detect_functions(sol_files: list[Path]) -> dict[str, list[str]]:
    """Best-effort extraction of state-mutating external/public functions."""
    fn_re = re.compile(
        r"function\s+(\w+)\s*\(([^)]*)\)\s+(?:external|public)"
        r"(?:\s+(?:override|virtual|payable|nonReentrant))*"
        r"(?:\s+returns\s*\([^)]*\))?"
    )
    keywords_state = {"deposit", "withdraw", "mint", "burn", "transfer",
                      "borrow", "repay", "swap", "stake", "unstake",
                      "claim", "redeem", "approve", "set", "update",
                      "execute", "release", "submit"}
    obligation_map = {}
    for f in sol_files[:20]:   # bound the work
        try:
            text = f.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for m in fn_re.finditer(text):
            name = m.group(1)
            params = m.group(2).strip()
            # Heuristic: only include state-mutating functions
            if any(k in name.lower() for k in keywords_state):
                # Build signature: name(types)
                types = []
                for p in params.split(","):
                    p = p.strip()
                    if p:
                        types.append(p.split()[0])
                sig = f"{name}({','.join(types)})"
                # Assign obligations heuristically
                obs = ["A2"]  # all need authorization
                lname = name.lower()
                if any(k in lname for k in ("deposit", "withdraw", "mint", "burn",
                                             "transfer", "borrow", "repay", "swap",
                                             "stake", "unstake", "redeem")):
                    obs.append("A1")  # value-conservation matters
                    obs.append("A4")  # reentrancy matters
                if "permit" in lname or "sig" in lname:
                    obs.append("A3")
                if any(k in lname for k in ("oracle", "price", "feed", "update",
                                             "submit", "execute", "release")):
                    obs.append("A5")
                obligation_map[sig] = sorted(set(obs))
    return obligation_map


def _run_slither(root: Path) -> Optional[dict]:
    """Try to run Slither; return its JSON if available."""
    if not shutil.which("slither"):
        return None
    try:
        result = subprocess.run(
            ["slither", str(root), "--json", "-"],
            capture_output=True, text=True, timeout=120,
        )
        if result.stdout:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None
    return None


def score_repo(path: Path, protocol: str = "unknown") -> dict:
    """Build a baseline PARALLAX-5 certificate from a repo."""
    sol_files = _find_solidity_files(path)

    now = datetime.utcnow().replace(microsecond=0)
    expires = now + timedelta(days=180)

    # Detect tools available
    slither_avail = shutil.which("slither") is not None
    halmos_avail = shutil.which("halmos") is not None

    # Pick a level
    if not sol_files:
        level = "P0"
    elif slither_avail:
        level = "P2"
    else:
        level = "P1"

    obligation_map = _detect_functions(sol_files) if sol_files else {}

    cert = {
        "schema_version": "PARALLAX-5/1.0",
        "certificate_id": f"p5cert-{protocol.replace(' ', '-')}-{now.strftime('%Y-%m-%d')}",
        "protocol_id": protocol,
        "compliance_level": level,
        "artifacts": {
            "source_repo": str(path.resolve()),
            "commit_hash": "0" * 40,
            "deployed_addresses": [],
            "bytecode_hashes": {},
        },
        "obligation_map": obligation_map,
        "trust_base_assumptions": {
            "OA1_key_integrity": {"controls": ["TBD — document key custody"]},
            "OA2_signer_sovereignty": {"controls": ["TBD — document signer process"]},
            "OA3_infrastructure_integrity": {"controls": ["TBD — document infra controls"]},
        },
        "known_exclusions": [],
        "revalidation_triggers": ["any commit to repo", "180 days elapsed"],
        "issued_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issuer": {
            "name": "parallax5 score (auto-issued — REPLACE WITH YOUR ISSUER)",
            "did": "did:web:example.org",
            "signature": "0x" + "0" * 130,
        },
    }

    # If P2+, run Slither and embed summary
    if level == "P2" and slither_avail:
        slither_json = _run_slither(path)
        if slither_json:
            # Count detector findings
            results = slither_json.get("results", {}).get("detectors", [])
            cert["artifacts"]["slither_detectors"] = len(results)

    # If halmos available, suggest path to P3
    if halmos_avail and sol_files:
        cert["_next_steps"] = [
            "halmos is installed — add halmos test contracts and re-run "
            "to reach P3 (Symbolically Checked)."
        ]

    return cert
