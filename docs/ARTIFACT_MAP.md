# PARALLAX-5 Artifact Map

**Purpose.** This document is the canonical, machine-readable inventory of every artifact referenced by the PARALLAX-5 paper. Each entry traces a paper claim to a file with a verifiable property. The paper's Appendix C contains a compact summary table; this file is the full map.

**Conformance.** A repository implementing PARALLAX-5 SHOULD include all artifacts in the "Formal core" and "Substrate foundations" sections. The "the worked examples worked examples" section is recommended for completeness but is not required for substrate conformance.

---

## Formal core (substrate v8 carryover)

| Artifact | File | Claim |
|---|---|---|
| Lean module | `parallax/formal/lean/Parallax5.lean` | 95 theorems, 0 `sorry` |
| Verification script | `parallax/formal/lean/verify.sh` | exit-code 0 on clean kernel run |
| Z3 SMT models | `parallax/formal/*.py` | UNSAT/SAT verdicts per Table 9 (Solver Stack) |
| Catalog (Python) | `parallax/formal/exploit_catalog.py` | 53 entries with confidence intervals |
| Fire tests | `parallax/formal/fire_tests.py` | 134 tests, 9 suites, all pass <30s |
| Halmos contracts | `parallax/formal/halmos/contracts/*.sol` | 4 vulnerable/hardened archetype pairs |
| Halmos verifier | `parallax/formal/halmos/verify.sh` | bytecode-level symbolic verification |

## Substrate foundations

| Artifact | File | Claim |
|---|---|---|
| Non-Capturability Charter | `docs/CHARTER.md` | 11-article CC0 governance commitment |
| Fork Protocol | `docs/FORK_PROTOCOL.md` | 4 fork types, 4 compatibility levels |
| Certificate Schema RFC v1.0 | `docs/CERTIFICATE_SCHEMA.md` | 19 fields, 7-state lifecycle, canonical serialization |
| JSON Schema | `schemas/certificate_v1.json` | validates as Draft 2020-12 |
| Worked-example certificate | `examples/certificate_uniswap_v3_core.json` | validates clean; CROPS (4,5,5,0,5); walkaway full |
| Walkaway theorem | `lean/Parallax5/Walkaway.lean` | 394 lines, 6 theorems, 0 `sorry` |
| Walkaway companion note | `docs/WALKAWAY_THEOREM.md` | accessible explainer with 5-level classification |
| CROPS module | `src/parallax5_coordinator/crops.py` | executable specification of v1.0.1 contribution matrix |
| CROPS test suite | `tests/test_crops.py` | 19 tests, all passing (including v1.0.1 invariants) |
| CROPS companion note | `docs/CROPS_VECTOR.md` | matrix rationale and worked examples |

## Worked examples

### Demo 1: ERC-4626 inflation attack (A1, D4)

| Artifact | File | Claim |
|---|---|---|
| Vulnerable contract | `demos/vault/contracts/VulnerableVault.sol` | reproduces Cream-clone inflation archetype |
| Patched contract | `demos/vault/contracts/PatchedVault.sol` | OpenZeppelin v4.8 virtual-shares mitigation |
| Exploit simulator | `demos/vault/exploit.py` | 2 scenarios, deterministic, victim loss bounded at 2.5e-7 on patched |
| Conservation proof | `demos/vault/proof/Conservation.lean` | 196 lines, 5 theorems, 0 `sorry` |
| Certificate | `demos/vault/output/certificate.json` | CROPS (4,5,5,0,4); walkaway full |
| Report | `demos/vault/REPORT.md` | accessible writeup |

### Demo 2: Bridge attestation (A3 + A5, D4)

| Artifact | File | Claim |
|---|---|---|
| Vulnerable contract | `demos/bridge/contracts/VulnerableBridge.sol` | malleable signatures + stale attestation |
| Patched contract | `demos/bridge/contracts/PatchedBridge.sol` | EIP-2 low-s + freshness window + epoch-binding hash |
| Exploit simulator | `demos/bridge/exploit.py` | 4 scenarios, ECDSA-faithful (uses `ecdsa` lib) |
| Attestation proof | `demos/bridge/proof/Attestation.lean` | 193 lines, 6 theorems, 0 `sorry` |
| Certificate | `demos/bridge/output/certificate.json` | CROPS (4,4,5,0,4) under v1.0.1 matrix; walkaway bounded |
| Report | `demos/bridge/REPORT.md` | accessible writeup |

### Demo 3: AI-agent runtime gate (A1 + A2, D5)

| Artifact | File | Claim |
|---|---|---|
| Target vault | `demos/agent_gate/contracts/TargetVault.sol` | the vault the agent acts against |
| Runtime gate | `demos/agent_gate/contracts/RuntimeGate.sol` | step-secure-enforcing relay contract |
| Gate simulator | `demos/agent_gate/simulate.py` | 5 scenarios, all pass |
| Containment proof | `demos/agent_gate/proof/Containment.lean` | 261 lines, 4 theorems incl. AI-Agent Containment, 0 `sorry` |
| Certificate | `demos/agent_gate/output/certificate.json` | CROPS (5,5,5,0,5); walkaway bounded; D5 on A1, A2 |
| Report | `demos/agent_gate/REPORT.md` | accessible writeup |

### Demo orchestration

| Artifact | File | Claim |
|---|---|---|
| Makefile | `Makefile` | `make demo-all` runs all three end-to-end |
| Verification recipe | `RUN_VERIFICATION.sh` | full pipeline check |

## Onchain certificate registry

| Artifact | File | Claim |
|---|---|---|
| Registry contract | `registry/src/ParallaxRegistry.sol` | 200 LOC, Apache-2.0, Solidity 0.8.24, gas-profiled |
| Foundry test suite | `registry/test/ParallaxRegistry.t.sol` | 24 tests pass (incl. 2 fuzz @ 256 runs each) |
| Lean state-machine proof | `lean/Parallax5/Registry.lean` | 6 theorems, 0 `sorry` |
| Deploy script | `registry/script/Deploy.s.sol` | env-driven, supports anvil/sepolia/mainnet |
| Deploy shell wrapper | `registry/scripts/deploy.sh` | safety-prompted mainnet path |
| Deployment manifest | `registry/deployments.json` | per-network address records |
| Python client | `src/parallax5_coordinator/registry_client.py` | web3.py wrapper with typed ABI |
| CLI registry submit | `parallax5 registry submit CERT.json [--broadcast]` | dry-run by default; live broadcast gated on env key |
| CLI registry state | `parallax5 registry state CERT.json` | reads on-chain state for a fingerprint |
| Usage doc | `docs/REGISTRY.md` | contract + deployment + audit notes |

## Coordinator and tooling

| Artifact | File | Claim |
|---|---|---|
| parallax5 CLI | `src/parallax5_coordinator/cli.py` | 6 subcommands: validate, certify, registry, theorems, crops, demo |
| Theorems module | `src/parallax5_coordinator/theorems.py` | 2,152 compositional theorem checks, all pass |
| PARALLAX-5 standard | `paper/PARALLAX-5-Standard.md` | compliance levels P0–P5 |

## Paper (canonical artifact)

| Artifact | File | Claim |
|---|---|---|
| Paper PDF | `paper/parallax-5.pdf` | 46 pages, three-pass clean compile, 0 unresolved refs |
| Paper TeX | `paper/parallax-5.tex` | source for reproducible compilation |

---

## Verification commands

| To verify | Command |
|---|---|
| All compositional theorems | `PYTHONPATH=src python3 -m parallax5_coordinator.theorems` |
| CROPS test suite | `PYTHONPATH=src python3 tests/test_crops.py` |
| All three demos end-to-end | `make demo-all` |
| Schema validation | `parallax5 validate examples/certificate_uniswap_v3_core.json` |
| Lean kernel (sorry audit) | `for f in lean/Parallax5/*.lean demos/*/proof/*.lean; do grep -c sorry $f; done` |
| Paper compile | `cd paper && pdflatex parallax-5.tex` |
| Full verification recipe | `./RUN_VERIFICATION.sh` |

---

*Last updated: 2026-05-26. This map is versioned with the substrate; updates accompany each release.*
