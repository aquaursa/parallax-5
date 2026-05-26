# Fork Protocol — PARALLAX-5

**Document status:** Companion to the Non-Capturability Charter; defines the operational procedure for forking the substrate.
**Version:** 1.0
**License of this document:** CC0
**Parent project DOI:** 10.5281/zenodo.20386868

---

## Preamble

The Non-Capturability Charter commits PARALLAX-5 to non-capturable governance. This Fork Protocol is the operational mechanism that makes that commitment real: anyone, at any time, for any reason, may fork the substrate. This document specifies how to do so cleanly — preserving compatibility where possible, avoiding name confusion, and contributing to a healthy plural ecosystem rather than a fragmented one.

A fork is not a hostile act. It is the substrate's primary mechanism for self-correction. The Charter prohibits AquaUrsa from contesting derivative variants; this Protocol gives forkers a clear path so the resulting ecosystem remains navigable.

---

## Article 1 — Scope

**1.1** This Protocol applies to forks of any of the following:

- The standard text (specification documents)
- The TOOL-MAPPING calibration namespace
- The certificate schema
- The reference implementation
- The on-chain registry interface
- The Lean 4 theorem files

**1.2** The Protocol does not require permission to fork; it merely documents best practice. Parties may deviate from this Protocol without legal consequence. Deviation, however, may make the fork harder to integrate into the broader ecosystem.

---

## Article 2 — Types of fork

Four distinct fork patterns are recognized, with different requirements.

### 2.1 Calibration fork (the most common case)

A party publishes an alternative TOOL-MAPPING calibration. The substrate's vocabulary, schema, and theorems are unchanged; only the depth values, justifications, or finding identifiers differ.

**Requirements**: minimal. Publish under a distinguishing namespace (e.g., `tool-mapping/trailofbits-v1`, `tool-mapping/certora-v1`, `tool-mapping/community-v1`). Cite the parent specification. Deposit on Zenodo with a fresh DOI.

**Example**: a security firm publishes its own mapping table reflecting its detector calibration, distinct from AquaUrsa's.

### 2.2 Extension fork

A party publishes an extension that adds new obligations, dimensions, or proof-depth levels while preserving the substrate's existing definitions. The fork is a strict superset.

**Requirements**: name the extension distinctively (e.g., `PARALLAX-5-Privacy-Extended-v1`). Cite the parent specification. Demonstrate that existing certificates remain valid under the extension (forward-compatibility proof). Deposit on Zenodo.

**Example**: a research group proposes a sixth obligation A6 (governance-process integrity) and publishes the extended taxonomy.

### 2.3 Refinement fork

A party publishes a refinement that modifies existing definitions, theorems, or schema fields — diverging from the parent in non-trivial ways.

**Requirements**: name distinctively (e.g., `PARALLAX-Strict-v1`, `PARALLAX-Mobile-v1`). Document the divergence explicitly: what changed, why, and what compatibility implications follow. Provide a translation guide from parent certificates to fork certificates where possible. Deposit on Zenodo.

**Example**: a project finds the existing A4 (temporal distinctness) definition too permissive for their domain and publishes a stricter variant.

### 2.4 Independent reformulation

A party publishes a verification substrate that does not claim continuity with PARALLAX-5 but acknowledges the prior art.

**Requirements**: use a distinct name (not "PARALLAX-*"). Cite PARALLAX-5 as related work where appropriate. No further obligations under this Protocol.

**Example**: a separate team builds a similar substrate for a non-EVM ecosystem and publishes under their own name.

---

## Article 3 — Naming

**3.1** To preserve a navigable ecosystem, forks should use names that:

- Distinguish the fork from the canonical release
- Indicate the relationship to the parent (where the fork claims one)
- Are stable: future versions of the same fork should follow the same naming pattern (e.g., `trailofbits-v1`, `trailofbits-v2`)

**3.2** AquaUrsa Research's own work is published under namespaces clearly identifying AquaUrsa (e.g., `tool-mapping/aquaursa-v1`, `certificate-issuer/aquaursa`). AquaUrsa does not claim the unqualified names "PARALLAX-5", "PARALLAX", or "TOOL-MAPPING" as exclusive.

**3.3** The unqualified name "PARALLAX-5" refers to the substrate as a whole — the vocabulary, taxonomy, schemas, and verification primitives. It is a name in the public domain and may be referenced by anyone in connection with substrate-compliant work, but should not be used as if it were a trademark or certification mark.

**3.4** Confusion avoidance: forkers are encouraged to choose names that minimize confusion. Names that imply official endorsement, primacy, or certification by AquaUrsa or any other party should be avoided.

---

## Article 4 — Compatibility

**4.1 Schema compatibility levels.** Certificates issued under a fork should declare their compatibility relationship with the parent:

- **`strict`**: every field has identical semantics; the fork certificate is interchangeable with a parent certificate
- **`additive`**: all parent fields preserved; the fork adds new fields that parent consumers should ignore
- **`semantic-divergence`**: at least one parent field has different semantics; parent consumers should not interpret the certificate without understanding the divergence
- **`independent`**: no compatibility claim

**4.2 Implementation compatibility.** Reference-implementation forks should:

- Preserve the parent's CLI surface where possible
- Document any deviation
- Provide a migration script for parent users where feasible

**4.3 No claim of compatibility implies compatibility.** Forks must explicitly declare their compatibility level. Absence of declaration is treated as `semantic-divergence`.

---

## Article 5 — Citation

**5.1** Forks that claim derivation from PARALLAX-5 should cite the parent. The minimum citation is:

```bibtex
@misc{duncan2026parallax5verification,
  author    = {{AquaUrsa Research}},
  title     = {{PARALLAX-5 / EVMYulLean Integration Verification}},
  year      = {2026},
  doi       = {10.5281/zenodo.20386868},
  publisher = {Zenodo}
}
```

**5.2** Forks of subsequent PARALLAX-5 components (Walkaway, CROPS, certificate schema, etc.) should cite the specific component's DOI in addition to the parent.

**5.3** Citation is a convention, not a legal requirement. The standard text is CC0 and may be used without attribution. Citation is preferred because it allows ecosystem participants to trace lineage, but it is not enforced.

---

## Article 6 — Deposit and discoverability

**6.1** Forks should be deposited on a permanent archival platform with a stable identifier. Recommended platforms:

- Zenodo (DOI assignment, indexed in academic databases)
- Software Heritage (SWHID, indexed for long-term preservation)
- ArXiv (for theoretical extensions; assigns arxiv IDs)
- OSF (for empirical extensions)

**6.2** The deposit should include:

- The fork's full specification or implementation
- A README explaining the fork's purpose, type (per Article 2), and compatibility level (per Article 4)
- A clear license declaration
- Citation of the parent

**6.3** Forks may optionally be registered in a community-maintained index of PARALLAX-5 derivatives. No such index is operated by AquaUrsa; ecosystem participants may establish their own.

---

## Article 7 — Conflicts and disputes

**7.1 No central authority.** No party has authority to declare a fork "valid" or "invalid". Adoption is determined by users of the substrate, not by AquaUrsa or any other party.

**7.2 Adversarial review.** Forks claiming compatibility may be challenged through the Falsification Challenge framework (Vision and Roadmap §11, Move 11). A successful challenge demonstrates that the fork's claimed compatibility does not hold; the resolution is recorded publicly. Forks may then update their compatibility claim.

**7.3 Name confusion.** If two forks adopt confusingly similar names, the convention is that priority goes to the earlier deposit (by Zenodo DOI timestamp). Later parties are encouraged but not required to disambiguate.

**7.4 No enforcement.** There is no enforcement mechanism for this Protocol. Compliance is voluntary. Adopters of the substrate are responsible for evaluating forks on their own merits.

---

## Article 8 — Pull-back to canonical

**8.1** A fork may, with the consent of its authors, be incorporated back into the canonical AquaUrsa release. This requires:

- Pull request to the relevant repository
- Compatibility check against the existing canonical specification
- Review by AquaUrsa Research (or the then-current maintainer)
- Public discussion period

**8.2** AquaUrsa Research is not obligated to accept any specific contribution. Rejection of a pull-back does not invalidate the fork; the fork continues to exist independently.

**8.3** Pull-back is at the discretion of the fork's authors. A fork does not become "less valid" by remaining independent; many useful calibrations will reasonably remain separate (e.g., a security firm's proprietary mapping is properly its own namespace).

---

## Article 9 — Examples

The following are illustrative examples of how the Protocol might be applied in practice. None of these are AquaUrsa endorsements; they are scenarios.

### 9.1 Example: Trail of Bits publishes a Slither-calibrated TOOL-MAPPING

- **Fork type**: Calibration fork (Article 2.1)
- **Namespace**: `tool-mapping/trailofbits-v1`
- **Citation**: cites parent specification doi:10.5281/zenodo.20386868
- **Deposit**: Zenodo with own DOI
- **Compatibility**: `strict` — same schema, only depth values and justifications differ
- **Outcome**: ecosystem now has two calibrations; consumers choose which to trust; disagreements are themselves informative

### 9.2 Example: A research group adds privacy obligations

- **Fork type**: Extension fork (Article 2.2)
- **Name**: `PARALLAX-5-Privacy-Extended-v1`
- **Documents**: published extended taxonomy + Lean 4 proofs for new obligations
- **Compatibility**: `additive` — parent certificates remain valid; extended certificates have additional fields
- **Citation**: cites parent + relevant prior privacy work
- **Outcome**: the extension may be incorporated back into PARALLAX-5 v2.0 via pull-back, or remain independent

### 9.3 Example: A company forks the registry contract

- **Fork type**: Refinement fork (Article 2.3)
- **Name**: `parallax-registry-enterprise-v1`
- **Divergence**: adds access controls for enterprise compliance use cases
- **Compatibility**: `semantic-divergence` — admin role exists; the contract no longer passes its own walkaway test
- **Documentation**: explicit divergence note explaining why and what compatibility is lost
- **Outcome**: enterprise users have a fitted tool; the canonical registry remains admin-free; ecosystem participants choose

### 9.4 Example: A team builds a Solana-native verification substrate citing PARALLAX-5

- **Fork type**: Independent reformulation (Article 2.4)
- **Name**: distinct (not "PARALLAX")
- **Citation**: PARALLAX-5 cited as related work
- **Compatibility**: independent
- **Outcome**: parallel ecosystem; cross-ecosystem citation maps both

---

## Article 10 — Forking this Protocol

**10.1** This Fork Protocol is itself CC0 and may be forked.

**10.2** A forked Fork Protocol should be named distinctively (e.g., `parallax5-fork-protocol-strict-v1`) and should document its divergence from this version.

**10.3** The PARALLAX-5 ecosystem may, over time, converge on one or more refined Fork Protocols. This document is a starting point, not the final word.

---

## Article 11 — Citation

```bibtex
@misc{duncan2026parallaxforkprotocol,
  author    = {{AquaUrsa Research}},
  title     = {{Fork Protocol: PARALLAX-5}},
  year      = {2026},
  version   = {1.0},
  publisher = {AquaUrsa Research},
  license   = {CC0},
  url       = {https://parallax.xyz/fork-protocol}
}
```

---

## Companion documents

- `docs/CHARTER.md` — the governance commitment this Protocol operationalizes
- `VISION_AND_ROADMAP_v2.0.md` — the substrate's strategic and operational reference
- `docs/CERTIFICATE_SCHEMA.md` (forthcoming) — the schema this Protocol's compatibility levels reference

---

**End of Protocol.**

This document is CC0. Fork it. Improve it. Reference the parent deposit if useful.
