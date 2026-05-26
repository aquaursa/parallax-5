"""
Tool runner: executes each integrated analysis tool against a contract
and parses its output into the normalized Finding model.

Each tool has its own subprocess interface; this module isolates the
quirks (output formats, timeouts, error handling) behind a uniform
`run_tool(name, contract_path) -> List[Finding]` interface.

The runners are designed to fail gracefully: if a tool is not
installed or times out, the runner records an empty findings list and
a diagnostic note in the run report rather than aborting the entire
analysis.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Callable
import subprocess
import json
import pathlib
import shutil
import time

from .findings import Finding


DEFAULT_TIMEOUT_SEC = 600   # 10 minutes per tool


@dataclass
class RunReport:
    """Result of running a single tool against a single contract."""
    tool_id: str
    contract_path: str
    findings: List[Finding] = field(default_factory=list)
    exit_code: Optional[int] = None
    duration_sec: float = 0.0
    timed_out: bool = False
    tool_available: bool = True
    diagnostic: str = ""


def _which(executable: str) -> Optional[str]:
    """Locate an executable on PATH."""
    return shutil.which(executable)


def run_slither(contract_path: str, timeout: int = DEFAULT_TIMEOUT_SEC) -> RunReport:
    """Run Slither and parse its JSON output into normalized findings."""
    report = RunReport(tool_id="slither", contract_path=contract_path)
    if not _which("slither"):
        report.tool_available = False
        report.diagnostic = "slither executable not found on PATH"
        return report

    t0 = time.time()
    try:
        result = subprocess.run(
            ["slither", contract_path, "--json", "-"],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        report.timed_out = True
        report.duration_sec = time.time() - t0
        report.diagnostic = f"slither timed out after {timeout}s"
        return report
    report.duration_sec = time.time() - t0
    report.exit_code = result.returncode

    # Slither writes JSON to stdout; non-zero exit means findings were detected
    # (this is by design — exit code 1 with findings is normal)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        report.diagnostic = f"failed to parse slither JSON output: {e}; first 200 bytes: {result.stdout[:200]}"
        return report

    if not data.get("success"):
        report.diagnostic = f"slither did not complete cleanly: {data.get('error', 'no error message')}"

    detectors = data.get("results", {}).get("detectors", [])
    for det in detectors:
        check = det.get("check", "unknown")
        impact = det.get("impact", "informational").lower()
        elements = det.get("elements", [])
        loc = ""
        if elements:
            el = elements[0]
            src = el.get("source_mapping", {})
            loc = f"{src.get('filename_short', '?')}:{src.get('lines', ['?'])[0] if src.get('lines') else '?'}"
        report.findings.append(Finding(
            tool_id="slither",
            finding_id=check,
            severity=impact,
            contract=pathlib.Path(contract_path).name,
            location=loc,
            message=det.get("description", "").strip()[:200],
            raw=det,
        ))
    return report


def run_mythril(contract_path: str, timeout: int = DEFAULT_TIMEOUT_SEC) -> RunReport:
    """Run Mythril and parse its JSON output."""
    report = RunReport(tool_id="mythril", contract_path=contract_path)
    if not _which("myth"):
        report.tool_available = False
        report.diagnostic = "myth executable not found on PATH (Mythril)"
        return report
    t0 = time.time()
    try:
        result = subprocess.run(
            ["myth", "analyze", contract_path, "-o", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        report.timed_out = True
        report.duration_sec = time.time() - t0
        report.diagnostic = f"mythril timed out after {timeout}s"
        return report
    report.duration_sec = time.time() - t0
    report.exit_code = result.returncode

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        report.diagnostic = f"mythril JSON parse failed: {e}; output: {result.stdout[:200]}"
        return report

    if not data.get("success"):
        report.diagnostic = data.get("error", "mythril reported failure")

    for issue in data.get("issues", []):
        swc = issue.get("swc-id") or issue.get("swcID") or "unknown"
        # Mythril prefixes with "SWC-"
        finding_id = f"SWC-{swc}" if not str(swc).startswith("SWC") else str(swc)
        report.findings.append(Finding(
            tool_id="mythril",
            finding_id=finding_id,
            severity=issue.get("severity", "").lower(),
            contract=pathlib.Path(contract_path).name,
            location=issue.get("filename") + ":" + str(issue.get("lineno", "?")) if issue.get("filename") else None,
            message=(issue.get("title", "") + " — " + issue.get("description", ""))[:200],
            raw=issue,
        ))
    return report


def run_halmos(contract_path: str, timeout: int = DEFAULT_TIMEOUT_SEC) -> RunReport:
    """Run halmos. Halmos requires a Foundry project structure with
    property functions; this runner expects contract_path to be a
    Foundry project root."""
    report = RunReport(tool_id="halmos", contract_path=contract_path)
    if not _which("halmos"):
        report.tool_available = False
        report.diagnostic = "halmos executable not found on PATH"
        return report
    t0 = time.time()
    try:
        result = subprocess.run(
            ["halmos", "--json-output", "/tmp/halmos.json"],
            cwd=contract_path,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        report.timed_out = True
        report.duration_sec = time.time() - t0
        report.diagnostic = f"halmos timed out after {timeout}s"
        return report
    report.duration_sec = time.time() - t0
    report.exit_code = result.returncode

    halmos_out = pathlib.Path("/tmp/halmos.json")
    if not halmos_out.exists():
        report.diagnostic = "halmos JSON output not produced (no property functions found?)"
        return report
    try:
        data = json.loads(halmos_out.read_text())
    except json.JSONDecodeError as e:
        report.diagnostic = f"halmos JSON parse failed: {e}"
        return report

    # Halmos reports property results; each failed property is a finding
    for prop_name, prop_result in data.items():
        if not isinstance(prop_result, dict):
            continue
        if prop_result.get("status") in ("fail", "FAIL", "counterexample"):
            report.findings.append(Finding(
                tool_id="halmos",
                finding_id="invariant-violated",
                severity="high",
                contract=pathlib.Path(contract_path).name,
                location=prop_name,
                message=f"Property {prop_name} violated; counterexample produced.",
                raw=prop_result,
            ))
    return report


def run_obligationsol(contract_path: str, timeout: int = DEFAULT_TIMEOUT_SEC) -> RunReport:
    """Run ObligationSol via the PARALLAX-5 pipeline CLI."""
    report = RunReport(tool_id="obligationsol", contract_path=contract_path)
    if not _which("parallax-obligationsol"):
        report.tool_available = False
        report.diagnostic = "parallax-obligationsol executable not found on PATH"
        return report
    t0 = time.time()
    try:
        result = subprocess.run(
            ["parallax-obligationsol", "scan", contract_path, "--json"],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        report.timed_out = True
        report.duration_sec = time.time() - t0
        report.diagnostic = f"obligationsol timed out after {timeout}s"
        return report
    report.duration_sec = time.time() - t0
    report.exit_code = result.returncode

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        report.diagnostic = f"obligationsol JSON parse failed: {e}"
        return report

    for sig in data.get("matches", []):
        report.findings.append(Finding(
            tool_id="obligationsol",
            finding_id=sig.get("signature_id", "unknown"),
            severity=sig.get("severity"),
            contract=pathlib.Path(contract_path).name,
            location=sig.get("location"),
            message=sig.get("message"),
            raw=sig,
        ))
    return report


RUNNERS: Dict[str, Callable[[str, int], RunReport]] = {
    "slither":  run_slither,
    "mythril":  run_mythril,
    "halmos":   run_halmos,
    "obligationsol": run_obligationsol,
}


def run_all(contract_path: str, tools: List[str] = None, timeout: int = DEFAULT_TIMEOUT_SEC) -> List[RunReport]:
    """Run the specified tools against the contract; return reports."""
    if tools is None:
        tools = list(RUNNERS.keys())
    reports = []
    for tool in tools:
        runner = RUNNERS.get(tool)
        if runner is None:
            report = RunReport(tool_id=tool, contract_path=contract_path,
                             tool_available=False,
                             diagnostic=f"no runner registered for tool '{tool}'")
        else:
            report = runner(contract_path, timeout)
        reports.append(report)
    return reports


def gather_findings(reports: List[RunReport]) -> List[Finding]:
    """Flatten findings across run reports."""
    return [f for r in reports for f in r.findings]
