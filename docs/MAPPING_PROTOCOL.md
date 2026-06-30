# PARALLAX-5 Mapping Protocol v1.0

**Specification for tool-mapping documents in the PARALLAX-5 registered-mapping pattern**

| | |
|---|---|
| **Version** | 1.0.0 |
| **Status** | Stable since v1.0.1; namespace pattern introduced in v1.1.0 |
| **Authors** | AquaUrsa Research |
| **License** | CC0 1.0 Universal (per Non-Capturability Charter Article 2) |
| **Date** | May 2026 |
| **Parent DOI** | 10.5281/zenodo.20386868 (PARALLAX-5 / EVMYulLean Integration Verification) |
| **Repository** | github.com/aquaursa-research/parallax5-coordinator |

---



## 0. The namespace pattern (added in substrate v1.1.0)

This document specifies a **protocol**, not a single mapping. The
PARALLAX-5 coordinator accepts certificates that reference any
registered tool-mapping conforming to this protocol. The substrate
ships one reference mapping, **`aquaursa-v1`**, authored by AquaUrsa
Research and located at `mappings/aquaursa-v1.json`. Its narrative
companion is `docs/mappings/aquaursa-v1.md`. Other authors are
invited to publish their own mappings under the namespace pattern

```
tool-mapping/{author}-v{major}
```

See `mappings/README.md` for the registration process.

When this document refers to "the mapping" below (e.g., in
"the mapping enables compositional verification"), substitute any
specific registered mapping the reader is using; the protocol
described here is identical across all conforming mappings.

## 1. Purpose

TOOL-MAPPING v1.0 is a structured calibration artifact that records, for each smart-contract analysis tool in scope, the mapping from that tool's native finding categories to the PARALLAX-5 obligation taxonomy (A1–A5) with an evidence depth (0–5) and a justification.

The mapping enables compositional verification: when multiple tools are run against the same contract, their outputs can be aggregated by obligation, with the joint coverage on each obligation being the maximum evidence depth contributed by any tool. The resulting per-obligation depth vector determines a defensible PARALLAX-5 P-level certificate.

## 2. Scope

TOOL-MAPPING v1.0 covers four EVM-focused tools at the indicated version pins:

| Tool | Version | Documentation |
|---|---|---|
| Slither | 0.10.x | https://github.com/crytic/slither/wiki/Detector-Documentation |
| Mythril | 0.24.x | https://github.com/SmartContractSecurity/SWC-registry |
| halmos | 0.2.x | https://github.com/a16z/halmos |
| ObligationSol | parallax5-v6 | https://parallax.xyz/research |

Solana (Anchor, Move), Substrate (ink!, pallets), and non-EVM tooling are out of scope for v1.0 and will be addressed in v1.x point releases as their analyzer ecosystems mature.

## 3. Definitions

### 3.1 Obligation

A PARALLAX-5 obligation is one of:

| Obligation | Informal | Formal |
|---|---|---|
| A1 | Value conservation | Total supply and per-account balances respect the relational conservation predicate. |
| A2 | Authorization closure | Every privileged operation has been authorized by a verifiable principal under the protocol's access-control policy. |
| A3 | Signature integrity | Cryptographic signatures used to authorize off-chain commitments are EUF-CMA secure under the protocol's signature scheme. |
| A4 | Temporal distinctness | State transitions complete atomically: no observable intermediate state admits re-entry or stale-read attack. |
| A5 | External-attestation trust | Off-chain attestations (oracles, bridge messages) used in on-chain decisions are within the protocol's freshness and quorum windows. |

### 3.2 Evidence depth

Evidence depth is a six-level monotone ladder:

| Depth | Label | Meaning |
|---|---|---|
| 0 | None | No relevant capability. |
| 1 | Mention | Code-location report; human-interpreted. |
| 2 | Static detector | Pattern match flagged the issue; sound up to detector calibration. |
| 3 | Symbolic-path witness | Path-condition for the issue is exhibited; restricted by exploration bounds. |
| 4 | Formal property | Verified by symbolic / bounded model checker against a stated invariant. |
| 5 | Machine theorem | Property is a theorem in an interactive proof assistant accepted by the kernel. |

A claim at depth `k` subsumes the (weaker) claim at depth `j` for `j ≤ k`.

### 3.3 Compositional theorems

**Theorem 1 (Compositional Coverage).** For a tool set T with per-tool capabilities `c_t : Obligation → Depth`, the joint capability `C_T(A) := max_{t ∈ T} c_t(A)` satisfies pointwise monotonicity and refinement under tool addition.

**Theorem 2 (Certificate Monotonicity).** Adding a tool to T never lowers the P-level certifiable from the joint capability.

Both theorems are mechanically verified by exhaustive check over the finite depth lattice (Python coordinator, 2,152 algebraic checks) and stated with kernel-accepted proofs in Lean 4 (`Parallax5/Compositional.lean`).

## 4. Mapping format

Each entry has the structure:

```json
{
  "finding_id": "...",          // tool-native identifier
  "obligation": "A1..A5",       // mapped obligation
  "depth":      0..5,           // evidence depth
  "justification": "..."        // textual rationale
}
```

The full machine-readable specification is published as `schemas/tool_mapping_v1.json` in the coordinator repository.

## 5. Calibrated capability matrix

The depth values below reflect each tool's documented capabilities on a typical Solidity codebase under default invocation. Halmos's capability is conditional on user-supplied property functions; the matrix records both the intrinsic ceiling (with-property) and the cold-run default (depth 0 on all obligations).

| Tool | A1 | A2 | A3 | A4 | A5 |
|---|---|---|---|---|---|
| Slither           | 2 | 2 | 0 | 2 | 0 |
| Mythril           | 3 | 3 | 2 | 3 | 0 |
| halmos (cold)     | 0 | 0 | 0 | 0 | 0 |
| halmos (with property)  | 4 | 4 | 4 | 4 | 4 |
| ObligationSol          | 2 | 2 | 0 | 2 | 2 |
| **Joint (with halmos+property)** | **4** | **4** | **4** | **4** | **4** |
| **Joint (cold)**  | **3** | **3** | **2** | **3** | **2** |

### 5.1 Key observations

- **A5 is uniquely served by ObligationSol** in the cold-run stack. Without ObligationSol, joint A5 capability collapses to 0. This is the empirical basis for ObligationSol's compositional necessity claim, exemplified by the Mango Markets case (incident-009).

- **A3 requires either Mythril or halmos-with-property**. Slither and ObligationSol have no native A3 reasoning. Mythril provides static-detector depth on a limited set of SWC categories (SWC-117 signature malleability, SWC-122 missing signature verification).

- **halmos is conditionally universal**. It can achieve depth 4 on any obligation given an appropriate property function. Without specification effort, its contribution is 0.

- **Cross-tool agreement at depth 2–3** is common for A1, A2, A4 (Slither + Mythril + ObligationSol). The mapping captures the agreement as evidence-aggregation rather than competition.

## 6. Per-tool entries

### 6.1 Slither (14 entries)

| Finding ID | Obligation | Depth | Justification |
|---|---|---|---|
| arbitrary-send-eth | A1 | 2 | Ether-send to attacker-controlled recipient; conservation violation. |
| arbitrary-send-erc20 | A1 | 2 | Same for ERC-20 transfers. |
| controlled-array-length | A1 | 2 | Storage-layout corruption can affect balance/supply slots. |
| incorrect-equality | A1 | 1 | Strict equality on supply/balance state; weak indicator. |
| unprotected-upgrade | A2 | 2 | Unauthorized impl-replacement on proxy. |
| unprotected-initialize | A2 | 2 | Reinitialization vulnerability. |
| suicidal | A2 | 2 | Unguarded SELFDESTRUCT. |
| tx-origin | A2 | 2 | tx.origin authorization (phishing-vulnerable). |
| delegatecall-loop | A2 | 2 | Delegatecall to user-supplied target. |
| reentrancy-eth | A4 | 2 | Classical ether-reentrancy. |
| reentrancy-no-eth | A4 | 2 | ERC-777-style callback reentrancy. |
| reentrancy-events | A4 | 2 | Event-emission reentrancy (low severity). |
| reentrancy-benign | A4 | 1 | Reentrancy with no apparent state inconsistency. |
| reentrancy-unlimited-gas | A4 | 2 | call.value without gas stipend. |

### 6.2 Mythril (8 entries, SWC-indexed)

| SWC | Name | Obligation | Depth | Justification |
|---|---|---|---|---|
| SWC-105 | Unprotected Ether Withdrawal | A1 | 3 | Path-condition witness for unauthorized withdrawal. |
| SWC-105 | Unprotected Ether Withdrawal | A2 | 3 | Same finding evidences authorization-closure failure. |
| SWC-106 | Unprotected SELFDESTRUCT | A2 | 3 | Symbolic path to SELFDESTRUCT without auth predicate. |
| SWC-107 | Reentrancy | A4 | 3 | Symbolic exploit path for reentrancy. |
| SWC-115 | Authorization through tx.origin | A2 | 2 | Pattern detector, not strengthened by symbolic exec. |
| SWC-117 | Signature Malleability | A3 | 2 | Pattern: missing low-s enforcement on ECDSA. |
| SWC-122 | Lack of Proper Signature Verification | A3 | 2 | Pattern: missing signature checks on privileged ops. |
| SWC-101 | Integer Overflow/Underflow | A1 | 3 | Symbolic path for arithmetic wrap violating conservation. |

### 6.3 halmos (5 entries, property-based)

| Finding ID | Obligation | Depth | Justification |
|---|---|---|---|
| invariant-violated | A1 | 4 | User-stated conservation invariant counterexample. |
| invariant-violated | A2 | 4 | User-stated authorization invariant. |
| invariant-violated | A3 | 4 | ECDSA symbolic model; signature-integrity properties. |
| invariant-violated | A4 | 4 | User-stated reentrancy invariant. |
| invariant-violated | A5 | 4 | Oracle staleness/quorum invariants. **Only tool with intrinsic A5 capability.** |

Halmos's coverage on each obligation is conditional on the analyst writing the corresponding property function. Cold-run depth = 0.

### 6.4 ObligationSol (6 entries)

| Finding ID | Obligation | Depth | Justification |
|---|---|---|---|
| A1_supply_inflation_signature | A1 | 2 | Obligation-signature pattern: supply-inflating operations. |
| A2_unprotected_admin_signature | A2 | 2 | Admin-protected ops missing access-control modifier. |
| A4_reentrancy_lock_absent | A4 | 2 | Reentrancy-guard absence across external-call entries. |
| A4_call_depth_unbounded | A4 | 2 | Recursive calls without depth bounds. |
| A5_oracle_stale_window | A5 | 2 | Oracle freshness check absent or permissive. **Unique to ObligationSol in cold-run stack.** |
| A5_oracle_quorum_insufficient | A5 | 2 | Oracle quorum below safe threshold. **Unique to ObligationSol in cold-run stack.** |

## 7. Compositional necessity: three worked cases

### 7.1 DAO reentrancy (incident-001)

```
Joint coverage on A4: 3 (from Mythril SWC-107)
Cross-tool confirmation: Slither (depth 2) + Mythril (depth 3) + ObligationSol (depth 2)
Marginal value of ObligationSol: confirmatory, not additive on A4
Joint capability still 0 on A3 and A5 in cold-run; certificate caps at P0.
```

### 7.2 Mango Markets oracle (incident-009) — **canonical compositional necessity**

```
Joint coverage on A5:
  {Slither, Mythril}              → 0   (no oracle reasoning in either tool)
  {Slither, Mythril, halmos_cold} → 0   (cold-run halmos contributes nothing)
  {Slither, Mythril, ObligationSol}    → 2   (ObligationSol unlocks A5)
Without ObligationSol, no A5 evidence at static-detector depth.
ObligationSol is NECESSARY (not merely useful) for any defensible A5 claim
in the current cold-run tool stack.
```

### 7.3 Beanstalk governance (incident-006)

```
Joint coverage on A2 with halmos-and-property: 4
  Slither (depth 1 — weak governance-pattern detection)
  Mythril (depth 1 — limited)
  halmos+property "quorum-invariant" (depth 4 — formal property)
  ObligationSol (depth 2 — partial signature match)
halmos's user-specified quorum invariant dominates; the others provide
complementary lower-depth evidence supporting the same conclusion.
```

## 8. Open problems

1. **Cross-function reentrancy at static-detector depth** is under-served by current detectors; full coverage requires depth 3+. The mapping should be refined when restricted to cross-function specifically.

2. **MEV-dependent A5 violations** (oracle manipulation enabled by extracted MEV) are out of scope of current tooling; specialized detectors needed.

3. **Off-chain attestation freshness in EVMYulLean.** The current deposit's EvmLikeMachine instance uses `attestationFresh := true` as a conservative approximation; a faithful implementation requires an upstream extension to `EvmYul.EVM.State` adding an explicit freshness oracle field.

4. **Solana / Move backends** are not yet mapped; cross-chain certification awaits per-VM mapping tables.

## 9. Governance and versioning

### 9.1 Contribution

The mapping is intended as a living, community-extensible artifact. Contributions are accepted via pull request to the coordinator repository under the following criteria:

- Each new entry must cite the tool's documentation for the finding category.
- Each new entry must include a justification at least two sentences in length.
- Each new entry must specify the version range over which it applies.
- Depth assignments above 2 must reference the underlying analysis technique (symbolic execution, formal property, theorem proof).

### 9.2 Versioning

TOOL-MAPPING follows semantic versioning:

- **Major (v2.0.0)**: Restructuring the mapping format or obligation taxonomy.
- **Minor (v1.1.0)**: Adding a new tool to scope or substantial revision of existing entries.
- **Patch (v1.0.1)**: Correcting individual entry justifications, version pins, or depth calibrations on existing entries.

Each minor / major version is deposited to Zenodo with its own DOI. Patches are made on the trunk repository.

### 9.3 Annual recalibration

The mapping is recalibrated annually with a published list of tool-version updates, new entries, and adjustments. The next recalibration is scheduled for May 2027.

## 10. Citation

```bibtex
@misc{aquaursa2026toolmapping,
  author    = {{AquaUrsa Research}},
  title        = {{TOOL-MAPPING v1.0: Canonical Mapping of Smart-Contract
                  Analysis Tool Findings to PARALLAX-5 Obligations}},
  year         = {2026},
  month        = may,
  version      = {1.0.0},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.XXXXXXXX},  
  note         = {Companion to PARALLAX-5 / EVMYulLean Integration
                  Verification, doi:10.5281/zenodo.20386868}
}
```

---

*This document describes a community standard, not a complete formal specification. The authoritative machine-readable specification is `schemas/tool_mapping_v1.json` in the coordinator repository, accompanied by the Lean 4 mechanization of the supporting compositional theorems in `lean/Parallax5/Compositional.lean`.*
