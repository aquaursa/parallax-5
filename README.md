# PARALLAX-5

**A five-obligation substrate for smart contracts and AI agents.**

[![CI](https://github.com/aquaursa/parallax-5/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aquaursa/parallax-5/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20402755-blue)](https://doi.org/10.5281/zenodo.20402755)
[![Lean theorems](https://img.shields.io/badge/Lean%20theorems-95-green)](parallax/formal/lean/Parallax5.lean)
[![Sorry count](https://img.shields.io/badge/sorry-0-success)](parallax/formal/lean/Parallax5.lean)
[![Catalog](https://img.shields.io/badge/empirical%20catalog-%245.97B%20across%2053%20incidents-orange)](paper/supplement/catalog.csv)

<table>
  <tr><td><strong>Paper</strong></td>     <td><a href="paper/parallax-5.pdf"><code>paper/parallax-5.pdf</code></a> · <a href="https://doi.org/10.5281/zenodo.20402755">doi:10.5281/zenodo.20402755</a></td></tr>
  <tr><td><strong>Verification artifact</strong></td><td><a href="https://doi.org/10.5281/zenodo.20386868">doi:10.5281/zenodo.20386868</a></td></tr>
  <tr><td><strong>Onchain reference (Sepolia)</strong></td><td><a href="https://sepolia.etherscan.io/address/0x8015A98dF9037Cd79a03B291a6fF3C2841992D5b#code"><code>0x8015A98dF9037Cd79a03B291a6fF3C2841992D5b</code></a></td></tr>
  <tr><td><strong>Version</strong></td>   <td>1.0.1</td></tr>
  <tr><td><strong>Status</strong></td>    <td>All gates green: 2,152 compositional · 129 Python fire tests · 24 Foundry · 47-page paper compiles cleanly</td></tr>
  <tr><td><strong>Verify all claims</strong></td><td><a href="CANONICAL_FACTS.md"><code>CANONICAL_FACTS.md</code></a> — single source of truth, reproducible in 3 min via <a href="RUN_VERIFICATION.sh"><code>./RUN_VERIFICATION.sh</code></a></td></tr>
  <tr><td><strong>Licenses</strong></td>  <td>Paper: CC-BY 4.0 · Standard text: CC0 1.0 · Code: Apache-2.0</td></tr>
</table>

PARALLAX-5 decomposes smart-contract safety into five primitive obligations:

| | Obligation |
|---|---|
| **A₁** | Value Conservation |
| **A₂** | Authorization Closure |
| **A₃** | Signature Integrity |
| **A₄** | Temporal Distinctness |
| **A₅** | External-Attestation Trust Boundary |

Under an explicit security-interface adequacy condition, every trust-base-respecting loss-inducing transition has a non-empty violation signature. The substrate is mechanized in Lean 4 (95 theorems, zero `sorry`), validated against a 53-incident empirical catalog ($5.97 B aggregate losses), and refined to a production EVM semantics via EvmYulLean. See [the paper](paper/parallax-5.pdf) for the full development.

## Repository structure

```
parallax-5/
├── paper/                  Paper (parallax-5.pdf, 47 pages) and supplements
├── docs/                   Standalone specifications:
│                             CHARTER, FORK_PROTOCOL, CERTIFICATE_SCHEMA,
│                             TOOL_MAPPING, REGISTRY, DEPLOY, CROPS_VECTOR,
│                             WALKAWAY_THEOREM, ARTIFACT_MAP
├── schemas/                JSON Schema for the certificate (v1.0)
├── parallax/               The substrate (research code):
│                             formal/  Lean 4 module + Z3 + halmos + 53-incident catalog
│                             obligations/     Five-obligation vocabulary (A₁–A₅)
│                             obligationsol/   Obligation-typed Solidity static checker
│                             economics/       Insurance pricing
│                             product/         Trust-surface server + reports + badges
│                             chronos/, hse/, standard/
├── src/                    Installable Python packages:
│                             parallax5_coordinator/  Coordinator + CLI + theorem framework
│                             parallax5_cli/          Practical CLI (doctor, quote, audit-import, …)
├── registry/               ParallaxRegistry.sol + 24 Foundry tests + Lean state-machine proof
├── lean/                   Lake project for substrate-level theorems
│                             (Compositional, Walkaway, Registry)
├── demos/                  Three worked examples with Lean proofs:
│                             vault (A₁, D4) · bridge (A₃ + A₅) · agent_gate (A₁ + A₂ + D5)
├── case_studies/           Additional case studies
├── examples/               Worked certificate examples
├── notebooks/              EVMYulLean integration verification notebook
├── integrations/           Downstream integrations (GitHub Action)
├── scripts/                CI helpers and tooling
└── tests/                  Test fixtures and Python test suites
```

## Quickstart

```bash
git clone --recursive https://github.com/aquaursa/parallax-5.git
cd parallax-5
pip install -e .
./RUN_VERIFICATION.sh
```

The full verification recipe runs all gates locally. Continuous integration runs the same gates on every push via `.github/workflows/ci.yml`.

## Navigation

- **Read the paper.** [`paper/parallax-5.pdf`](paper/parallax-5.pdf) — the canonical 47-page artifact.
- **Use the substrate.**
  - [`docs/CHARTER.md`](docs/CHARTER.md) — the structurally irrevocable non-capturability commitments.
  - [`docs/FORK_PROTOCOL.md`](docs/FORK_PROTOCOL.md) — how to fork the standard cleanly.
  - [`docs/CERTIFICATE_SCHEMA.md`](docs/CERTIFICATE_SCHEMA.md) — the certificate format specification.
  - [`docs/TOOL_MAPPING.md`](docs/TOOL_MAPPING.md) — the calibration standard mapping security tools to depth levels.
  - [`docs/REGISTRY.md`](docs/REGISTRY.md) — the onchain registry contract reference.
- **Run the demos.** `make demo-all` exercises the three end-to-end worked examples.
- **Validate a certificate.** `parallax5 validate path/to/cert.json` after install.
- **Compose a P-level certificate.** `parallax5-coordinator analyze tests/VulnerableLending.sol --output /tmp/cert.json` produces a defensible certificate from Slither, Mythril, halmos, and ObligationSol output.
- **Contribute.** See [`CONTRIBUTING.md`](CONTRIBUTING.md).
- **Report a vulnerability.** See [`SECURITY.md`](SECURITY.md).

## Citation

```bibtex
@software{parallax5_2026,
  author    = {{AquaUrsa Research}},
  title     = {{PARALLAX-5: A Five-Obligation Substrate for Smart Contracts
                and AI Agents}},
  year      = {2026},
  version   = {1.0.1},
  doi       = {10.5281/zenodo.20402755},
  url       = {https://github.com/aquaursa/parallax-5},
  note      = {Companion verification artifact:
               doi:10.5281/zenodo.20386868}
}
```

The repository also includes a [`CITATION.cff`](CITATION.cff) which the GitHub web UI renders as a "Cite this repository" widget.

## License

PARALLAX-5 is layered by component type per the [Non-Capturability Charter](docs/CHARTER.md):

| Component | License |
|---|---|
| Paper (`paper/parallax-5.{tex,pdf}`) | CC-BY 4.0 — see [`LICENSE-PAPER`](LICENSE-PAPER) |
| Standard text (specification documents, schemas, vocabulary) | CC0 1.0 Universal — see [`LICENSE-CC0`](LICENSE-CC0) |
| Code (Python, Solidity, Lean, scripts) | Apache License 2.0 — see [`LICENSE`](LICENSE) |

The standard vocabulary is structurally unencumbered; the reference implementation preserves attribution. See `docs/CHARTER.md` Article 2 for the full irrevocability commitment, and `docs/FORK_PROTOCOL.md` for the fork procedure.

## Acknowledgments

This substrate builds on EvmYulLean (Nethermind's Lean 4 EVM semantics, Cancun fork), forge-std (Foundry Standard Library, foundry-rs), Mathlib (Lean 4), and the open-source security tool ecosystem (Slither, Mythril, halmos). The certificate registry contract is anchored on Sepolia testnet.
