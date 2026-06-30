# PARALLAX-5: A Standard for Obligation-Based Safety in Value-Bearing Computation

**Status:** Draft Standard\
**Editors:** AquaUrsa Research\
**Date:** May 2026\
**Document:** PRX-5-2026-001

---

## Abstract

This document specifies PARALLAX-5, a standard for static and runtime safety verification of value-bearing state machines. PARALLAX-5 defines (a) five orthogonal safety invariants, (b) declaration syntax for asserting per-function obligations, (c) the verification semantics under which a contract is said to "satisfy" the standard, (d) compliance test vectors, and (e) integration patterns for static analyzers, runtime gates, and insurance frameworks.

The intent of this document is to provide a single, mechanically verifiable specification that any auditor, insurer, smart-contract platform, or regulator can reference to make precise statements about a contract's or system's safety posture.

## 1. Scope and Motivation

PARALLAX-5 covers on-chain state-machine safety. The five invariants in §3 collectively cover the documented class of code-level vulnerabilities in decentralized finance (2016–2026), aggregating approximately \$3.38B of historical losses. Off-chain failures—key compromise, signer social engineering, oracle-infrastructure subversion—are explicitly out of scope of this standard and SHALL be addressed by complementary controls (see §11).

This document uses the keywords MUST, SHOULD, MAY, and SHALL as defined in RFC 2119.

## 2. Terminology

* **Value-bearing state machine:** a stateful computation whose state space contains data with monetary or asset interpretation, and whose transitions can transfer such data between principals.
* **On-chain:** state and transitions whose semantics are determined by a public, deterministic execution environment (EVM, SVM, Move VM, etc.).
* **Off-chain:** semantic content (keys, attestations, configuration) whose integrity depends on trust assumptions outside the deterministic execution environment.
* **Principal:** an identity that can initiate transitions (EOA, contract, signer set).
* **Obligation (in this document):** one of five named safety invariants, each defined precisely in §3.
* **Obligation:** a per-function declaration that the function satisfies a given obligation (declaration syntax in §4).
* **Verification:** the act of mechanically establishing that a contract's functions discharge their declared obligations (semantics in §5).
* **Compliance:** the property of having every obligation discharged AND every relevant obligation declared for every value-affecting function (criteria in §6).

## 3. the five obligations

### 3.1 A1 — Share-Asset Conservation

For every state \(s\) of a vault-type state machine:

> If \(s.\text{shares} > 0\), then \(s.\text{assets} > 0\), and if \(s.\text{assets} > 0\), then \(s.\text{shares} \geq \rho_{\min}\), where \(\rho_{\min}\) is a system parameter (RECOMMENDED \(\rho_{\min} = 10^3\)).

**Rationale:** prevents share-supply inflation attacks (Cream Finance class) by guaranteeing a non-trivial minimum supply once assets are deposited.

### 3.2 A2 — Authorization Closure

For every state-mutating function \(f\) on the value-bearing state machine:

> Either the calling principal is in the authorized set for \(f\), or the call SHALL revert.

The authorized set MAY be a single owner, a multisig threshold, a governance quorum, or any precisely specified predicate.

**Rationale:** prevents unauthorized state mutation (Parity Multisig class, Pickle class).

### 3.3 A3 — Signature Integrity

For every function accepting a signature-bound authorization:

> The recovered signer MUST be non-zero, MUST equal the expected signer, AND the message hash MUST include domain separator, nonce, deadline, and chain ID.

**Rationale:** prevents signature replay and forgery (Wormhole, Nomad, generic EIP-712 misuse).

### 3.4 A4 — Temporal Distinctness

For every value-affecting external function entry/exit:

> The call depth MUST be 0 at entry-and-exit, OR the function MUST be explicitly marked as a permitted re-entrant continuation with its own audit obligations.

For every group of operations \((op_1, op_2)\):

> No same-block ordering MAY violate a documented sequencing dependency.

**Rationale:** prevents reentrancy (The DAO, Lendf.Me, Cream Finance 1st, Solv, Penpie) and flash-loan governance overrides (Beanstalk).

### 3.5 A5 — Oracle Trust Boundary

For every consumption of off-chain data:

> The data MUST carry a freshness timestamp, the current time MUST be within \(\tau_{\max}\) of the freshness timestamp (RECOMMENDED \(\tau_{\max} = 1800\) seconds), AND the data SHALL be sourced from a manipulation-resistant aggregator (multi-source, TWAP, or equivalent).

**Rationale:** prevents oracle manipulation (bZx, Harvest, PancakeBunny, Polter, Mango).

## 4. Declaration Syntax

This document specifies an annotation grammar for declaring per-function obligations. Implementations MAY use NatSpec, attribute syntax, or any equivalent mechanism. The canonical form is:

```
/// @axioms A1+ A4+ A5-
function deposit(uint256 assets) external returns (uint256 shares) { ... }
```

The annotation grammar:

* `A_i+` declares that the function preserves obligation \(A_i\).
* `A_i-` declares that the function does NOT need to preserve \(A_i\) (the obligation is irrelevant to the function's semantics; verifiers SHALL NOT discharge an obligation for \(A_i\) on this function).
* Absence of a declaration means the verifier SHALL infer the obligation from the function's behavior, or report "no claim" if inference is not supported.

## 5. Verification Semantics

A function \(f\) discharges its declared obligation \(A_i+\) if and only if, under all reachable pre-states satisfying \(A_i\) and all admissible inputs, the post-state of \(f\) also satisfies \(A_i\).

Equivalently:

> The Hoare triple \(\{A_i(s)\} \;\; f(s, \vec{x}) \;\; \{A_i(s')\}\) is valid.

Verifier implementations conforming to this standard MUST produce one of three verdicts:

* **DISCHARGED:** the verifier has produced a proof of the Hoare triple.
* **REFUTED:** the verifier has produced a counter-example \((s, \vec{x}, s')\) witnessing the triple's failure.
* **UNDETERMINED:** the verifier was unable to discharge or refute within its time/space budget.

A contract is **compliant** with PARALLAX-5 if every declared obligation receives a DISCHARGED verdict from at least one conforming verifier, with no REFUTED verdicts.

## 6. Conformance Criteria and Compliance Levels

### 6.1 Compliance Levels (P0–P5)

PARALLAX-5 defines five progressive compliance levels:

| Level | Name | Requirement |
|---|---|---|
| **P0** | Unclassified | No basis mapping declared. |
| **P1** | Annotated | Each value-affecting transition mapped to A1–A5 obligations via `@axioms` declarations. |
| **P2** | Statically Screened | ObligationSol or another static analyzer produces an obligation report; obligations flagged for human review. |
| **P3** | Symbolically Checked | Bounded counterexample search over all value-affecting paths (e.g., halmos, Mythril, Manticore) with no REFUTED verdicts. |
| **P4** | Formally Proved | SMT/Lean/Certora-style proof of obligations; every declared obligation DISCHARGED with machine-checkable artifact. |
| **P5** | Runtime Enforced | A pre-action gate rejects unsafe post-states at execution time and emits cryptographic certificates per transition. |

Higher levels include all requirements of lower levels. A protocol may declare different compliance levels for different functions or modules.

### 6.2 Conformance Criteria

A smart contract is conformant with this standard at level $L$ if and only if:

1. Every function that mutates value-bearing state has at least one explicit `@axioms` declaration (P1+).
2. The requirements of every level up to and including $L$ are satisfied.
3. The verifier's identity, version, and verification artifacts (counter-examples, SMT-LIB proof obligations, or proof terms) are published alongside the contract source code.

A platform (chain, L2, application platform) is conformant if it provides:

1. A mechanism for compiled bytecode to be associated with conformance certificates from registered verifiers.
2. A public registry of verified contracts and their conformance status and level.
3. A revocation mechanism for verifiers found to have issued faulty discharges.

## 7. Test Vectors

This standard includes a normative test suite of fixtures, each consisting of:

* A canonical vulnerable contract pattern (Cream-class, Wormhole-class, Mango-class, Solv-class, etc.).
* A canonical hardened equivalent.
* The expected verifier verdicts (REFUTED for vulnerable; DISCHARGED for hardened).

The test fixtures are available in the reference implementation under `parallax/formal/halmos/`. Implementations claiming conformance MUST pass the entire test suite.

## 8. Integration Patterns

### 8.1 Static Analyzer Integration

A static analyzer (Slither-class, Mythril-class, Certora-class) integrating with this standard SHOULD:

* Parse `@axioms` annotations from source.
* For each declared obligation, attempt to discharge the corresponding Hoare triple.
* Emit a conformance certificate in the format defined in §9.

### 8.2 Runtime Gate Integration

A runtime safety gate (i.e., a smart-contract or off-chain service that filters proposed actions) MAY use PARALLAX-5 by:

* Maintaining a registry of target-contract conformance certificates.
* Permitting actions only against conformant targets, OR
* Performing pre-action obligation verification against the candidate post-state.

### 8.3 Insurance Underwriting

An insurer underwriting smart-contract risk MAY use PARALLAX-5 conformance status as a primary risk indicator. The reference economic-security analysis (§10) provides a basis for premium pricing.

## 9. Conformance Certificate Format

A conformance certificate is a structured record (JSON, EIP-712 signed, or equivalent) carrying at minimum:

```
{
  "contract_address": "0x...",
  "source_hash": "0x...",                       // commit-pinned source
  "verifier_id": "halmos-0.3.3",                // verifier name + version
  "verifier_signature": "0x...",                // verifier attestation
  "obligations": [
    { "function": "deposit",
      "axioms": ["A1+", "A4+"],
      "verdict": "DISCHARGED",
      "evidence_uri": "ipfs://..." },
    ...
  ],
  "issued_at": "2026-05-24T00:00:00Z",
  "expires_at": "2027-05-24T00:00:00Z"
}
```

The evidence URI SHALL resolve to one of:

* A halmos counter-example trace (for REFUTED verdicts).
* An SMT-LIB proof obligation file (for DISCHARGED verdicts).
* A Lean 4 module containing the discharged theorem.
* Equivalent artifacts from other conforming verifiers.

## 10. Economic Security Reference

Under universal adoption of this standard (verification rate \(p \to 1\)), the rational attacker's expected utility over a single attack is

\[
\mathbb{E}[\text{utility}] = (1-p) \cdot v - c
\]

where \(v\) is the expected attack value and \(c\) is the attack cost. For typical DeFi attack values \(v = \$10^7\) and modest attack costs \(c = \$5 \times 10^4\), the critical verification rate above which rational attackers stop is

\[
p^* = 1 - c/v = 99.5\%.
\]

Empirically, the historical loss-prevention table:

| Verification rate | On-chain losses prevented (\$B) | % of total losses |
|---|---|---|
| 10%  | 0.34 | 5.7% |
| 25%  | 0.84 | 14.2% |
| 50%  | 1.69 | 28.3% |
| 75%  | 2.53 | 42.5% |
| 90%  | 3.04 | 51.0% |
| 99%  | 3.34 | 56.1% |
| 100% | 3.38 | 56.6% |

Note that 43.4% of historical losses are off-chain (key compromise, multisig social engineering, oracle infrastructure subversion) and remain outside this standard's scope. They require complementary controls per §11.

## 11. Trust Base (Off-Chain Assumptions)

PARALLAX-5 assumes the following off-chain conditions, which are NOT verified by conformance and SHALL be addressed by complementary controls:

* **OA1 — Key Integrity:** Signing keys are not exfiltrated, duplicated, or lost. Recommended controls: hardware-secured signing (HSM, secure enclave), key rotation, separation of duties.
* **OA2 — Signer Sovereignty:** Multisig and governance signers are not coerced, deceived, or coordinated by an adversary. Recommended controls: signer training, distributed jurisdiction, transaction-content review tooling, anti-phishing measures.
* **OA3 — Infrastructure Integrity:** RPC nodes, oracle data sources, validator software are not subverted. Recommended controls: multi-DVN configurations, oracle diversification, RPC redundancy, infrastructure hardening.

PARALLAX-5 conformance is necessary but not sufficient for total system safety; OA1–OA3 controls are complementary requirements.

## 12. Cross-VM Applicability

the five obligations generalize across execution environments. Implementations MAY apply this standard to:

* **Ethereum Virtual Machine** (EVM) — the reference environment.
* **Solana Virtual Machine** (SVM, SBPF) — accounts as state, sysvars as oracle source, CPI depth as call depth.
* **Move VM** (Sui, Aptos) — resources as conserved quantities, capabilities as authorization predicates.
* **CosmWasm** — actor model with replies analogous to callbacks.
* **Off-VM application substrates** (banking ledgers, healthcare records, supply chain registries) — same invariants over domain-specific value types.

Section 8.3 of the reference paper [PRX-PAPER-2026] formalizes the cross-VM equivalence via a type-class abstraction.

## 13. Versioning and Future Extensions

This document is version 1.0 of PARALLAX-5. Future revisions MAY:

* Add new obligations IF a documented vulnerability class is shown not to reduce to A1–A5 (none known as of publication).
* Refine the closure classes IF subdivisions of the existing 31 classes prove operationally significant.
* Extend the conformance certificate schema.

Backward-compatible extensions SHALL be issued as PARALLAX-5.x. Breaking changes SHALL be issued as PARALLAX-6.

## 14. References

[PRX-PAPER-2026] Anonymous (2026). *Conservation Laws for Decentralized Computation: A Five-Obligation Basis for State-Machine Security in DeFi and a Substrate for AI Agency.*

[RFC2119] Bradner, S. (1997). *Key words for use in RFCs to Indicate Requirement Levels.*

[KEVM] Hildenbrandt, E., et al. (2018). *KEVM: A Complete Formal Semantics of the Ethereum Virtual Machine.* IEEE CSF.

[HALMOS] a16z (2024). *halmos: Symbolic Bounded Model Checker for Ethereum.*

[LEAN4] Moura, L., et al. (2021). *The Lean 4 Theorem Prover and Programming Language.*

## Appendix A: Compliance Checklist

A contract author preparing for PARALLAX-5 conformance review SHOULD verify:

- [ ] Every value-affecting function carries an `@axioms` declaration.
- [ ] Every declared obligation is DISCHARGED by at least one conforming verifier.
- [ ] Counter-examples or proof artifacts are accessible via stable URI.
- [ ] First-depositor inflation protection (MIN_LIQUIDITY or equivalent) is in place for A1+ vaults.
- [ ] Authorization predicates are explicit (modifier or explicit require).
- [ ] All signature paths include zero-check, signer-match, domain separator, nonce, deadline, chain ID.
- [ ] Reentrancy guards are present on all functions that perform external calls AND mutate state, including sibling callback functions.
- [ ] Oracle reads include freshness gates and manipulation-resistant aggregation.

## Appendix B: Reference Implementation Stack

The reference implementation comprises:

* **ObligationSol:** Solidity dialect with `@axioms` annotations + a regex-based static checker.
* **halmos integration:** bytecode-level symbolic execution against obligation assertions.
* **Z3 abstract model:** state-machine model + 88 mechanically checked fire tests.
* **Lean 4 module:** 46 theorems including basis minimality, closure inhabitation, preservation under hardening, AI-agent session safety, cross-VM domain generalization, and completeness for the standard attack classes.

All reference artifacts and test vectors are available under the project repository (URL anonymized for review).

---

*This document is part of the PARALLAX-5 Standards Series. Comments and falsification attempts are explicitly invited under the open-science framing of the underlying research.*

## Appendix A. Example PARALLAX-5 Certificate

A conforming verifier emits a JSON certificate per verified contract per release.
The example below corresponds to a P4 (Formally Proved) compliance level on a
hypothetical ERC-4626 vault.

```json
{
  "schema_version": "PARALLAX-5/1.0",
  "certificate_id": "p5cert-0x4c4f4f5050494e47-2026-05-25",
  "protocol_id": "Looping Vault V2",
  "compliance_level": "P4",
  "artifacts": {
    "source_repo": "github.com/looping-finance/vault-v2",
    "commit_hash": "9a3f7c8d2e1b4a5f6d8e9c0a1b2c3d4e5f6a7b8c",
    "deployed_addresses": [
      { "chain_id": 1,    "address": "0x5e1b9a3f7c8d2e1b4a5f6d8e9c0a1b2c3d4f6a8b" },
      { "chain_id": 8453, "address": "0xa1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8d9ef" }
    ],
    "bytecode_hashes": {
      "ethereum":   "0x9b4f2c8d3e1a5b6f7c8d9e0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c",
      "base":       "0x9b4f2c8d3e1a5b6f7c8d9e0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c"
    }
  },
  "obligation_map": {
    "deposit(uint256,address)": ["A1", "A2", "A4"],
    "redeem(uint256,address,address)": ["A1", "A2", "A4"],
    "setFeeRecipient(address)": ["A2"],
    "harvest()": ["A1", "A4", "A5"]
  },
  "proof_artifacts": {
    "A1": {
      "tool": "halmos",
      "version": "0.3.3",
      "verdict": "PASS",
      "paths_explored": 47,
      "artifact_hash": "sha256:7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b"
    },
    "A2": {
      "tool": "Certora",
      "version": "7.10.0",
      "verdict": "PASS",
      "rule_id": "auth_admin_only",
      "artifact_hash": "sha256:1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e"
    },
    "A4": {
      "tool": "halmos",
      "version": "0.3.3",
      "verdict": "PASS",
      "paths_explored": 23,
      "artifact_hash": "sha256:5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f"
    },
    "A5": {
      "tool": "Lean4",
      "version": "4.10.0",
      "verdict": "PASS",
      "theorem_names": ["oracle_freshness_holds", "quorum_satisfied"],
      "artifact_hash": "sha256:9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d"
    }
  },
  "trust_base_assumptions": {
    "OA1_key_integrity": {
      "controls": ["multisig 4-of-7", "hardware-secured signers", "key rotation 6mo"],
      "auditor": "Halborn Hardware Audit 2026-04"
    },
    "OA2_signer_sovereignty": {
      "controls": ["signer training program", "jurisdictional separation", "intent-aware signing UI"]
    },
    "OA3_infrastructure_integrity": {
      "controls": ["3-of-5 oracle quorum", "independent RPC paths", "DNS DNSSEC"]
    }
  },
  "known_exclusions": [
    "delegatecall to external library X requires separate certificate",
    "front-running protection out of scope of this certificate"
  ],
  "revalidation_triggers": [
    "any commit to repo",
    "oracle provider change",
    "multisig signer change",
    "365 days elapsed"
  ],
  "issued_at": "2026-05-25T14:00:00Z",
  "expires_at": "2027-05-25T14:00:00Z",
  "issuer": {
    "name": "AquaUrsa Verification Lab",
    "did": "did:web:verify.aquaursa.ai",
    "signature": "0x8e9f0a1b2c3d4e5f00112233445566778899aabbccddeeff8e9f0a1b2c3d4e5f00112233445566778899aabbccddeeff8e9f0a1b2c3d4e5f0011"
  }
}
```

## Appendix B. JSON Schema (excerpt)

The complete JSON Schema for PARALLAX-5 certificates is at
`paper/supplement/parallax5_certificate.schema.json`. Key requirements:

- `schema_version`: literal "PARALLAX-5/1.0"
- `compliance_level`: enum {"P0", "P1", "P2", "P3", "P4", "P5"}
- `protocol_id`, `artifacts.source_repo`, `artifacts.commit_hash`,
  `artifacts.deployed_addresses` are required
- `obligation_map`: every value-affecting function MUST be present
- For P3+: every entry in `obligation_map` MUST have a corresponding
  entry in `proof_artifacts`
- For P5: certificate MUST include a `runtime_gate` block describing the
  deployed step-secure gate's address and configuration

## Appendix C. Minimal Conformance Tests

To claim PARALLAX-5 conformance at level $L$, an implementation MUST pass:

1. **Schema validation**: the certificate validates against the JSON Schema.
2. **Hash consistency**: deployed bytecode at every listed address hashes to
   the declared bytecode_hash for its chain.
3. **Artifact existence**: every artifact_hash referenced in proof_artifacts
   corresponds to a downloadable file whose SHA-256 matches.
4. **Tool replay (for L >= P2)**: re-running the listed tool against the
   referenced commit and configuration produces the asserted verdict.
5. **Falsification challenge**: no public basis counterexample has been
   submitted within 90 days of certificate issuance.
