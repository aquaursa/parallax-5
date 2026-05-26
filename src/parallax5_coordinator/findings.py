"""
Normalized findings model.

Each tool emits findings in its native format. The coordinator
normalizes these into a uniform `Finding` record so that the
obligation-mapper and certifier can operate over a single schema.

This module is the bridge between TOOL-MAPPING v1.0 (which is a
JSON-encoded knowledge artifact) and the coordinator logic.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Iterable
import json
import pathlib

from .capability import Obligation, Depth


@dataclass(frozen=True)
class Finding:
    """A single finding produced by a single tool on a single contract.

    The `obligation` and `depth` fields are populated by the mapper
    using TOOL-MAPPING v1.0; before mapping they are None.
    """
    tool_id: str
    finding_id: str                  # The tool's native identifier (detector name, SWC code, etc.)
    severity: Optional[str] = None   # Tool's native severity, if available
    contract: Optional[str] = None
    location: Optional[str] = None   # source line / function / instruction
    message: Optional[str] = None    # Human-readable description
    raw: Optional[Dict] = None       # Native tool output, preserved for audit
    # Populated by the mapper:
    obligation: Optional[Obligation] = None
    depth: Optional[Depth] = None
    mapping_justification: Optional[str] = None

    def is_mapped(self) -> bool:
        return self.obligation is not None and self.depth is not None


def load_tool_mapping(path: str = None) -> Dict:
    """Load TOOL-MAPPING v1.0 from disk."""
    if path is None:
        path = str(pathlib.Path(__file__).parent.parent.parent / "schemas" / "tool_mapping_v1.json")
    return json.loads(pathlib.Path(path).read_text())


def map_finding(finding: Finding, tool_mapping: Dict) -> Finding:
    """Apply the TOOL-MAPPING v1.0 lookup to populate obligation + depth.

    Returns a new Finding instance with the obligation, depth, and
    justification fields filled in. Returns the original Finding
    unchanged if no mapping entry exists (caller should track these
    as 'unmapped' for the audit log).
    """
    tool_block = tool_mapping["mappings"].get(finding.tool_id)
    if not tool_block:
        return finding

    for entry in tool_block["entries"]:
        if entry.get("finding_id") == finding.finding_id:
            return Finding(
                tool_id=finding.tool_id,
                finding_id=finding.finding_id,
                severity=finding.severity or entry.get("severity"),
                contract=finding.contract,
                location=finding.location,
                message=finding.message,
                raw=finding.raw,
                obligation=Obligation[entry["obligation"]],
                depth=Depth(entry["depth"]),
                mapping_justification=entry.get("justification"),
            )
    return finding


def map_findings(findings: Iterable[Finding], tool_mapping: Dict = None) -> List[Finding]:
    """Map a batch of findings. Unmapped findings are returned as-is."""
    if tool_mapping is None:
        tool_mapping = load_tool_mapping()
    return [map_finding(f, tool_mapping) for f in findings]


def findings_to_json(findings: Iterable[Finding]) -> List[Dict]:
    """JSON-serializable representation of mapped findings."""
    result = []
    for f in findings:
        d = asdict(f)
        # Enums don't serialize cleanly via asdict
        if f.obligation is not None:
            d["obligation"] = f.obligation.name
        if f.depth is not None:
            d["depth"] = int(f.depth)
        result.append(d)
    return result
