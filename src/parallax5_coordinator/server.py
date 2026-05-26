"""
FastAPI service for the PARALLAX-5 Coordinator.

Provides HTTP endpoints for compositional verification:

  POST /v1/certify
        Body: { "contract_source": "...", "tools": ["slither", ...] }
        Returns: full certificate JSON with audit trail

  GET  /v1/capability
        Returns: the current capability matrix

  GET  /v1/mapping
        Returns: TOOL-MAPPING v1.0 (full or filtered by ?tool=)

  GET  /v1/health
        Returns: { "status": "ok", "tools_available": [...] }

This service is the nascent form of the rating service: a protocol can
upload its source and receive a defensible P-level certificate with
audit trail. Production deployments would add authentication,
rate-limiting, and persistence of certificates with append-only
fingerprint logs.
"""
from __future__ import annotations
import logging
import pathlib
import tempfile
from typing import List, Optional
from datetime import datetime, timezone

try:
    from fastapi import FastAPI, HTTPException, Body
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError(
        "FastAPI service requires 'fastapi' and 'pydantic'. "
        "Install with: pip install fastapi uvicorn pydantic"
    )

from .capability import (
    KNOWN_TOOLS, JointCapability, p_level, capability_matrix_table,
    Obligation, Depth,
)
from .findings import load_tool_mapping, map_findings, Finding
from .certifier import certify, explain
from .runner import run_all, gather_findings, RUNNERS, _which


logger = logging.getLogger(__name__)

app = FastAPI(
    title="PARALLAX-5 Coordinator Service",
    description=(
        "Compositional smart-contract verification via the five-obligation "
        "PARALLAX-5 taxonomy. Takes Solidity source, runs the configured "
        "tool stack, produces a defensible P-level certificate with audit "
        "trail."
    ),
    version="1.0.0",
)


# ─── Request / response models ───────────────────────────────────────

class CertifyRequest(BaseModel):
    contract_source: str = Field(..., description="Solidity source code as a single string")
    contract_name: Optional[str] = Field(None, description="Optional contract identifier for the certificate")
    tools: Optional[List[str]] = Field(
        None,
        description=("Tool identifiers to run. Defaults to all available "
                     "tools on the host (currently: slither, mythril, halmos, obligationsol).")
    )
    timeout_per_tool_sec: int = Field(600, description="Per-tool timeout in seconds")


class CertifyResponse(BaseModel):
    certificate: dict
    summary: dict
    explanation: str


class CapabilityResponse(BaseModel):
    matrix: dict
    p_level_table: dict
    table_render: str


class HealthResponse(BaseModel):
    status: str
    tools_available: List[str]
    tools_unavailable: List[str]
    version: str


# ─── Endpoints ───────────────────────────────────────────────────────

@app.get("/v1/health", response_model=HealthResponse, tags=["meta"])
def health():
    """Health check + tool-availability report."""
    available = []
    unavailable = []
    binary_for = {"slither": "slither", "mythril": "myth", "halmos": "halmos",
                  "obligationsol": "parallax-obligationsol"}
    for tool, binary in binary_for.items():
        if _which(binary):
            available.append(tool)
        else:
            unavailable.append(tool)
    return HealthResponse(
        status="ok",
        tools_available=available,
        tools_unavailable=unavailable,
        version="1.0.0",
    )


@app.get("/v1/capability", response_model=CapabilityResponse, tags=["calibration"])
def capability():
    """Return the calibrated capability matrix."""
    matrix = {
        tool_id: {ob.name: int(t.depth(ob)) for ob in Obligation}
        for tool_id, t in KNOWN_TOOLS.items()
    }
    joint = JointCapability(tuple(KNOWN_TOOLS.values()))
    matrix["joint"] = {ob.name: int(joint.depth(ob)) for ob in Obligation}
    p_table = {f"P{i}": int(d) for i, d in [(0, Depth.NONE), (1, Depth.MENTION),
              (2, Depth.STATIC_DETECTOR), (3, Depth.SYMBOLIC_PATH),
              (4, Depth.FORMAL_PROPERTY), (5, Depth.MACHINE_THEOREM)]}
    return CapabilityResponse(
        matrix=matrix, p_level_table=p_table,
        table_render=capability_matrix_table(),
    )


@app.get("/v1/mapping", tags=["calibration"])
def mapping(tool: Optional[str] = None):
    """Return TOOL-MAPPING v1.0, optionally filtered by tool id."""
    m = load_tool_mapping()
    if tool:
        if tool not in m["mappings"]:
            raise HTTPException(404, detail=f"No mapping for tool '{tool}'")
        return {"spec_version": m["spec_version"], "tool": tool, "entries": m["mappings"][tool]}
    return m


@app.post("/v1/certify", response_model=CertifyResponse, tags=["certification"])
def certify_endpoint(req: CertifyRequest = Body(...)):
    """Run the coordinator pipeline against a Solidity source and return
    the resulting P-level certificate with audit trail."""

    # Write source to a temporary file for tool consumption
    with tempfile.NamedTemporaryFile(suffix=".sol", mode="w", delete=False) as f:
        f.write(req.contract_source)
        contract_path = f.name

    try:
        tools = req.tools
        logger.info(f"Running tools {tools or 'all'} against {contract_path}")
        reports = run_all(contract_path, tools, timeout=req.timeout_per_tool_sec)

        findings = gather_findings(reports)
        mapped = map_findings(findings)

        tools_run = [r.tool_id for r in reports if r.tool_available]
        cert = certify(
            contract_id=req.contract_name or pathlib.Path(contract_path).name,
            mapped_findings=mapped,
            tools_run=tools_run,
            notes=f"API-issued certificate at {datetime.now(timezone.utc).isoformat()}",
        )

        summary = {
            "p_level": cert.p_level,
            "fingerprint": cert.fingerprint(),
            "issued_at": cert.issued_at,
            "tools_run": tools_run,
            "findings_count": len(findings),
            "mapped_count": sum(1 for f in mapped if f.is_mapped()),
            "unmapped_count": len(cert.unmapped_findings),
            "gaps_to_next_level": cert.gaps,
        }
        return CertifyResponse(
            certificate=cert.to_json_dict(),
            summary=summary,
            explanation=explain(cert),
        )
    finally:
        try:
            pathlib.Path(contract_path).unlink(missing_ok=True)
        except Exception:
            pass


@app.get("/", tags=["meta"])
def root():
    """Service-level metadata."""
    return {
        "service": "PARALLAX-5 Coordinator",
        "version": "1.0.0",
        "endpoints": [
            "GET  /v1/health",
            "GET  /v1/capability",
            "GET  /v1/mapping",
            "POST /v1/certify",
        ],
        "documentation": "https://parallax.xyz/coordinator",
        "source": "https://github.com/aquaursa-research/parallax5-coordinator",
    }
