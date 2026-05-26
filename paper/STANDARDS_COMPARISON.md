# PARALLAX-5 vs Existing Security Standards

PARALLAX-5 is designed to coordinate with, not displace, the existing smart-contract security standards ecosystem. This document maps each major standard onto the PARALLAX-5 obligation interface.

## "Why not just use OWASP SCSVS or EthTrust?"

The most important question, asked plainly.

| Standard | Checklist | Formal obligation mapping | Machine-readable certificate | Runtime gate | Agent safety |
|---|---|---|---|---|---|
| **OWASP SCSVS** | ✓ | partial | limited | — | — |
| **EEA EthTrust [S]/[M]/[Q]** | ✓ | partial | limited | — | — |
| **Trail of Bits / OZ / Consensys guidance** | partial (narrative) | partial | — | — | — |
| **Immunefi / Code4rena severity** | per-finding | — | per-finding | — | — |
| **PARALLAX-5** | ✓ | **✓** | **✓** | **✓** | **✓** |

PARALLAX-5 is the only standard that:
- Defines obligations at the *transition* level (not the contract level)
- Emits machine-readable certificates conforming to a Draft 2020-12 JSON Schema
- Specifies a deployable runtime enforcement option (P5)
- Specifies an AI-agent execution-gating model (case study 3 + 4)

Existing standards are *vertical* (per-contract checklists) or *horizontal* (per-finding narratives) or *transactional* (per-bug severity). PARALLAX-5 is *organizational* — the shared vocabulary above all three.

## Per-standard mapping

### EEA EthTrust Security Levels

EthTrust defines three trust levels:
- **[S] Security**: pass automated tools without unaddressed warnings.
- **[M] Mitigation**: known issues mitigated by design.
- **[Q] Quality assurance**: code review, no known vulnerabilities, tests pass.

PARALLAX-5 mapping:
- EthTrust [S] → **P2** (Statically Screened)
- EthTrust [M] → **P2 + documented exclusions in `known_exclusions`**
- EthTrust [Q] → **P3** (Symbolically Checked) if tests are symbolic; otherwise P2 with rich trust-base

An EthTrust [Q]-certified contract can issue a P3 PARALLAX-5 certificate by attaching the test outputs as `proof_artifacts`.

### OWASP SCSVS

SCSVS organizes controls into chapters (V1–V13). Each control clusters under PARALLAX-5 obligations:

| SCSVS chapter | Clusters under |
|---|---|
| V1 Architecture, design, threat modelling | structural — informs `trust_base_assumptions` |
| V2 Access control | **A2** |
| V3 Blockchain data | A1 (state integrity), A5 (oracle data) |
| V4 Communications | A3 (signatures), A5 (cross-chain) |
| V5 Arithmetic | **A1** |
| V6 Malicious input | A2, A4 |
| V7 Gas usage | A4 (DoS via gas) |
| V8 Components | trust-base (`known_exclusions`) |
| V9 Token issuance / supply | **A1** |
| V10 Centralization risk | OA1, OA2 trust-base |
| V11 Oracles | **A5** |
| V12 Cross-chain | **A5** (generalized) |
| V13 Operational considerations | OA1, OA2, OA3 trust-base |

A SCSVS-pinned audit naturally produces a P2 or P3 certificate by re-organizing findings under A1–A5.

### Trail of Bits / Consensys Diligence / OpenZeppelin

These firms produce narrative audit reports. The conversion to PARALLAX-5:

1. Every finding gets tagged with one or more of {A1, A2, A3, A4, A5}.
2. For every value-affecting function, list which findings were ruled out and at what tool level.
3. The aggregate level is the minimum across all functions: if any function is P1, the contract is P1.
4. Trust-base controls (OA1/OA2/OA3) come from the operational section of the audit.

A typical audit yields a P2 certificate; a Certora-augmented audit yields P3 or P4. See [paper/supplement/before_after/](supplement/before_after/) for a worked example.

### Bug bounty platform severity rubrics

Immunefi's tiers correspond roughly to:

| Severity | Obligation violation strength |
|---|---|
| Critical | Full A1 or A2 violation on a value-affecting function |
| High | Partial A1/A2/A4/A5 with material loss potential |
| Medium | Edge-case A4/A5 or recoverable A1 |
| Low | Best-practice / non-exploitable |

A P0–P3 PARALLAX-5 certificate identifies which obligations are NOT yet symbolically verified — a precise shopping list for bug hunters.

### NIST SP 800-zzz (draft DLT framework)

NIST is drafting a DLT security framework that aligns naturally with OA1/OA2/OA3 trust-base sections. PARALLAX-5's compliance ladder provides the per-protocol granularity NIST's framework lacks.

## Why PARALLAX-5 fits with all of them

PARALLAX-5 is the **per-obligation labeling layer** that existing standards lack. A protocol can simultaneously be:
- EthTrust [Q] certified
- SCSVS-aligned
- Audited by Trail of Bits
- Bounty-eligible on Immunefi
- And issue ONE PARALLAX-5 certificate that references all four as evidence.

The unification thesis made concrete: every existing standard maps in; no one is displaced.
