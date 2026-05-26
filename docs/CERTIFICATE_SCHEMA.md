# PARALLAX-5 Certificate Schema — RFC v1.0

**Document status:** Specification of the shared object emitted by the PARALLAX-5 substrate.
**Version:** 1.0
**License of this document:** CC0
**Companion documents:** `docs/CHARTER.md`, `docs/FORK_PROTOCOL.md`, `VISION_AND_ROADMAP_v2.0.md`
**Machine-readable schema:** `schemas/certificate_v1.json` (JSON Schema draft 2020-12)
**Parent project DOI:** 10.5281/zenodo.20386868

---

## Abstract

A PARALLAX-5 certificate is a structured, machine-checkable record of a value-bearing protocol's safety posture, expressed in terms of the five obligations (A1–A5), the CROPS dimension matrix, and a proof-depth scale. It is the *shared object* on which the seven-layer substrate architecture composes: auditors, formal-methods tools, insurers, wallets, agents, chains, and challengers all consume the certificate through a common schema.

This document specifies the schema, its lifecycle, conformance requirements for issuers and consumers, and the relationship between certificates and the on-chain registry. The companion `schemas/certificate_v1.json` is the authoritative machine-readable specification; this document is its human-readable explanation.

---

## 1. Status

This is RFC v1.0, the first proposed standard for the PARALLAX-5 certificate format. It is intended for public review. Substantive feedback should be submitted via the Falsification Challenge framework (Vision and Roadmap §11) or as issues against the canonical repository.

The specification is CC0; it may be forked under the Fork Protocol. Forks adopting modified schemas should follow Article 4 of the Fork Protocol regarding compatibility declarations.

---

## 2. Purpose

### 2.1 What a certificate is

A certificate is a record that:

- Identifies a specific protocol artifact (contract source or bytecode at a specific hash)
- Reports the obligations satisfied at specific evidence depths
- Cites the tool outputs, proofs, or attestations that constitute the evidence
- Names the calibration mapping used to translate raw findings into obligation/depth claims
- Declares the issuer's identity and signing key
- States the validity window and the events that would invalidate the certificate
- Is cryptographically fingerprinted so that any tampering is detectable

### 2.2 What a certificate is not

- It is **not** a guarantee that the protocol is bug-free. It states what has been checked, by what means, to what depth — and explicitly identifies what has not been checked.
- It is **not** an endorsement by AquaUrsa Research. AquaUrsa issues certificates under its own commercial mapping (`aquaursa-v1`); other parties may issue certificates under their own mappings.
- It is **not** a substitute for an audit. It is a structured object that can carry an audit's findings, but the audit itself remains valuable as the source of those findings.
- It is **not** static. The lifecycle (Section 5) specifies how certificates supersede, revoke, and respond to challenges.

### 2.3 Why a certificate

The substrate's value proposition rests on the existence of a shared object that every constituency in the adoption network (protocols, auditors, insurers, wallets, agents, chains) can consume. Without a shared object, every consumer must build its own interpretation layer. With a shared object, the consumers compose into an ecosystem.

---

## 3. Schema structure

A certificate is a JSON document with the following top-level fields. Field-by-field semantics in Section 4.

```json
{
  "schema_version": "parallax5-certificate-v1.0",
  "certificate_id": "uuid-v4-string",
  "protocol": { ... },
  "artifact": { ... },
  "deployment": [ ... ],
  "mapping": { ... },
  "trust_base": { ... },
  "obligation_coverage": { ... },
  "crops_vector": { ... },
  "walkaway": { ... },
  "evidence": [ ... ],
  "issuer": { ... },
  "issuance": { ... },
  "validity": { ... },
  "supersession": { ... } | null,
  "revocation": { ... } | null,
  "challenges": [ ... ],
  "fingerprint": "hex-string",
  "signature": "hex-string"
}
```

---

## 4. Field specifications

### 4.1 `schema_version` (string, required)

The schema version identifier. Initial value: `"parallax5-certificate-v1.0"`. Consumers should reject certificates whose `schema_version` they do not implement.

### 4.2 `certificate_id` (UUID v4 string, required)

A unique identifier assigned by the issuer. Used to refer to this specific certificate in supersession, revocation, and challenge events.

### 4.3 `protocol` (object, required)

Identifies the protocol being certified.

```json
{
  "name": "Uniswap V3 Core",
  "version": "1.0.0",
  "identifier": "https://github.com/Uniswap/v3-core",
  "category": "automated_market_maker"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| name | string | yes | Human-readable protocol name |
| version | string | yes | Protocol version |
| identifier | string | recommended | Stable URL or identifier |
| category | string | recommended | One of: amm, lending, bridge, governance, oracle, vault, agent, other |

### 4.4 `artifact` (object, required)

Identifies the specific code being certified.

```json
{
  "source_hash": "sha256:abc123...",
  "bytecode_hash": "sha256:def456...",
  "compiler": "solc-0.8.20",
  "compiler_settings": { "optimizer": { "enabled": true, "runs": 200 } }
}
```

The `source_hash` and `bytecode_hash` are required if available; one of the two MUST be present. Compiler version and settings are required for source-based certification to enable bytecode reproduction.

### 4.5 `deployment` (array of objects, optional)

If the certified artifact has been deployed on-chain, lists the deployments.

```json
[
  {
    "chain_id": 1,
    "chain_name": "ethereum-mainnet",
    "address": "0x...",
    "deployed_at_block": 18000000,
    "deployer": "0x..."
  }
]
```

If empty or absent, the certificate covers source/bytecode only.

### 4.6 `mapping` (object, required)

Names the calibration mapping under which findings were translated to obligations.

```json
{
  "namespace": "tool-mapping/aquaursa-v1",
  "version": "1.0.0",
  "doi": "10.5281/zenodo.XXXXX",
  "hash": "sha256:..."
}
```

The `namespace` is required (per Fork Protocol Article 3). The `doi` is required for any mapping deposited on Zenodo. The `hash` enables verification that the specific mapping version was used.

### 4.7 `trust_base` (object, required)

Explicit list of security interface assumptions on which the obligation claims rest. PARALLAX-5's conditional completeness theorems hold *under* the trust base; the trust base must be disclosed.

```json
{
  "ecdsa_euf_cma": true,
  "evm_yul_lean_refinement": true,
  "oracle_freshness_window_seconds": 600,
  "external_attestation_quorum": "5-of-9",
  "assumptions": [
    "Standard ERC-20 transfer semantics for collateral tokens",
    "Chainlink oracle aggregator integrity"
  ]
}
```

Consumers can reject the certificate if the trust base does not match their threat model.

### 4.8 `obligation_coverage` (object, required)

Per-obligation evidence depth on the original PARALLAX-5 scale (D0–D5).

```json
{
  "A1": { "depth": 4, "evidence_refs": ["evidence-001", "evidence-002"] },
  "A2": { "depth": 3, "evidence_refs": ["evidence-003"] },
  "A3": { "depth": 2, "evidence_refs": ["evidence-004"] },
  "A4": { "depth": 4, "evidence_refs": ["evidence-005"] },
  "A5": { "depth": 0, "evidence_refs": [] }
}
```

All five obligations must be present. Depth 0 with empty evidence refs is valid (and honest); it indicates that obligation was not addressed.

**Depth scale (per Vision and Roadmap §5 PARALLAX-CROPS)**:

| D | Label | Meaning |
|---|---|---|
| 0 | None | No coverage |
| 1 | Declared | Claim made in docs/comments; no machine evidence |
| 2 | Statically checked | Pattern detector flagged or absence-of-finding |
| 3 | Symbolically checked | Path-condition witness or refutation |
| 4 | Formally proved | Kernel-accepted theorem in a proof assistant |
| 5 | Runtime enforced | StepSecure gate actively checking the obligation at runtime |

D4 and D5 are complementary: a certificate may have D4 (proved) without D5 (enforced), or D5 without D4 (a runtime gate without a formal proof of its correctness), or both. They are reported as separate dimensions; this field reports the maximum depth achieved, and the `enforcement_mode` field below disambiguates.

### 4.9 `crops_vector` (object, required)

The CROPS-dimension rating. Each dimension is rated 0–5 on the same depth scale, computed from the per-obligation findings filtered through the dimensional projection (see Section 6).

```json
{
  "C": 3,
  "R": 5,
  "O": 5,
  "P": 2,
  "S": 4,
  "computation_method": "max_within_dimension"
}
```

| Symbol | Dimension |
|---|---|
| C | Censorship-resistance |
| R | Capture-resistance / Walkaway |
| O | Openness |
| P | Privacy |
| S | Security (the original A1–A5 aggregate) |

### 4.10 `walkaway` (object, required)

The protocol's walkaway classification per the Walkaway Theorem.

```json
{
  "classification": "full",
  "proof_ref": "evidence-006",
  "explanation": "Contract is deployed without admin keys, proxy patterns, or governance hooks. The walkaway test holds trivially.",
  "dependencies_disclosed": []
}
```

Classifications: `full` / `bounded` / `partial` / `centralized` / `fake`. The `fake` classification is reserved for protocols that *claim* walkaway but have hidden off-chain dependencies; only third-party challengers should issue `fake` classifications.

### 4.11 `evidence` (array of objects, required)

The audit trail. Each evidence object documents one source of one finding.

```json
[
  {
    "evidence_id": "evidence-001",
    "tool": "slither",
    "tool_version": "0.10.4",
    "finding_id": "reentrancy-eth",
    "obligation_mapped_to": "A4",
    "depth_contribution": 2,
    "raw_finding": { ... },
    "justification": "Slither's reentrancy-eth detector triggered on withdraw()..."
  },
  {
    "evidence_id": "evidence-005",
    "tool": "halmos",
    "tool_version": "0.2.x",
    "finding_id": "invariant-violated",
    "obligation_mapped_to": "A4",
    "depth_contribution": 4,
    "property_checked": "nonReentrant invariant on all external entry points",
    "result": "passed",
    "justification": "Halmos verified the nonReentrant invariant holds across all symbolic execution paths within the bound."
  }
]
```

Evidence entries are referenced from `obligation_coverage` by `evidence_id`. Every non-zero depth in `obligation_coverage` MUST have at least one corresponding evidence entry. Evidence entries MUST cite the calibration mapping (via the certificate's top-level `mapping` field) under which the finding was translated.

### 4.12 `issuer` (object, required)

The party issuing the certificate.

```json
{
  "name": "AquaUrsa Research",
  "identifier": "https://parallax.xyz",
  "public_key": "ed25519:6698bfea91e1827955191845c5a8c61b50f9b6cb209805374fb24d7a0d64dd3c",
  "registry_address": "0x..."
}
```

The `public_key` is the Ed25519 public key whose corresponding private key signed the certificate. The `registry_address` is the Ethereum address used by the issuer when registering certificates on-chain (may differ from the signing key).

### 4.13 `issuance` (object, required)

```json
{
  "timestamp": "2026-05-26T10:30:00Z",
  "issuance_method": "automated_pipeline",
  "human_review": false,
  "notes": ""
}
```

`issuance_method` values: `automated_pipeline`, `automated_with_review`, `human_audit`, `hybrid`.

### 4.14 `validity` (object, required)

```json
{
  "valid_from": "2026-05-26T10:30:00Z",
  "valid_until": "2026-11-26T10:30:00Z",
  "revalidation_triggers": [
    "contract_upgrade",
    "compiler_change",
    "dependency_update",
    "external_assumption_change"
  ]
}
```

A certificate without an explicit `valid_until` defaults to 180 days from `valid_from`. Revalidation triggers are events that, if they occur, invalidate the certificate before its natural expiry — they must be enumerated explicitly.

### 4.15 `supersession` (object or null, required field)

If the certificate has been superseded by a newer certificate, this records the supersession.

```json
{
  "superseded_by": "uuid-of-new-certificate",
  "superseded_at": "2026-06-15T14:00:00Z",
  "reason": "Contract upgraded to v1.1; new certificate issued."
}
```

When absent, the field is explicitly `null`.

### 4.16 `revocation` (object or null, required field)

If the issuer has revoked the certificate (without supersession), this records the revocation.

```json
{
  "revoked_at": "2026-06-15T14:00:00Z",
  "revoked_by": "issuer_pubkey_signing",
  "reason": "Identified flaw in mapping calibration; revoking pending recalibration."
}
```

When absent, explicitly `null`.

### 4.17 `challenges` (array, required field — may be empty)

Records of Falsification Challenge events. Initially empty for a newly-issued certificate.

```json
[
  {
    "challenge_id": "challenge-001",
    "challenger_pubkey": "ed25519:...",
    "challenge_type": "wrong_mapping",
    "submitted_at": "2026-06-01T09:00:00Z",
    "evidence_ref": "https://...",
    "resolution": {
      "resolved_at": "2026-06-10T11:00:00Z",
      "outcome": "upheld",
      "consequence": "supersession_issued"
    }
  }
]
```

`challenge_type` values match the six types in Vision and Roadmap §11 (Move 11):
- `basis_counterexample`
- `wrong_mapping`
- `invalid_certificate`
- `stale_proof`
- `unsound_monitor`
- `wrong_walkaway_classification`

### 4.18 `fingerprint` (hex string, required)

SHA-256 over the canonical JSON serialization of all fields except `signature`. Computed using the canonical form specified in Section 7.

### 4.19 `signature` (hex string, required)

Ed25519 signature over the `fingerprint` using the issuer's signing key. The corresponding public key MUST match `issuer.public_key`.

---

## 5. Lifecycle

A certificate moves through the following states.

```
                    [Issued]
                       │
            ┌──────────┼──────────────┐
            │          │              │
            ▼          ▼              ▼
       [Challenged] [Valid]    [Superseded]
            │          │              │
            ▼          ▼              │
       [Resolved] [Expired]           │
            │                          │
            └─────► [Revoked] ◄────────┘
```

### 5.1 State definitions

- **Issued**: certificate created, signed, optionally registered on-chain. Initial state.
- **Valid**: within validity window, no active challenges, not superseded or revoked. Consumable.
- **Challenged**: at least one open Falsification Challenge. Consumers should treat with caution but may still consume; the challenge metadata is available.
- **Resolved**: a prior challenge has been resolved (upheld, rejected, or partial). The certificate may continue in Valid state or transition to Superseded or Revoked depending on resolution.
- **Expired**: `valid_until` has passed. Consumers should treat as informational only, not actionable.
- **Superseded**: a newer certificate covers the same artifact. The superseding certificate is the authoritative one.
- **Revoked**: explicitly revoked by the issuer without a superseding certificate. Consumers should not act on the certificate.

### 5.2 State transitions

Recorded as on-chain registry events (per Vision and Roadmap §2.4 Layer 4):

| Event | Trigger |
|---|---|
| `Registered` | Issuance + on-chain submission |
| `Superseded` | New certificate issued covering same artifact |
| `RevokedByIssuer` | Issuer explicitly revokes |
| `Challenged` | Falsification challenge submitted |
| `Resolved` | Challenge resolved (any outcome) |
| `MappingRegistered` | New calibration namespace registered |

---

## 6. CROPS vector computation

The CROPS vector is computed from the per-obligation coverage using the dimensional projection:

For each CROPS dimension D ∈ {C, R, O, P, S}, define a set of obligation-relevance weights: an obligation either does or does not contribute to a CROPS dimension. The dimensional projection is:

```
crops_vector[D] = max{ obligation_coverage[A_i].depth : A_i contributes to D }
```

The contribution matrix (which obligations contribute to which dimensions) is specified in the companion `docs/CROPS_VECTOR.md` and is summarized below:

| Obligation | C | R | O | P | S |
|---|:---:|:---:|:---:|:---:|:---:|
| A1 Conservation | ✓ | — | — | — | ✓ |
| A2 Authorization | — | ✓ | — | — | ✓ |
| A3 Signature | — | — | — | ✓ | ✓ |
| A4 Temporal | ✓ | — | — | — | ✓ |
| A5 Attestation | ✓ | — | ✓ | — | ✓ |
| (Walkaway derived) | — | ✓ | — | — | — |
| (Source openness) | — | — | ✓ | — | — |
| (Privacy primitives) | — | — | — | ✓ | — |

The S column simply re-aggregates A1–A5 at maximum depth. C, R, O, P add dimensional structure beyond security. The full matrix is given in `docs/CROPS_VECTOR.md`.

---

## 7. Canonical serialization

For deterministic fingerprinting, certificates are canonicalized before hashing:

1. All keys in objects are sorted lexicographically (UTF-8 code-point order)
2. Whitespace between tokens is removed (no spaces, no newlines, no tabs)
3. Numeric values are serialized in their shortest unambiguous form
4. String values are UTF-8 encoded with standard JSON escaping
5. The `signature` field is excluded from canonicalization
6. The `fingerprint` field is excluded from canonicalization (it is the result)

Reference implementation: the `parallax5_coordinator.certifier.Certificate.fingerprint()` method in the canonical Python package implements this scheme.

---

## 8. Conformance requirements

### 8.1 Issuer conformance

An issuer claiming to produce PARALLAX-5 v1.0 certificates MUST:

1. Produce certificates that validate against `schemas/certificate_v1.json`
2. Compute `fingerprint` using the canonical serialization (Section 7)
3. Sign `fingerprint` with the Ed25519 key whose public form appears in `issuer.public_key`
4. Cite the specific mapping namespace and version used
5. Enumerate the trust base completely; not list `assumptions` as "none"
6. Provide evidence entries for every non-zero obligation depth claim
7. Set `valid_until` explicitly OR accept the 180-day default
8. Enumerate revalidation triggers

### 8.2 Validator conformance

A validator (party checking a certificate) MUST:

1. Reject certificates whose `schema_version` is not implemented
2. Verify the `signature` against `issuer.public_key`
3. Recompute the `fingerprint` and verify it matches
4. Check the validity window (current time within `valid_from` to `valid_until`)
5. Check supersession and revocation state (via registry if available)
6. Verify the named mapping is available and matches the cited hash
7. Surface the trust base to the human consumer; do not silently accept unstated assumptions
8. Treat `walkaway: fake` as a strong negative signal

### 8.3 Consumer conformance

A consumer (party making a decision based on a certificate) MUST be informed of:

1. The validity state (current, expired, superseded, revoked)
2. Active challenges
3. The trust base
4. The CROPS vector (not just an aggregate score)
5. The walkaway classification

Consumers MAY make their own policy decisions about which mappings to trust, which trust bases to accept, and which CROPS dimensions are required for their use case.

---

## 9. Worked example

The full worked example is provided in `examples/certificate_uniswap_v3_core.json`. Summary:

```json
{
  "schema_version": "parallax5-certificate-v1.0",
  "certificate_id": "c1234567-89ab-cdef-0123-456789abcdef",
  "protocol": {
    "name": "Uniswap V3 Core",
    "version": "1.0.0",
    "identifier": "https://github.com/Uniswap/v3-core",
    "category": "amm"
  },
  "artifact": {
    "source_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "bytecode_hash": "sha256:..."
  },
  "mapping": {
    "namespace": "tool-mapping/aquaursa-v1",
    "version": "1.0.0",
    "doi": "10.5281/zenodo.20386868"
  },
  "obligation_coverage": {
    "A1": { "depth": 4, "evidence_refs": ["e-001"] },
    "A2": { "depth": 5, "evidence_refs": ["e-002"] },
    "A3": { "depth": 0, "evidence_refs": [] },
    "A4": { "depth": 4, "evidence_refs": ["e-003"] },
    "A5": { "depth": 0, "evidence_refs": [] }
  },
  "crops_vector": { "C": 4, "R": 5, "O": 5, "P": 0, "S": 5 },
  "walkaway": {
    "classification": "full",
    "explanation": "No admin keys, no proxy patterns, no governance hooks."
  },
  "..." : "abbreviated"
}
```

The example illustrates:
- A protocol with strong S (security) and R (capture-resistance) but P=0 (no privacy claims)
- A walkaway: full classification with formal proof
- Honest reporting of A3=0, A5=0 (not addressed in this scope)
- Citation of the canonical aquaursa-v1 mapping

---

## 10. Open questions

For RFC discussion:

1. Should `crops_vector` be required or optional? Currently required; some have argued optional for backward compatibility with the original P-level model.
2. Should `walkaway` have a sub-spectrum for the "partial" classification (e.g., partial-low, partial-high)?
3. Should `evidence` entries be required to include the raw tool output, or only a reference?
4. Should the schema support multi-protocol certificates (e.g., a bridge that spans Ethereum and another chain)?
5. Should `challenges` be in-band (in the certificate itself) or out-of-band (only in registry)?

These questions are open for resolution in v1.1 based on community feedback.

---

## 11. Citation

```bibtex
@misc{duncan2026parallax5certschema,
  author    = {{AquaUrsa Research}},
  title     = {{PARALLAX-5 Certificate Schema RFC v1.0}},
  year      = {2026},
  version   = {1.0},
  publisher = {AquaUrsa Research},
  license   = {CC0},
  url       = {https://parallax.xyz/certificate-schema}
}
```

---

**End of RFC.**

This document is CC0. Fork it. Improve it. The machine-readable schema in `schemas/certificate_v1.json` is the authoritative artifact.
