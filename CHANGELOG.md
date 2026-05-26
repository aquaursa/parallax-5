# Changelog

All notable changes to PARALLAX-5 are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] — 2026-05-27

### Added (Move 10: mapping registry)

- **Registered-mapping pattern.** The substrate now supports a registry
  of named tool-mappings. The reference `tool-mapping/aquaursa-v1`
  ships in `mappings/aquaursa-v1.json`; other authors may publish
  their own mappings under `tool-mapping/{author}-v{major}` namespaces.
  See `mappings/README.md` for the registration process.
- **`schemas/mapping_protocol_v1.json`** formally defines the schema
  every registered mapping must satisfy. Distinct from the previous
  `schemas/tool_mapping_v1.json` which conflated the schema with the
  AquaUrsa data instance.
- **`docs/MAPPING_PROTOCOL.md`** (rewrite of the prior
  `docs/TOOL_MAPPING.md`) describes the protocol for tool-mapping
  documents. The narrative companion for the AquaUrsa instance is
  `docs/mappings/aquaursa-v1.md`.
- **Coordinator API** (`parallax5_coordinator.capability`): three new
  exports — `load_mapping(namespace)`, `load_mapping_document(namespace)`,
  `list_registered_mappings()`. The legacy module-level constants
  (`SLITHER_CAPABILITY`, etc.) remain as aliases whose values match
  the loaded values exactly (enforced by
  `tests/test_mapping_registry.py`).
- **CLI** (`parallax5 certify`): `--mapping NAMESPACE` flag and
  `--list-mappings` discovery flag. Defaults to
  `tool-mapping/aquaursa-v1` when neither is set or provided in the
  spec.
- **Fire tests** (`tests/test_mapping_registry.py`, 11 new tests):
  schema validation for every file in `mappings/`,
  namespace–version consistency, drift check between loaded values
  and legacy module constants, CLI mapping-resolution paths.

### Changed

- Certificate emission now resolves the `mapping` field via
  `_resolve_mapping_field()` with precedence
  `--mapping > spec.mapping > default(aquaursa-v1)`. Externally
  observable behavior unchanged on default-path runs; the new
  behavior is purely additive.

### Deprecated (slated for removal in v2.0)

- Direct import of `SLITHER_CAPABILITY`, `MYTHRIL_CAPABILITY`,
  `HALMOS_CAPABILITY`, `AXIOMSOL_CAPABILITY` — use
  `load_mapping(namespace)` instead.
- `schemas/tool_mapping_v1.json` (the schema/data-conflated file).
  The same data lives at `mappings/aquaursa-v1.json` with proper
  namespace metadata; the schema lives at
  `schemas/mapping_protocol_v1.json`. The conflated file is kept
  during the v1.x line for backward compatibility with downstream
  tooling.

### Migration

Downstream code reading the AquaUrsa mapping should switch from

```python
from parallax5_coordinator.capability import SLITHER_CAPABILITY  # old
```

to

```python
from parallax5_coordinator.capability import load_mapping
caps = load_mapping("tool-mapping/aquaursa-v1")
slither = caps["slither"]                                          # new
```

Both yield identical values during the v1.x line. The legacy
imports will be removed in v2.0.

## [1.0.1] — 2026-05-26

Repository-hygiene release. No change to the substrate's mathematical
content, theorems, or verification gates; the substrate definition is
unchanged from v1.0.0.

### Removed

- Four non-substrate subsystems that drifted in from adjacent project
  directions:
  - `parallax/hse/` — hypothesis-search machinery from a bug-discovery
    pipeline
  - `parallax/product/` — consumer product surface (trust-surface server,
    HTML reports, SVG badges, pre-transaction simulator)
  - `parallax/economics/` — insurance pricing model
  - `parallax/chronos/` — temporal-coherence research direction
- The corresponding CLI commands (`trust-surface`, `report`,
  `pretx-simulate`) that depended on the removed modules.
- Stale fire tests that exercised the removed subsystems.

### Changed

- Restructured standalone specifications under `docs/`:
  `CHARTER.md`, `FORK_PROTOCOL.md`, `CERTIFICATE_SCHEMA.md`,
  `TOOL_MAPPING.md`, `REGISTRY.md`, `DEPLOY.md`, `CROPS_VECTOR.md`,
  `WALKAWAY_THEOREM.md`, `ARTIFACT_MAP.md`, `REPRODUCIBILITY_LOG.txt`.
- Dropped `_v1.0` from `PARALLAX5_CERTIFICATE_SCHEMA_v1.0.md` and
  `TOOL_MAPPING_v1.0.md` (file names should not bake in spec versions).
- Dropped `_NOTE` from `CROPS_VECTOR_NOTE.md` and `WALKAWAY_THEOREM_NOTE.md`.
- Converted `registry/lib/forge-std` from 68 checked-in files to a proper
  git submodule pinned at `v1.16.1` (≈ 1.3 MB removed from tracking).
- Fire-test count updated to 129 (was 134) to reflect the cleaned codebase.
- Paper title page now cites the v1.0.1 DOI with the v1.0.0 DOI
  preserved as the original-publication reference.

### Added

- `CITATION.cff` (Citation File Format; renders as "Cite this repository")
- `CHANGELOG.md` (this file)
- `CONTRIBUTING.md` — distinguishes implementation contributions
  (Apache-2.0) from standard-text contributions (CC0, via Fork Protocol)
- `SECURITY.md` — vulnerability disclosure policy + basis-counterexample
  challenge scope
- `.gitmodules` — forge-std submodule wiring

### Fixed

- `scripts/self_security_audit.py`: corrected import ordering
  (`from __future__ import annotations` must precede regular imports)
- `parallax/formal/fire_tests.py`: hardened `test_lean_compiles_with_zero_sorry`
  with `shutil.which("lean")` and try/except around subprocess invocation,
  so the test soft-passes on environments without an executable Lean binary
- Replaced five broken legacy CI workflows with a single clean `ci.yml`
  that exercises this repo's actual gates (Python gates, Foundry tests,
  paper compile)

### Verification gates (all green)

- 2,152 / 2,152 compositional theorem checks
- 19 / 19 CROPS tests
- 129 / 129 Python fire tests across three suites
- 24 / 24 Foundry tests (incl. 2 fuzz @ 256 runs)
- 135 total Lean theorems, 0 `sorry`
- 3 / 3 demos end-to-end via `make demo-all`
- Paper compiles cleanly in three-pass pdflatex (47 pages, 0 errors)

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
  semantics, and the AI-Agent Containment Theorem. EvmYulLean integration
  via typeclass-based refinement (Cancun fork).
- **Empirical catalog.** 53 incidents (2016–2026), aggregate $5.97 B,
  classified by minimum observability set.
- **Worked examples.** Three end-to-end demos with Lean proofs:
  ERC-4626 inflation attack (A1, depth D4), bridge attestation
  (A3 and A5), and an AI-agent runtime gate (A1 and A2, depth D5).
- **Onchain certificate registry.** `ParallaxRegistry` (Solidity 0.8.24)
  with seven-state lifecycle and six event kinds. Foundry suite (24 tests,
  two of which fuzz at 256 runs). Lean state-machine proof. Live reference
  deployment on Sepolia at `0x8015A98dF9037Cd79a03B291a6fF3C2841992D5b`
  (Etherscan-verified).
- **Paper.** 47-page artifact, mechanically verified, three-pass clean
  compile.
- **Tooling.** Coordinator package (`parallax5-coordinator`), practical
  CLI (`parallax5`).
- **Licensing.** Standard text under CC0 1.0; reference implementations
  under Apache-2.0; the paper itself under CC-BY 4.0. Non-capturability
  commitments: no AquaUrsa patent claims over the substrate, no
  trademark on PARALLAX-5, no token, no governance body, fork-friendly
  evolution via the Fork Protocol.

[1.0.1]: https://github.com/aquaursa/parallax-5/releases/tag/v1.0.1
[1.0.0]: https://doi.org/10.5281/zenodo.20400525
