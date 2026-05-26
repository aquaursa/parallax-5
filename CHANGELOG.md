# Changelog

All notable changes to PARALLAX-5 are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-05-26

First public release. Substrate foundations, three worked examples, paper,
onchain registry, and certificate schema are all in place.

### Added

- **Substrate foundations.** Non-Capturability Charter (CC0, 11 articles,
  structurally irrevocable), Fork Protocol (four fork types, four
  compatibility levels), Certificate Schema v1.0 (19 fields, seven-state
  lifecycle, canonical serialization), Walkaway Theorem mechanization in
  Lean 4, PARALLAX-CROPS trust-surface vector (5×5 matrix + proof-depth
  scale + 19-test suite).
- **Formal core.** Lean 4 module with 95 theorems and zero `sorry`,
  including the conditional completeness theorem, step-secure gate
  semantics with both post-state and transition-obligation checks, and
  the AI-Agent Containment Theorem. EvmYulLean integration via typeclass-
  based refinement (Cancun fork).
- **Empirical catalog.** 53 incidents (2016–2026), aggregate $5.97 B,
  classified by minimum observability set. 134 Python fire tests across
  nine suites; 2,152 compositional theorem checks.
- **Worked examples.** Three end-to-end demos with Lean proofs:
  ERC-4626 inflation attack (A1, depth D4), bridge attestation
  (A3 and A5), and an AI-agent runtime gate (A1 and A2, depth D5
  runtime enforcement).
- **Onchain certificate registry.** Permissionless Solidity 0.8.24
  contract (`ParallaxRegistry`) with seven-state lifecycle and six
  event kinds; Foundry test suite (24 tests, two of which fuzz at
  256 runs); Lean state-machine proof. Live reference deployment on
  Sepolia at `0x8015A98dF9037Cd79a03B291a6fF3C2841992D5b`
  (Etherscan-verified).
- **Paper.** 47-page artifact, mechanically verified, three-pass clean
  compile.
- **Tooling.** Coordinator package (`parallax5-coordinator`), practical
  CLI (`parallax5`) with `doctor`, `quote`, `score`, `audit-import`,
  `validate`, `certify`, and `registry` subcommands. Trust-surface
  product surface (`parallax/product/`) with FastAPI server, HTML
  reports, and SVG badges.
- **Licensing.** Standard text under CC0 1.0; reference implementations
  under Apache-2.0; the paper itself under CC-BY 4.0. Non-capturability
  commitments: no AquaUrsa patent claims over the substrate, no
  trademark on PARALLAX-5, no token, no governance body, fork-friendly
  evolution via the Fork Protocol.

### Verification gates (all green at release)

- 2,152 / 2,152 compositional theorem checks
- 19 / 19 CROPS tests
- 70 / 70 fire tests across nine suites
- 24 / 24 Foundry tests (incl. 2 fuzz @ 256 runs)
- 135 total Lean theorems, 0 `sorry`
- 3 / 3 demos end-to-end

[1.0.0]: https://github.com/aquaursa/parallax-5/releases/tag/v1.0.0
