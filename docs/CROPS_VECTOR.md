# CROPS Vector Note

**Document version:** 1.0
**License:** CC0
**Companion to:** `src/parallax5_coordinator/crops.py`, `lean/Parallax5/Walkaway.lean`
**Parent project DOI:** 10.5281/zenodo.20386868

---

## Abstract

The original PARALLAX-5 substrate reports a single scalar compliance level (P0–P5) computed from the maximum evidence depth across the five obligations A1–A5. This is operationally convenient but collapses four orthogonal trust dimensions into one number. The CROPS Vector replaces the scalar with a five-component vector aligned with the Ethereum Foundation's CROPS framework (Censorship-resistance, capture-Resistance, Openness, Privacy, Security), extending the substrate from a security-only frame to a complete trust-surface frame.

This note specifies the obligation-to-dimension projection matrix, the depth computation rule, the relationship between CROPS dimensions and existing PARALLAX-5 primitives (Walkaway, basis-observability), and the conformance requirements for certificate issuers and consumers.

---

## 1. The five dimensions

| Symbol | Dimension | What it measures |
|---|---|---|
| **C** | Censorship-resistance | No on-chain entity can prevent the protocol from operating as specified |
| **R** | capture-Resistance / Walkaway | No off-chain entity can divert or pause the protocol; the protocol survives founder disappearance |
| **O** | Openness | Source available, building blocks reusable, dependencies open |
| **P** | Privacy | Transaction privacy, identity protection, selective disclosure supported |
| **S** | Security | The five obligations A1–A5 hold at evidence depths |

A complete CROPS rating is a vector `(C, R, O, P, S)` where each component is on the D0–D5 evidence-depth scale.

### 1.1 Worked example

A typical Uniswap V3-class AMM:
```
(C=4, R=5, O=5, P=0, S=5)
```

- C=4: censorship-resistance is high (no per-transaction admin gating) but not 5 (block-builder MEV exposure remains)
- R=5: full walkaway (no admin role at all)
- O=5: source open, dependencies open, build reproducible
- P=0: no privacy primitives — transactions are public by design
- S=5: all five obligations formally proved

This protocol is excellent on C, R, O, S; it makes no privacy claims. The vector makes this explicit. A privacy-seeking user would not be misled by a single high P-level; they would see P=0 and route to a privacy-focused protocol.

### 1.2 Why a vector beats a scalar

A protocol with `(C=5, R=5, O=5, P=2, S=2)` and one with `(C=2, R=2, O=2, P=5, S=5)` have wildly different trust profiles, but both might compress to "P3" under a scalar averaging scheme. The vector preserves the structure that matters for consumers' decisions.

---

## 2. The contribution matrix

Each PARALLAX-5 obligation contributes to one or more CROPS dimensions. The contribution matrix is the formal projection.

| Obligation | C | R | O | P | S |
|---|:---:|:---:|:---:|:---:|:---:|
| **A1** Value conservation | ✓ | — | — | — | ✓ |
| **A2** Authorization closure | — | ✓ | — | — | ✓ |
| **A3** Signature integrity | — | — | — | ✓ | ✓ |
| **A4** Temporal distinctness | ✓ | — | — | — | ✓ |
| **A5** External-attestation trust | ✓ | — | ✓ | — | ✓ |
| (derived) Walkaway classification | — | ✓ | — | — | — |
| (derived) Source openness | — | — | ✓ | — | — |
| (derived) Privacy primitives | — | — | — | ✓ | — |

### 2.1 Justifications per cell

**A1 → C, S**:
- *C (censorship-resistance)*: value conservation prevents specific actors from siphoning value as a means of de facto censorship (the protocol cannot be selectively starved).
- *S (security)*: A1 is the foundational security obligation.

**A2 → R, S**:
- *R (capture-resistance)*: authorization closure prevents unauthorized principals from gaining control; it is the obligation most directly aligned with the walkaway property.
- *S*: standard security.

**A3 → S** (v1.0.1 refinement):
- *S*: standard security. Signature integrity prevents replay and message-authentication failures.
- *Note*: An earlier version of this matrix mapped A3 to {P, S}. The privacy contribution was removed in v1.0.1 after external review observed that signature malleability is primarily an integrity/replay/canonicalization issue. The privacy-adjacent consequence (cross-message identity correlation by an attacker) is real but conditional on the protocol making an explicit privacy claim via signature canonicalization (ring signatures, blinded signatures). Honest CROPS reporting requires that privacy contributions flow from explicit privacy primitives declared in the spec rather than from incidental properties of A3 evidence. Protocols whose A3 enforcement is part of a privacy-primitive design should declare `privacy_primitives_depth` accordingly.

**A4 → C, S**:
- *C*: temporal distinctness prevents reentrancy and stale-read attacks that can be used to selectively favor or harm specific users (a censorship vector).
- *S*: standard security.

**A5 → C, O, S**:
- *C*: external attestation freshness prevents oracle-controlled censorship of specific users or markets.
- *O*: external attestation transparency is a form of openness (which oracles are trusted, what their refresh schedule is, what their failure modes are).
- *S*: standard security.

**Derived obligations** (Walkaway, Openness, Privacy):
- The Walkaway classification (from the Walkaway Theorem) contributes exclusively to R.
- Source openness (open-source verification, build reproducibility) contributes exclusively to O.
- Privacy primitives (ZK proofs, selective disclosure, mixers) contribute exclusively to P.

### 2.2 Why this matrix and not another

The matrix is intentionally **sparse and conservative**. We claim a contribution only where the relationship is direct and defensible. Cells marked `—` are not asserting that the obligation is irrelevant to the dimension; rather, they assert that the contribution is too indirect to justify aggregation under that dimension.

For example, one could argue that A1 contributes to R (capture-resistance) because value-conservation prevents an attacker who has captured admin rights from extracting unbounded value. This argument is true but indirect — the proper capture-resistance dimension is dominated by the Walkaway-derived signal, and including A1 in R would inflate R-scores for protocols with strong conservation but weak walkaway.

When in doubt, the matrix omits the contribution. Honesty over completeness.

---

## 3. Depth computation

For each CROPS dimension D, the depth is computed by `max_within_dimension`:

$$\text{crops\_vector}[D] = \max\{ \text{obligation\_coverage}[A_i].\text{depth} : A_i \in \text{contributes\_to}(D) \}$$

### 3.1 Why max and not min/average

Three alternatives were considered:

- **Min within dimension**: weakest-link computation. Rejected because it punishes broad coverage. If A1 has depth 5 and A4 has depth 0, taking min(5,0)=0 for C tells consumers "C is zero" when the truth is "C is partially established at depth 5 from A1 alone, with A4 contribution missing."
- **Weighted average**: more honest in principle, but the weights are subjective. Open standards should not embed contentious calibration parameters.
- **Max within dimension**: chosen. Reports the strongest contribution. Honest if the consumer knows the matrix (which they do — it's published). A consumer who needs all-A_i-contributing-to-C at depth ≥ k can compute this from the per-obligation coverage; the CROPS-vector is the executive summary.

The certificate's `crops_vector.computation_method` field records `"max_within_dimension"` as the standard choice. Alternative methods may be used but must be declared.

### 3.2 The S column

The S column simply re-aggregates A1–A5 at maximum depth:

$$\text{crops\_vector}[S] = \max_{i \in 1..5} \text{obligation\_coverage}[A_i].\text{depth}$$

This is the same number as the original PARALLAX-5 P-level. The S column ensures backward compatibility: any consumer that ignores C, R, O, P and reads only S gets the same scalar the v1.0 substrate produced.

### 3.3 The R column and Walkaway

The R column is computed from A2's depth AND the walkaway classification:

$$\text{crops\_vector}[R] = \max(\text{obligation\_coverage}[A2].\text{depth}, \text{walkaway\_depth})$$

where `walkaway_depth` maps the classification to a depth:

| Walkaway class | walkaway_depth |
|---|:---:|
| full | 5 |
| bounded | 4 |
| partial | 3 |
| centralized | 1 |
| fake | 0 |

This is the formal expression of "walkaway is the capture-resistance dimension."

---

## 4. Proof-depth modes (D0–D5)

The depth scale was originally a security-oriented "how strongly verified" scale. With the addition of runtime gates as Layer 6 of the substrate architecture, the scale gains a sixth level:

| D | Label | Meaning |
|---|---|---|
| 0 | None | No coverage |
| 1 | Declared | Claim made in docs/comments; no machine evidence |
| 2 | Statically checked | Pattern detector flagged or absence-of-finding |
| 3 | Symbolically checked | Path-condition witness or refutation |
| 4 | Formally proved | Kernel-accepted theorem in a proof assistant |
| 5 | Runtime enforced | StepSecure gate actively checking the obligation at runtime |

### 4.1 D4 and D5 are complementary, not ordered

A common misreading is that D5 (runtime enforced) is "stronger" than D4 (formally proved). The truth is more nuanced:

- **D4 (formal proof)**: establishes that the obligation cannot be violated by *correct* code under the stated trust base. Useful if the trust base is sound. Has no recourse if a flaw is later found in the proof itself or in the trust base.
- **D5 (runtime enforcement)**: actively checks at runtime; rejects bad transitions. Useful even when the proof is incomplete or the trust base is uncertain. Has computational cost; can be bypassed if the gate itself is incorrectly placed.

A certificate may have D4 without D5 (proved but not enforced), D5 without D4 (enforced without formal proof), or both. The certificate's `enforcement_mode` field per obligation disambiguates:

```json
"obligation_coverage": {
  "A2": {
    "depth": 5,
    "enforcement_mode": "gated",
    "evidence_refs": ["evidence-003"]
  }
}
```

`enforcement_mode` values:
- `passive`: certificate documents the depth claim only
- `monitored`: runtime observability without enforcement
- `gated`: D5 enforcement; transitions violating the obligation are rejected

### 4.2 Composition rule

When an obligation has both formal proof and runtime enforcement, the depth reports the higher (D5), and the enforcement_mode is `gated`. Consumers should treat D5+gated as the strongest assurance available.

When only one is present, the depth reflects what is present (D4 + passive, or D5 + gated without formal proof).

---

## 5. The honesty of explicit nulls

A protocol that does not address privacy receives **P=0**, not "P=not assessed" or "P=N/A". This is intentional.

A consumer making decisions on the basis of certificates needs to know: *did this protocol claim privacy and fail to deliver, or did it not address privacy at all*? The answer is the same from the consumer's perspective: **the protocol provides no privacy assurance**. Whether the absence is by choice or by oversight is the issuer's problem to explain in the certificate metadata.

The substrate is structurally honest about absence. P=0 is a valid CROPS-vector component and should be reported plainly.

---

## 6. CROPS-vector use cases

### 6.1 Consumer-side policy

A consumer can declare a CROPS-vector policy:

```yaml
required_minimums:
  C: 3   # require at least depth-3 censorship-resistance
  R: 4   # require strong capture-resistance
  O: 3   # require at least statically-checked openness
  S: 4   # require formal-proof security
  # P: not required — privacy is optional for this use case
```

The CLI's planned `parallax5 check --policy policy.yaml certificate.json` (forthcoming) returns success only if every component of the certificate's CROPS vector meets or exceeds the policy minimum.

### 6.2 Insurer-side risk pricing

An insurer's pricing model can be expressed as a function of the CROPS vector:

```
premium = base_rate × risk_multiplier(C, R, O, P, S)
```

Different insurance products price different dimensions differently. A custody-focused insurer cares most about R and S. A privacy-focused insurer cares most about P. The CROPS vector provides the input.

### 6.3 Wallet / agent runtime decisions

A wallet showing a transaction confirmation can surface the destination protocol's CROPS vector:

```
You are interacting with: Uniswap V3 Core
Trust profile:  C=4 R=5 O=5 P=0 S=5
                ^^^^^^^^^^^^^^^^^^^
                Strong on security and capture-resistance.
                NO PRIVACY: this transaction is public.
```

This is the runtime-consumption pattern that the wallet integration goal (Vision and Roadmap §9.9) operationalizes.

---

## 7. Relationship to existing PARALLAX-5 primitives

| PARALLAX-5 primitive | CROPS dimension |
|---|---|
| A1 conservation | C, S |
| A2 authorization | R, S |
| A3 signature (v1.0.1) | S |
| A4 temporal | C, S |
| A5 attestation | C, O, S |
| StepSecure gate | D5 enforcement mode for any obligation |
| Walkaway theorem | R |
| Source openness (derived) | O |
| Privacy primitives (derived) | P (sole source) |
| Basis-observability boundary | bounded by what the certificate cannot claim |
| Conditional completeness | the trust base on which all CROPS claims rest |

The CROPS extension does not replace the existing primitives; it organizes them.

---

## 8. Forward compatibility

The CROPS vector is a strict superset of the v1.0 P-level: any v1.0 certificate's P-level equals the new vector's `S` component. Consumers of older certificates can ignore C, R, O, P and read S only without loss of correctness.

Forward compatibility is required by the Certificate Schema RFC (Section 4.9). A certificate issuer who chooses not to assess C, R, O, P may report them as 0 — the certificate remains valid; the consumer is informed of the absence.

---

## 9. Open questions

For RFC discussion in v1.1:

1. **Should the matrix be more fine-grained?** Each cell currently is a binary contribution; a weighted contribution scheme would allow finer aggregation but introduces calibration parameters.
2. **Should there be derived obligations beyond the three currently listed?** Possible candidates: governance-process integrity, MEV-resistance, oracle-decentralization.
3. **Should P (privacy) be split into transaction-privacy, identity-privacy, metadata-privacy?**
4. **Should the depth scale extend to D6 (formally proved AND runtime enforced AND empirically tested)?**

These questions are open and welcome adversarial input.

---

## 10. Citation

```bibtex
@misc{duncan2026cropsvector,
  author    = {{AquaUrsa Research}},
  title     = {{CROPS Vector: Multi-Dimensional Trust-Surface Rating in PARALLAX-5}},
  year      = {2026},
  version   = {1.0},
  publisher = {AquaUrsa Research},
  license   = {CC0},
  url       = {https://parallax.xyz/crops-vector}
}
```

---

**End of note.**

This document is CC0. The implementation in `src/parallax5_coordinator/crops.py` is Apache-2.0.
