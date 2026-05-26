# Security Policy

## Reporting a vulnerability

Email `security@aquaursa.io` with details. Please do not open a public
issue for vulnerabilities until they have been triaged.

For each report, include:

- the affected component (paper claim, Lean theorem, fire test, Solidity
  contract, Python code, etc.),
- the conditions under which the issue manifests,
- a minimal reproduction or counterexample where possible,
- whether the issue affects only the reference implementation or the
  underlying standard text.

We acknowledge reports within five business days. Disclosure timing is
negotiated case by case.

## Basis counterexample challenge

The Non-Capturability Charter (Article 6) and the paper (§4) define a
falsification challenge: any submission demonstrating a basis-respecting
loss-inducing transition that violates no obligation under the adequacy
hypothesis qualifies. The challenge has its own discovery process and is
documented in `paper/FALSIFICATION_CHALLENGE.md`. Submissions are
structurally validated by `parallax5 challenge validate`.

## Scope

Security-relevant components are:

| Component | Path |
|---|---|
| Lean substrate proofs | `parallax/formal/lean/`, `lean/Parallax5/` |
| EvmYulLean refinement | `parallax/formal/lean/Parallax5_EvmYulLean.lean` |
| Coordinator | `src/parallax5_coordinator/` |
| CLI | `src/parallax5_cli/` |
| Registry contract | `registry/src/ParallaxRegistry.sol` |
| Schema validation | `src/parallax5_coordinator/cli.py` |
| Certificate schema | `schemas/certificate_v1.json` |
| Fire tests | `parallax/formal/fire_tests.py`, `parallax/obligationsol/fire_tests.py` |

Tooling-only concerns (CI configuration, build scripts, documentation
typos) are issues, not security reports.
