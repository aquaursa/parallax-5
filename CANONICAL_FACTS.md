# PARALLAX-5 Canonical Facts

**Version**: 1.0.1
**Last verified**: 2026-05-27
**Purpose**: Single source of truth for every numerical claim about PARALLAX-5. Documentation, paper, marketing, and external citations should reference this file. If you find a discrepancy elsewhere in this repository, the bug is elsewhere — not here.

Every claim in this document is mechanically verifiable. Reproduce all of them locally with:

```bash
./RUN_VERIFICATION.sh
```

The reproduction takes ~3 minutes (Python gates) or ~10 minutes (with the Foundry tests and paper compile).

---

## Formal verification

| Claim | Value | How to verify |
|---|---|---|
| Lean theorems in `parallax/formal/lean/Parallax5.lean` (paper-canonical core) | **95** | `grep -cE "^theorem \|^lemma " parallax/formal/lean/Parallax5.lean` |
| Lean theorems across substrate + demos (CHANGELOG v1.0.1 aggregate) | **135** | `find . -name "*.lean" -not -path "./notebooks/*" -exec grep -hE "^theorem \|^lemma " {} \; \| wc -l` |
| Lean theorems including exploratory notebooks | **177** | `find . -name "*.lean" -exec grep -hE "^theorem \|^lemma " {} \; \| wc -l` |
| `sorry` occurrences in proof bodies (excluding comments) | **0** (across all 177) | `find . -name "*.lean" -exec grep -hE "(^\|\s)sorry(\s\|$)" {} \; \| grep -vE "^\s*(--\|/\*)" \| wc -l` |
| Lean toolchain (`Parallax5.lean` core) | **4.10.0** | See file header |
| Lean toolchain (`Parallax5_EvmYulLean.lean` instance) | **4.22.0** | Matches Nethermind/EVMYulLean's `lean-toolchain` |

The `Parallax5.lean` core (95 theorems) is the bulk of the mechanization and what the paper cites in its main claim. The CHANGELOG's 135 figure aggregates the core with `lean/Parallax5/*.lean` (Compositional, Walkaway, Registry) and the three demo proofs (Vault Conservation, Bridge Attestation, Agent-gate Containment). The additional 42 theorems in `notebooks/lean_modules/` are exploratory work and not load-bearing for the substrate's main claims.

The EVMYulLean instance file lives on a different Lean toolchain track to match the upstream EVMYulLean version. Abstract refinement theorems transfer to the concrete instance by parametricity.

## Empirical catalog

| Claim | Value | How to verify |
|---|---|---|
| Incident rows in `paper/supplement/catalog.csv` | **53** | `python3 -c "import csv; print(len(list(csv.DictReader(open('paper/supplement/catalog.csv')))))"` |
| Aggregate loss USD | **5,966,000,000** | `python3 -c "import csv; print(sum(float(r['loss_usd']) for r in csv.DictReader(open('paper/supplement/catalog.csv')) if r['loss_usd'].strip()))"` |
| Marketing-friendly aggregate | **\$5.97B** | Round of the above to two significant figures |
| Date range (first row) | **2016-06-17** (The DAO) | First data row of catalog |
| Catalog columns | 15: `protocol, date, loss_usd, chain, archetype, root_cause_class, basis_observable, axiom_signature, confidence, preventive_control, containment_control, halmos_reproduction, axiomsol_catches, sources, notes` | `head -1 paper/supplement/catalog.csv` |

## Test suites

| Suite | Pass count | Where it runs |
|---|---|---|
| **All Python fire tests (paper-canonical aggregate)** | **129** | All Python test files combined; matches paper §1 claim |
| Compositional theorems (sub-checks) | **2,152** | `python -m parallax5_coordinator.theorems` |
| CROPS test suite (cross-runtime obligation-preserving) | **19/19** | `python tests/test_crops.py` |
| Fire tests (`parallax/formal/fire_tests.py`) | **65/65** | `python parallax/formal/fire_tests.py` |
| ObligationSol fire tests | **10/10** | `python parallax/obligationsol/fire_tests.py` |
| Obligations fire tests | **3/3** | `python parallax/obligations/fire_tests.py` |
| Mapping registry tests | **11/11** | `python -m pytest tests/test_mapping_registry.py -v` |
| Foundry tests (ParallaxRegistry) | **24/24** | `cd registry && forge test` (includes 2 fuzz tests at 256 runs) |
| Paper compile | 3-pass pdflatex, **0 errors, 0 unresolved refs** | `cd paper && pdflatex parallax-5.tex` (×3) |

Self-consistency: `parallax/formal/fire_tests.py::test_paper_counts_match_artifact_state` programmatically asserts that the paper text contains the string "129 Python fire tests" and that `parallax/formal/lean/Parallax5.lean` contains 95 theorems with zero `sorry`. Any drift between paper and code fails CI.

All of these are gated on every push and PR — see `.github/workflows/ci.yml`.

## On-chain artifacts

| Asset | Value | How to verify |
|---|---|---|
| Sepolia certificate registry address | **`0x8015A98dF9037Cd79a03B291a6fF3C2841992D5b`** | `curl https://api.etherscan.io/v2/api?chainid=11155111&module=proxy&action=eth_getCode&address=0x8015A98dF9037Cd79a03B291a6fF3C2841992D5b&tag=latest&apikey=$KEY` (returns non-empty bytecode) |
| Etherscan link | https://sepolia.etherscan.io/address/0x8015A98dF9037Cd79a03B291a6fF3C2841992D5b#code | Browser |
| Mainnet deployment | not yet deployed | Future |

## Publication metadata

| Asset | Identifier | URL |
|---|---|---|
| Main paper (Zenodo v1.0.1) | DOI `10.5281/zenodo.20402755` | https://doi.org/10.5281/zenodo.20402755 |
| Main paper (Zenodo v1.0.0, superseded) | DOI `10.5281/zenodo.20400525` | https://doi.org/10.5281/zenodo.20400525 |
| EVMYulLean integration verification artifact | DOI `10.5281/zenodo.20386868` | https://doi.org/10.5281/zenodo.20386868 |
| GitHub repository | `aquaursa/parallax-5` | https://github.com/aquaursa/parallax-5 |
| Marketing site | parallax.aquaursa.ai | https://parallax.aquaursa.ai |
| Author / org | AquaUrsa Research LLC (Wyoming, USA) | research@aquaursa.ai |

The Zenodo v1.0.1 deposit is the most recent version. v1.0.0 remains accessible at its original DOI but is superseded.

## Worked examples

Three case studies that exercise the substrate end-to-end:

1. **Vault** (`demos/vault/`) — ERC-4626-shape conservation invariant. Lean refinement in `demos/vault/proof/Conservation.lean` (5 theorems).
2. **Bridge** (`demos/bridge/`) — external-attestation trust boundary. Lean refinement in `demos/bridge/proof/Attestation.lean` (7 theorems).
3. **Agent gate** (`demos/agent_gate/`) — the AI-Agent Containment Theorem. Lean refinement in `demos/agent_gate/proof/Containment.lean` (6 theorems).

Each demo has its own `Makefile` target: `make demo-vault`, `make demo-bridge`, `make demo-agent-gate`.

## Multi-runtime support

| Runtime | `ValueBearingMachine` / `EvmLikeMachine` instance | Refinement depth |
|---|---|---|
| EVM (production semantic refinement via EVMYulLean) | yes — `parallax/formal/lean/Parallax5_EvmYulLean.lean` | Production-grade (composes with EVMYulLean's 99.99% Ethereum conformance) |
| EVM (typeclass-level) | yes — `parallax/formal/lean/Parallax5.lean` | Abstract |
| Solana / SVM | yes — typeclass-level instance | Demonstration only; full semantic refinement is future work |
| Move (Sui / Aptos) | yes — typeclass-level instance | Demonstration only; full semantic refinement is future work |
| Traditional banking ledger | yes — typeclass-level instance | Demonstration only |

The CROPS test suite (19 tests) demonstrates that the same obligation set, expressed abstractly, reduces to runtime-specific checks correctly across the four runtimes.

We are explicit about scope: production-grade refinement (via a third-party Lean development of the target semantics, the way we use EVMYulLean for EVM) currently exists only for EVM. The other runtimes are typeclass-level demonstrations of the generic theorem `generic_agent_gate_preserves_security`.

## Reference implementation surface

| Component | Status |
|---|---|
| `parallax5` CLI (validate, quote, capability, audit-import) | Functional — see `pyproject.toml::project.scripts` |
| `parallax5-coordinator` CLI | Functional |
| `ParallaxRegistry.sol` Solidity contract | Deployed Sepolia (`0x8015…92D5b`); 24/24 Foundry tests pass |
| Lean mechanization (`parallax/formal/lean/`) | Compiles; 95 theorems in core file, 0 `sorry` |
| EVMYulLean composition (`parallax/formal/lean/Parallax5_EvmYulLean.lean`) | Spec-complete; build requires lake-based Lean 4.22.0 project (see file header for setup) |
| Certificate schema v9 (`schemas/`) | 19 fields; backward-compatible with v8 |

## What we explicitly do NOT claim

- **100% exploit prevention.** The 53-incident catalog separates **basis-observable** losses (\$4,007,500,000 / 67.2% / 43 incidents) from **basis-unobservable** losses (\$1,623,500,000 / 27.2% / 8 incidents) and **ambiguous** cases (\$335,000,000 / 5.6% / 2 incidents). Only the basis-observable share is preventable by a deployed PARALLAX-5 gate. The full \$5.97B is not. Verify: `python3 -c "import csv; r=list(csv.DictReader(open('paper/supplement/catalog.csv'))); print({k: sum(float(x['loss_usd']) for x in r if x['basis_observable']==k) for k in ('yes','no','ambiguous')})"`
- **Production-grade refinement for non-EVM runtimes.** Solana and Move instances are typeclass-level demonstrations. Full semantic refinement is explicit future work.
- **Full AGI safety.** The AI-Agent Containment Theorem covers the slice of AI agents that propose transitions to value-bearing state machines. It does not bound emergent multi-agent behavior or out-of-band influence.
- **Minimality of A1–A5.** The five-obligation set appears sufficient for the empirical surface we have examined; we have not proven minimality.

## Update protocol

If a value in this file changes (e.g., new theorems added, new catalog rows, etc.):

1. Update this file **first**, in the same commit as the underlying change
2. Update the `Last verified` date at the top
3. Update CITATION.cff if the version number changes
4. Search the codebase for the old value and replace any stale references
5. Commit message: `chore(canonical-facts): update {field} ({reason})`

This file is the head of the documentation graph. Drift here is a bug.
