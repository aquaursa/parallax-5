"""
Command-line interface for the PARALLAX-5 Coordinator.

Subcommands:
    parallax5 analyze CONTRACT [--tools ...] [--output FILE]
    parallax5 validate CERTIFICATE.json [--schema SCHEMA]
    parallax5 certify SPEC.yaml [--output FILE]
    parallax5 registry submit CERTIFICATE.json [--dry-run]
    parallax5 capability
    parallax5 mapping [--tool TOOL]
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import sys
import uuid
from datetime import datetime, timezone, timedelta

from .capability import capability_matrix_table, KNOWN_TOOLS, JointCapability, p_level
from .findings import map_findings, load_tool_mapping
from .certifier import certify, explain
from .runner import run_all, gather_findings
from .crops import (CROPSDimension, WalkawayClass, compute_crops_vector)
from .capability import Depth


SCHEMA_PATH_DEFAULT = pathlib.Path(__file__).parent.parent.parent / "schemas" / "certificate_v1.json"


def cmd_capability(args):
    print(capability_matrix_table())


def cmd_mapping(args):
    mapping = load_tool_mapping()
    print(f"TOOL-MAPPING v{mapping['spec_version']}")
    print()
    for tool, info in mapping["mappings"].items():
        if args.tool and tool != args.tool:
            continue
        print(f"Tool: {tool} (version pin: {info.get('version_pin', 'n/a')})")
        for entry in info["entries"]:
            fid = entry.get("finding_id") or entry.get("name", "?")
            print(f"  {fid:<35s}  → {entry['obligation']} @ depth {entry['depth']}")
        print()


def cmd_analyze(args):
    tools = [t.strip() for t in args.tools.split(",")] if args.tools else None
    if args.simulate:
        print(f"[SIMULATION MODE — loading findings from {args.simulate}]")
        from .findings import Finding
        data = json.loads(pathlib.Path(args.simulate).read_text())
        findings = [Finding(**f) for f in data["findings"]]
        tools_run = data.get("tools_run", ["simulated"])
    else:
        print(f"[Running tools: {tools or 'all four'}]")
        reports = run_all(args.contract, tools)
        for r in reports:
            status = "OK" if r.tool_available and r.exit_code is not None else "SKIP"
            print(f"  {r.tool_id:<10s} [{status}]  {len(r.findings)} findings  ({r.duration_sec:.1f}s)" +
                  (f"  — {r.diagnostic}" if r.diagnostic else ""))
        findings = gather_findings(reports)
        tools_run = [r.tool_id for r in reports if r.tool_available]
        print()
    print(f"Mapping {len(findings)} finding(s) through TOOL-MAPPING v1.0...")
    mapped = map_findings(findings)
    cert = certify(contract_id=args.contract, mapped_findings=mapped, tools_run=tools_run)
    print()
    print(explain(cert))
    if args.output:
        out_path = pathlib.Path(args.output)
        out_path.write_text(json.dumps(cert.to_json_dict(), indent=2))
        print(f"\nCertificate written to {out_path}")


def cmd_validate(args):
    """Validate a PARALLAX-5 certificate JSON against the v1.0 schema."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("ERROR: jsonschema package required. Install with: pip install jsonschema")
        sys.exit(2)

    cert_path = pathlib.Path(args.certificate)
    if not cert_path.exists():
        print(f"ERROR: certificate file not found: {cert_path}")
        sys.exit(2)
    schema_path = pathlib.Path(args.schema) if args.schema else SCHEMA_PATH_DEFAULT
    if not schema_path.exists():
        print(f"ERROR: schema file not found: {schema_path}")
        sys.exit(2)
    try:
        cert = json.loads(cert_path.read_text())
        schema = json.loads(schema_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}")
        sys.exit(2)

    issues = []
    validator = Draft202012Validator(schema)
    schema_errors = list(validator.iter_errors(cert))
    if schema_errors:
        issues.append(("schema", f"{len(schema_errors)} schema violation(s)"))
        for e in schema_errors[:5]:
            issues.append(("  detail", f"{'.'.join(str(p) for p in e.path)}: {e.message[:120]}"))

    # Fingerprint recomputation
    body = {k: v for k, v in cert.items() if k not in ("fingerprint", "signature")}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    computed_fp = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if computed_fp != cert.get("fingerprint", ""):
        issues.append(("fingerprint", f"mismatch: computed {computed_fp[:24]}..."))

    # Evidence reference resolution
    evidence_ids = {e["evidence_id"] for e in cert.get("evidence", [])}
    for ob_name, ob_data in cert.get("obligation_coverage", {}).items():
        for ref in ob_data.get("evidence_refs", []):
            if ref not in evidence_ids:
                issues.append(("evidence_ref", f"{ob_name} cites unknown evidence: {ref}"))
        if ob_data.get("depth", 0) > 0 and not ob_data.get("evidence_refs"):
            issues.append(("evidence_required", f"{ob_name} claims depth>{0} but no evidence"))

    # Depth consistency
    for ob_name, ob_data in cert.get("obligation_coverage", {}).items():
        obligation_depth = ob_data.get("depth", 0)
        for ref in ob_data.get("evidence_refs", []):
            ev = next((e for e in cert.get("evidence", []) if e["evidence_id"] == ref), None)
            if ev and ev.get("depth_contribution", 0) > obligation_depth:
                issues.append(("depth_inconsistency",
                              f"{ob_name} depth={obligation_depth} but evidence {ref} contributes {ev['depth_contribution']}"))

    # Validity dates
    try:
        valid_from = datetime.fromisoformat(cert["validity"]["valid_from"].replace("Z", "+00:00"))
        valid_until = datetime.fromisoformat(cert["validity"]["valid_until"].replace("Z", "+00:00"))
        if valid_until <= valid_from:
            issues.append(("validity", f"valid_until <= valid_from"))
        if datetime.now(timezone.utc) > valid_until:
            issues.append(("expired", f"certificate expired at {valid_until}"))
    except (KeyError, ValueError) as e:
        issues.append(("validity_parse", f"could not parse validity dates: {e}"))

    print(f"Validating: {cert_path}")
    print(f"Schema:     {schema_path}")
    print(f"Cert ID:    {cert.get('certificate_id', '(missing)')}")
    print(f"Protocol:   {cert.get('protocol', {}).get('name', '(missing)')}")
    print()
    if not issues:
        print("✓ Certificate is structurally valid, fingerprint matches, evidence resolves.")
        cv = cert.get('crops_vector', {})
        print(f"  CROPS vector:  C={cv.get('C',0)} R={cv.get('R',0)} O={cv.get('O',0)} P={cv.get('P',0)} S={cv.get('S',0)}")
        print(f"  Walkaway:      {cert.get('walkaway', {}).get('classification', '(missing)')}")
        sys.exit(0)
    else:
        print(f"✗ {len(issues)} issue(s) found:")
        for category, msg in issues:
            print(f"  [{category}] {msg}")
        sys.exit(1)


def cmd_certify(args):
    """Issue a certificate from a YAML specification."""
    try:
        import yaml
    except ImportError:
        print("ERROR: pyyaml required. Install with: pip install pyyaml")
        sys.exit(2)

    spec_path = pathlib.Path(args.spec)
    if not spec_path.exists():
        print(f"ERROR: spec file not found: {spec_path}")
        sys.exit(2)
    spec = yaml.safe_load(spec_path.read_text())
    issued_at = datetime.now(timezone.utc)

    source_path = pathlib.Path(spec["contract_source"])
    if not source_path.exists():
        print(f"ERROR: contract source not found: {source_path}")
        sys.exit(2)
    source_hash = "sha256:" + hashlib.sha256(source_path.read_bytes()).hexdigest()

    print(f"Running coordinator on {source_path}...")
    tools = spec.get("tools", None)
    reports = run_all(str(source_path), tools)
    for r in reports:
        status = "OK" if r.tool_available and r.exit_code is not None else "SKIP"
        print(f"  {r.tool_id:<10s} [{status}]  {len(r.findings)} findings")
    findings = gather_findings(reports)
    mapped = map_findings(findings)
    tools_run = [r.tool_id for r in reports if r.tool_available]

    obligation_coverage = {f"A{i}": {"depth": 0, "evidence_refs": []} for i in range(1, 6)}
    evidence = []
    for idx, f in enumerate(mapped):
        if not f.is_mapped():
            continue
        ev_id = f"evidence-{idx+1:03d}"
        ob_name = f.obligation.name
        evidence.append({
            "evidence_id": ev_id,
            "tool": f.tool_id,
            "tool_version": "see tool docs",
            "finding_id": f.finding_id,
            "obligation_mapped_to": ob_name,
            "depth_contribution": int(f.depth),
            "justification": (f.mapping_justification or f.message or "(no justification)")[:300]
        })
        obligation_coverage[ob_name]["evidence_refs"].append(ev_id)
        if int(f.depth) > obligation_coverage[ob_name]["depth"]:
            obligation_coverage[ob_name]["depth"] = int(f.depth)

    # Support external evidence from YAML spec (e.g., Lean proofs that
    # the coordinator runner doesn't directly execute).
    for ext in spec.get("external_evidence", []):
        ob = ext["obligation"]
        depth = ext["depth"]
        ev_id = f"evidence-ext-{len(evidence)+1:03d}"
        evidence.append({
            "evidence_id": ev_id,
            "tool": ext.get("tool", "external"),
            "tool_version": ext.get("tool_version", "n/a"),
            "finding_id": ext.get("finding_id", "external_evidence"),
            "obligation_mapped_to": ob,
            "depth_contribution": depth,
            "justification": ext.get("justification", "External evidence declared in spec")[:300],
        })
        obligation_coverage[ob]["evidence_refs"].append(ev_id)
        if depth > obligation_coverage[ob]["depth"]:
            obligation_coverage[ob]["depth"] = depth

    # Compute the CROPS vector via the authoritative crops.py module
    from .capability import Obligation as _Ob
    depth_map = {
        _Ob.A1: Depth(obligation_coverage["A1"]["depth"]),
        _Ob.A2: Depth(obligation_coverage["A2"]["depth"]),
        _Ob.A3: Depth(obligation_coverage["A3"]["depth"]),
        _Ob.A4: Depth(obligation_coverage["A4"]["depth"]),
        _Ob.A5: Depth(obligation_coverage["A5"]["depth"]),
    }
    walkaway_data = spec.get("walkaway", {})
    walkaway_class = None
    wc_str = walkaway_data.get("classification", "").upper()
    if wc_str in ("FULL", "BOUNDED", "PARTIAL", "CENTRALIZED", "FAKE"):
        walkaway_class = WalkawayClass[wc_str]
    source_openness = Depth(spec.get("source_openness_depth", 0))
    privacy_primitives = Depth(spec.get("privacy_primitives_depth", 0))
    _cv = compute_crops_vector(
        depth_map,
        walkaway=walkaway_class,
        source_openness_depth=source_openness,
        privacy_primitives_depth=privacy_primitives,
    )
    crops_vector = _cv.to_dict()

    cert = {
        "schema_version": "parallax5-certificate-v1.0",
        "certificate_id": str(uuid.uuid4()),
        "protocol": spec["protocol"],
        "artifact": {"source_hash": source_hash, **spec.get("artifact", {})},
        "deployment": spec.get("deployment", []),
        "mapping": spec.get("mapping", {
            "namespace": "tool-mapping/aquaursa-v1", "version": "1.0.0",
            "doi": "10.5281/zenodo.20386868"
        }),
        "trust_base": spec.get("trust_base", {
            "ecdsa_euf_cma": True, "evm_yul_lean_refinement": True,
            "assumptions": ["No additional security-interface assumptions disclosed"]
        }),
        "obligation_coverage": obligation_coverage,
        "crops_vector": crops_vector,
        "walkaway": spec.get("walkaway", {
            "classification": "centralized",
            "explanation": "Walkaway classification not specified in spec; defaulting to most conservative.",
            "dependencies_disclosed": []
        }),
        "evidence": evidence,
        "issuer": spec.get("issuer", {
            "name": "Unsigned (CLI issuance)",
            "public_key": "ed25519:" + "0" * 64
        }),
        "issuance": {
            "timestamp": issued_at.isoformat(),
            "issuance_method": "automated_pipeline",
            "human_review": False,
            "notes": "Issued by parallax5 certify subcommand"
        },
        "validity": {
            "valid_from": issued_at.isoformat(),
            "valid_until": (issued_at + timedelta(days=180)).isoformat(),
            "revalidation_triggers": ["contract_upgrade", "compiler_change", "manual"]
        },
        "supersession": None, "revocation": None, "challenges": []
    }

    body = {k: v for k, v in cert.items() if k not in ("fingerprint", "signature")}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    cert["fingerprint"] = fingerprint
    cert["signature"] = hashlib.sha512(("mock_" + fingerprint).encode()).hexdigest()[:128]
    if args.signing_key:
        try:
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            private_key = load_pem_private_key(pathlib.Path(args.signing_key).read_bytes(), password=None)
            cert["signature"] = private_key.sign(bytes.fromhex(fingerprint)).hex()
            print("✓ Signed with provided Ed25519 key")
        except Exception as e:
            print(f"WARNING: signing failed ({e}); using mock signature")

    out_path = pathlib.Path(args.output) if args.output else pathlib.Path("certificate.json")
    out_path.write_text(json.dumps(cert, indent=2))
    print()
    print(f"✓ Certificate issued")
    print(f"  Fingerprint:   {fingerprint}")
    print(f"  Certificate:   {out_path}")
    print(f"  CROPS vector:  C={crops_vector['C']} R={crops_vector['R']} O={crops_vector['O']} P={crops_vector['P']} S={crops_vector['S']}")


def cmd_registry(args):
    cert_path = pathlib.Path(args.certificate)
    if not cert_path.exists():
        print(f"ERROR: certificate not found: {cert_path}")
        sys.exit(2)
    cert = json.loads(cert_path.read_text())
    fp = cert.get("fingerprint", "")
    if not fp:
        print(f"ERROR: certificate has no fingerprint")
        sys.exit(2)
    fp_hex = "0x" + fp if not fp.startswith("0x") else fp

    if args.action == "submit":
        # Build the submission payload for display
        submission = {
            "registry_function": "issue",
            "contract_hash": cert["artifact"].get("source_hash", cert["artifact"].get("bytecode_hash", "")),
            "fingerprint": fp_hex,
            "proof_hash": "0x" + hashlib.sha256(json.dumps(cert["evidence"], sort_keys=True).encode()).hexdigest(),
            "mapping_id": "0x" + hashlib.sha256(cert["mapping"]["namespace"].encode()).hexdigest(),
            "issuer_address": cert["issuer"].get("registry_address", "0x" + "0"*40),
            "network": args.network,
        }
        print("Submission payload:")
        print(json.dumps(submission, indent=2))
        print()

        if not args.broadcast:
            print("✓ Dry run (default) — no on-chain submission attempted.")
            print("  To broadcast: re-run with --broadcast and set PARALLAX5_REGISTRY_KEY.")
            return

        # Live submission path
        import os as _os
        if not _os.environ.get("PARALLAX5_REGISTRY_KEY"):
            print("ERROR: --broadcast requires the PARALLAX5_REGISTRY_KEY env var.")
            print("       Set it to the issuer's signing key. The CLI never persists this value.")
            sys.exit(2)
        try:
            from .registry_client import submit_certificate
        except ImportError as e:
            print(f"ERROR: web3.py / eth-account not installed: {e}")
            print("       Install with: pip install web3 eth-account")
            sys.exit(2)
        receipt = submit_certificate(cert_path, network=args.network, dry_run=False)
        print("✓ On-chain submission confirmed:")
        print(json.dumps(receipt, indent=2, default=str))

    elif args.action == "state":
        # Read current on-chain state
        try:
            from .registry_client import RegistryClient, load_deployment
        except ImportError as e:
            print(f"ERROR: web3.py / eth-account not installed: {e}")
            sys.exit(2)
        deployment = load_deployment(args.network)
        if deployment["address"] == "0x" + "0"*40:
            print(f"ERROR: no deployment recorded for network '{args.network}'.")
            print(f"       Edit registry/deployments.json after deployment.")
            sys.exit(2)
        client = RegistryClient(
            rpc_url=deployment["rpc_url"],
            contract_address=deployment["address"],
            chain_id=deployment.get("chain_id"),
        )
        state = client.get_state(fp_hex)
        print(f"Fingerprint:    {fp_hex}")
        print(f"Network:        {args.network}")
        print(f"Contract:       {deployment['address']}")
        print(f"On-chain state: {state.name} (enum {state.value})")
    else:
        print(f"ERROR: unknown registry action '{args.action}'")
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(prog="parallax5", description="PARALLAX-5 Coordinator: compositional verification substrate")
    sub = parser.add_subparsers(dest="cmd", required=True)
    
    p_cap = sub.add_parser("capability"); p_cap.set_defaults(func=cmd_capability)
    
    p_map = sub.add_parser("mapping")
    p_map.add_argument("--tool"); p_map.set_defaults(func=cmd_mapping)
    
    p_an = sub.add_parser("analyze")
    p_an.add_argument("contract"); p_an.add_argument("--tools"); p_an.add_argument("--output"); p_an.add_argument("--simulate", metavar="JSON")
    p_an.set_defaults(func=cmd_analyze)
    
    p_val = sub.add_parser("validate")
    p_val.add_argument("certificate"); p_val.add_argument("--schema")
    p_val.set_defaults(func=cmd_validate)
    
    p_cert = sub.add_parser("certify")
    p_cert.add_argument("spec"); p_cert.add_argument("--output"); p_cert.add_argument("--signing-key")
    p_cert.set_defaults(func=cmd_certify)
    
    p_reg = sub.add_parser("registry")
    p_reg.add_argument("action", choices=["submit", "state"])
    p_reg.add_argument("certificate")
    p_reg.add_argument("--network", default="sepolia",
                       choices=["anvil", "sepolia", "mainnet"],
                       help="target network (default: sepolia)")
    p_reg.add_argument("--broadcast", action="store_true",
                       help="actually broadcast the transaction (default: dry-run)")
    p_reg.add_argument("--dry-run", action="store_true",
                       help="explicit dry-run (default behavior; included for compatibility)")
    p_reg.set_defaults(func=cmd_registry)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
