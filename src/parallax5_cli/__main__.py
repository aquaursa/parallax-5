"""parallax5 CLI entrypoint."""
from __future__ import annotations
import json
import sys
import shutil
import subprocess
import os
from pathlib import Path
from importlib import resources
import click


def _schema_path() -> Path:
    return Path(str(resources.files("parallax5_cli") / "resources" / "schema.json"))


def _example_path() -> Path:
    return Path(str(resources.files("parallax5_cli") / "resources" / "example_certificate.json"))


# ──────────────────────────────────────────────────────────────
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="parallax5", prog_name="parallax5")
def cli():
    """PARALLAX-5: unification-layer security interface for smart contracts and AI agents.

    \b
    Quickstart (60 seconds):
        $ pip install parallax5
        $ parallax5 doctor .                    # what level does this repo qualify for?
        $ parallax5 init --level P2 > cert.json # author a baseline certificate
        $ parallax5 validate cert.json          # check it conforms to the standard

    Quickstart (5 minutes):
        $ parallax5 score .                     # run Slither + emit a P2 certificate
        $ parallax5 quote --tvl 1B --level P3   # see what insurance would cost
    """


# ──────────────────────────────────────────────────────────────
@cli.command()
@click.argument("cert", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--schema", type=click.Path(exists=True, path_type=Path), default=None,
              help="Custom schema path (defaults to bundled v1.0 schema)")
@click.option("--strict", is_flag=True, help="Enforce best-practice warnings as errors")
def validate(cert: Path, schema: Path, strict: bool):
    """Validate a PARALLAX-5 certificate against the schema."""
    from parallax5_cli.validator import validate_certificate
    schema = schema or _schema_path()
    rc = validate_certificate(cert, schema, strict)
    sys.exit(rc)


# ──────────────────────────────────────────────────────────────
@cli.command()
@click.option("--level", type=click.Choice(["P0", "P1", "P2", "P3", "P4", "P5"]),
              default="P2", help="Target compliance level")
@click.option("--protocol", default="my-protocol", help="Protocol identifier")
@click.option("--non-interactive", is_flag=True, help="Skip the wizard, emit baseline")
def init(level: str, protocol: str, non_interactive: bool):
    """Wizard to author a new PARALLAX-5 certificate (output to stdout)."""
    from datetime import datetime, timedelta
    now = datetime.utcnow().replace(microsecond=0)
    base = json.loads(_example_path().read_text())

    # Customize
    base["compliance_level"] = level
    base["certificate_id"] = f"p5cert-{protocol.replace(' ', '-')}-{now.strftime('%Y-%m-%d')}"
    base["protocol_id"] = protocol
    base["issued_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    base["expires_at"] = (now + timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ")
    base["issuer"]["name"] = "TBD"
    base["issuer"]["did"] = "did:web:example.org"
    base["issuer"]["signature"] = "0x" + "0" * 130

    # If not P3+, drop proof_artifacts
    if level in {"P0", "P1", "P2"}:
        base.pop("proof_artifacts", None)
    # If not P5, drop runtime_gate
    if level != "P5":
        base.pop("runtime_gate", None)
    elif level == "P5" and "runtime_gate" not in base:
        base["runtime_gate"] = {
            "address": "0x" + "0" * 40,
            "configuration_hash": "sha256:" + "0" * 64,
        }
    # If P0, no obligation_map required
    if level == "P0":
        base["obligation_map"] = {}

    if non_interactive:
        click.echo(json.dumps(base, indent=2))
        return

    # Interactive mode: prompt for key fields
    base["protocol_id"] = click.prompt("Protocol name", default=base["protocol_id"])
    base["artifacts"]["source_repo"] = click.prompt(
        "Source repo (GitHub URL)", default="github.com/example/example"
    )
    base["artifacts"]["commit_hash"] = click.prompt(
        "Commit hash (40 hex)", default="0" * 40
    )
    # Functions to map
    if level != "P0":
        fns = click.prompt(
            "Value-affecting functions (comma-separated)",
            default="deposit(uint256,address),withdraw(uint256,address,address)",
        )
        obligation_map = {}
        for f in [x.strip() for x in fns.split(",") if x.strip()]:
            obs = click.prompt(
                f"  Obligations for {f} (subset of A1,A2,A3,A4,A5)", default="A1,A2,A4"
            )
            obligation_map[f] = [x.strip() for x in obs.split(",") if x.strip()]
        base["obligation_map"] = obligation_map

    click.echo(json.dumps(base, indent=2))


# ──────────────────────────────────────────────────────────────
@cli.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--protocol", default=None, help="Protocol name (defaults to repo basename)")
@click.option("--write", type=click.Path(path_type=Path), default=None,
              help="Write output to file instead of stdout")
def score(path: Path, protocol: str, write: Path):
    """Auto-issue a PARALLAX-5 certificate by running available tools.

    Detects and invokes (best-effort):
      - Slither   → P2 certificate from static detectors
      - halmos    → P3 certificate from symbolic execution

    Falls back gracefully if tools aren't installed.
    """
    from parallax5_cli.scorer import score_repo
    cert = score_repo(path, protocol=protocol or path.name)
    out = json.dumps(cert, indent=2)
    if write:
        write.write_text(out)
        click.echo(f"Certificate written to {write}")
    else:
        click.echo(out)


# ──────────────────────────────────────────────────────────────
def _parse_money(s: str) -> float:
    """Parse $1.5B, 500M, 100k → floats."""
    s = s.strip().upper().replace("$", "").replace(",", "")
    multiplier = 1.0
    if s.endswith("K"):
        multiplier, s = 1e3, s[:-1]
    elif s.endswith("M"):
        multiplier, s = 1e6, s[:-1]
    elif s.endswith("B"):
        multiplier, s = 1e9, s[:-1]
    elif s.endswith("T"):
        multiplier, s = 1e12, s[:-1]
    return float(s) * multiplier


@cli.command()
@click.option("--tvl", required=True, help="Protocol TVL, e.g. 1.5B, 500M, 100K")
@click.option("--level", type=click.Choice(["P0", "P1", "P2", "P3", "P4", "P5"]),
              required=True)
@click.option("--eps", default=0.005, type=float, help="Monitor false-negative rate")
@click.option("--loss-ratio", default=0.65, type=float, help="Target loss ratio")
@click.option("--history", default=0, type=int, help="Prior incident count")
def quote(tvl: str, level: str, eps: float, loss_ratio: float, history: int):
    """Quote an insurance premium for a protocol at a compliance level."""
    from parallax5_cli.economics import quote_premium
    tvl_usd = _parse_money(tvl)
    q = quote_premium(tvl=tvl_usd, level=level, eps=eps,
                      target_loss_ratio=loss_ratio,
                      historical_incidents=history)
    bps = (q["premium_usd"] / tvl_usd) * 10_000
    click.echo("")
    click.echo(f"  Protocol TVL:           ${tvl_usd/1e6:>12,.2f}M")
    click.echo(f"  Compliance level:        {level:>12s}")
    click.echo(f"  Monitor FN rate (ε):     {eps:>12.4f}")
    click.echo(f"  Coverage at this level:  {q['coverage']*100:>11.0f}%")
    click.echo(f"  Expected annual loss:   ${q['expected_loss_usd']/1e6:>12,.2f}M")
    click.echo(f"  Suggested annual premium: ${q['premium_usd']/1e6:>10,.2f}M  ({bps:.0f} bps)")
    click.echo("")
    click.echo("  Breakdown:")
    for k, v in q["breakdown"].items():
        if k.startswith("L_"):
            click.echo(f"    {k:<30s} ${v/1e6:>10,.2f}M")
    click.echo("")


# ──────────────────────────────────────────────────────────────
@cli.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
def doctor(path: Path):
    """Diagnose what compliance level a repo qualifies for today.

    Inspects: which tools are installed, what artifacts exist in the
    repo, what trust-base controls are documented. Outputs a verdict
    plus a checklist of what to add to climb the next level.
    """
    from parallax5_cli.doctor import diagnose
    rep = diagnose(path)
    click.echo("")
    click.echo(f"  Repo:                       {path}")
    click.echo(f"  Estimated level today:      {rep['estimated_level']}")
    click.echo(f"  Solidity files found:       {rep['solidity_files']}")
    click.echo("")
    click.echo("  Tools available:")
    for tool, ok in rep["tools"].items():
        mark = "✓" if ok else "✗"
        click.echo(f"    {mark} {tool}")
    click.echo("")
    if rep["next_steps"]:
        click.echo(f"  To reach {rep['next_level']}:")
        for s in rep["next_steps"]:
            click.echo(f"    • {s}")
    click.echo("")


# ──────────────────────────────────────────────────────────────
@cli.command()
def schema():
    """Print the PARALLAX-5 certificate JSON Schema."""
    click.echo(_schema_path().read_text())


@cli.command()
def example():
    """Print an example PARALLAX-5 certificate."""
    click.echo(_example_path().read_text())


@cli.command()
@click.option("--year", type=int, help="Filter by year")
@click.option("--axiom", help="Filter by axiom (e.g., A1, A2)")
@click.option("--min-loss", default=0.0, type=float, help="Minimum loss in USD")
@click.option("--basis", type=click.Choice(["observable", "unobservable", "ambiguous"]),
              help="Filter by basis observability")
def catalog(year: int, axiom: str, min_loss: float, basis: str):
    """Browse the 53-incident empirical catalog."""
    from parallax5_cli.catalog import load_catalog
    entries = load_catalog()
    total_n = len(entries)
    if year:
        entries = [e for e in entries if e["date"].startswith(str(year))]
    if axiom:
        entries = [e for e in entries if axiom in e["axiom_signature"]]
    if min_loss:
        entries = [e for e in entries if e["loss_usd"] >= min_loss]
    if basis:
        entries = [e for e in entries if e["basis_observable"] == basis]
    entries.sort(key=lambda e: -e["loss_usd"])
    total_loss = sum(e["loss_usd"] for e in entries)
    click.echo("")
    click.echo(f"  {len(entries)} of {total_n} incidents  (${total_loss/1e6:,.0f}M total)")
    click.echo("")
    click.echo(f"  {'Protocol':<30s} {'Date':<10s} {'$M':>8s} {'σ(t)':<14s} {'basis':<12s}")
    click.echo("  " + "─" * 76)
    for e in entries[:50]:
        click.echo(f"  {e['protocol'][:28]:<30s} {e['date'][:10]:<10s} "
                   f"{e['loss_usd']/1e6:>8.1f} {e['axiom_signature'][:14]:<14s} "
                   f"{e['basis_observable']:<12s}")
    click.echo("")


if __name__ == "__main__":
    cli()


# ──────────────────────────────────────────────────────────────
@cli.command(name="audit-import")
@click.argument("audit_report", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--protocol", required=True, help="Protocol identifier")
@click.option("--write", type=click.Path(path_type=Path), default=None,
              help="Write output to file instead of stdout")
def audit_import(audit_report: Path, protocol: str, write: Path):
    """Convert a narrative audit report into a PARALLAX-5 certificate.
    
    Supported input formats:
      - parallax-audit-v1: structured per-finding JSON
      - SARIF 2.1.0: GitHub-compatible static analyzer output
      - Slither native JSON
    
    The conversion is best-effort: edit the resulting certificate to add
    issuer details, signatures, and trust-base assumptions before validation.
    """
    from parallax5_cli.audit_import import auto_detect_and_convert
    cert = auto_detect_and_convert(audit_report, protocol)
    out = json.dumps(cert, indent=2)
    if write:
        write.write_text(out)
        click.echo(f"Certificate written to {write}")
    else:
        click.echo(out)


# ──────────────────────────────────────────────────────────────
