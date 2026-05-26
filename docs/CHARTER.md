# Non-Capturability Charter — PARALLAX-5

**Document status:** Foundational governance commitment of the PARALLAX-5 substrate.
**Version:** 1.0
**Issued by:** AquaUrsa Research
**License of this document:** CC0 (no rights reserved)
**Companion documents:** `docs/FORK_PROTOCOL.md`, `VISION_AND_ROADMAP_v2.0.md`
**Parent project DOI:** 10.5281/zenodo.20386868

---

## Preamble

A verification substrate that depends on a single individual, organization, or commercial entity for its operation is not credibly neutral. It is, at best, an instrument of one party's reputation; at worst, a captured standard whose authority can be revoked. PARALLAX-5 is designed to be neither.

This Charter is the public commitment of AquaUrsa Research that PARALLAX-5 — defined as the vocabulary, taxonomy, schemas, and verification primitives published under the PARALLAX-5 name and its derivative variants — shall remain a public good. It is also the technical statement of the structural mechanisms by which that commitment is enforced.

The commitment is not enforced by AquaUrsa's promise. It is enforced by the absence of any mechanism by which AquaUrsa, or any successor, could revoke or constrain the substrate's availability.

---

## Article 1 — Defined terms

**1.1** "The substrate" refers collectively to: the PARALLAX-5 obligation taxonomy (A1–A5), the CROPS dimension framework (Censorship-resistance, Capture-resistance/Walkaway, Openness, Privacy, Security), the certificate schema specification, the TOOL-MAPPING calibration format, the formal theorem statements expressed in Lean 4, the published proofs of those theorems, the registry interface specification, the falsification challenge protocol, and any subsequent extensions or refinements published under the PARALLAX-5 name.

**1.2** "The standard text" refers to the human-readable specification documents that describe the substrate: the published papers, the Vision and Roadmap documents, the TOOL-MAPPING specification, the certificate schema specification, the Walkaway theorem note, the CROPS matrix note, this Charter, and the Fork Protocol.

**1.3** "The code artifacts" refers to the reference implementation: the `parallax5_coordinator` Python package, the JSON Schema specifications, the Lean 4 theorem files, the smart contracts deployed under the PARALLAX-5 name, the CI/CD integrations, and any associated tooling distributed under the PARALLAX-5 name.

**1.4** "AquaUrsa" refers to AquaUrsa Research and its successors, agents, or assignees.

**1.5** "A derivative variant" refers to any fork, extension, refinement, or independent reformulation of the substrate, published under a name that distinguishes it from the canonical PARALLAX-5 release (e.g., `tool-mapping/trailofbits-v1`, `parallax5/community-v1`, or a renamed derivative).

---

## Article 2 — Licensing commitments

**2.1 The standard text** is released under Creative Commons Zero (CC0 1.0 Universal). No rights are reserved. Any party may copy, modify, distribute, or republish the standard text without permission, attribution, or compensation to AquaUrsa.

**2.2 The code artifacts** are released under the Apache License, Version 2.0. Apache-2.0 preserves attribution to original contributors while permitting commercial use, modification, and redistribution without royalty or further permission.

**2.3** AquaUrsa Research **shall not** issue, claim, register, or enforce any trademark, service mark, certification mark, or analogous identifier over the names "PARALLAX-5", "PARALLAX5", "PARALLAX", "TOOL-MAPPING", or derivative names that would restrict their use by third parties. The names exist in the public domain.

**2.4** AquaUrsa Research **shall not** apply for or hold patents over the substrate's mechanisms — including the obligation taxonomy, the certificate schema, the compositional theorems, the runtime gate architecture, the falsification challenge protocol, or any other published method.

**2.5** These licensing commitments are **structurally irrevocable**: CC0 cannot be revoked; Apache-2.0 grants are perpetual; absence of trademark cannot be retroactively created.

---

## Article 3 — Operational commitments

**3.1 No proprietary control points.** AquaUrsa Research shall not introduce, into the substrate's reference implementation or smart contracts, any mechanism that requires AquaUrsa's involvement for the substrate to operate. Specifically:

- The reference implementation shall depend on no API endpoint operated by AquaUrsa
- The reference smart contracts shall have no admin functions, upgrade paths, governance mechanisms, or AquaUrsa-controlled parameters
- The Lean 4 proofs shall depend on no proprietary tooling
- All toolchain dependencies shall be open-source with permissive licenses

**3.2 No gating of the vocabulary.** AquaUrsa Research shall not require permission, license fees, registration, or any other gating mechanism for any party to:

- Use the obligation taxonomy in their own work
- Issue certificates against the schema
- Publish calibrations or mappings
- Submit entries to the on-chain registry
- Reference the substrate in academic, commercial, or other contexts

**3.3 No exclusivity claims.** AquaUrsa Research shall not enter into any agreement — commercial, governmental, or otherwise — that grants any party exclusive rights, preferred access, or first-refusal over the substrate or its evolution.

**3.4 Transparent derivative work.** AquaUrsa Research, when issuing certificates, calibrations, or services that build on the substrate, shall do so under names that clearly distinguish AquaUrsa's commercial work from the substrate itself (e.g., "TOOL-MAPPING/aquaursa-v1" rather than "TOOL-MAPPING official").

---

## Article 4 — Governance commitments

**4.1 No governance body.** PARALLAX-5 has no governance body, board, council, foundation, DAO, or analogous structure. There is no party authorized to issue binding decisions about the substrate's evolution. Evolution proceeds through Zenodo deposit chains, public discussion, and the Fork Protocol (see `docs/FORK_PROTOCOL.md`).

**4.2 No token.** No cryptocurrency token, governance token, or analogous instrument is or shall be issued in connection with the substrate. Any tokenization of services built on the substrate (e.g., insurance pools backed by certificates) is the work of independent parties and not endorsed, controlled, or coordinated by AquaUrsa.

**4.3 No treasury.** AquaUrsa Research does not hold a treasury on behalf of the substrate. AquaUrsa's commercial revenue from paid services is its own corporate revenue and is not characterized as substrate-related funds.

**4.4 No authority over derivatives.** AquaUrsa Research has no authority to approve, reject, certify, or de-certify derivative variants of the substrate. Any party may fork the substrate under the conditions of the Fork Protocol.

---

## Article 5 — Mathematical commitments

**5.1 Falsifiability.** Every claim made by the substrate (taxonomic, theoretical, empirical, or operational) shall be stated in a form that admits explicit counterexample. The Falsification Challenge framework (see Vision and Roadmap §11) operationalizes this commitment.

**5.2 Machine-verifiability.** All formal theorems shall be expressed in Lean 4 (or equivalent kernel-checkable proof assistant) and shall be kernel-accepted with zero unverified obligations (`sorry`).

**5.3 Honest scope.** The substrate shall not claim to address matters outside its formal scope. Specifically, the basis-observability boundary identified in PARALLAX-5 shall be explicitly named in all certificates and claims; nothing shall be asserted about what the substrate cannot, in principle, prove.

---

## Article 6 — Anti-fragility commitments

**6.1 Adversarial review.** AquaUrsa Research explicitly invites critique, falsification, and challenge of all substrate components. Reviewer effort that produces substantive technical correction shall be credited in subsequent publications with the reviewer's consent. Reviewers who identify substantive flaws are invited to be credited as co-authors on the next revision.

**6.2 Public response to challenges.** Every accepted falsification challenge (per the Vision and Roadmap §11 framework) shall be publicly resolved: the challenge documented, the resolution recorded on the registry, and the substrate updated where appropriate. Adversarial events strengthen the substrate.

**6.3 No silencing.** AquaUrsa Research shall not pursue legal, social, or commercial action to suppress, retract, or discourage public critique of the substrate. Even critique that is substantively incorrect remains publicly addressable, not silenced.

---

## Article 7 — The walkaway commitment

The substrate is designed to satisfy its own walkaway test: it must continue to function, evolve, and serve the public if AquaUrsa Research disappears tomorrow.

**7.1 Continuity by structure.** The mechanisms that ensure continuity are:

- The standard text under CC0: anyone may republish without permission
- The reference implementation under Apache-2.0: anyone may fork and maintain
- The Zenodo deposits are immutable and indexed by DOIs not controlled by AquaUrsa
- The on-chain registry has no admin and cannot be paused or revoked
- The mapping calibrations exist as a namespace; AquaUrsa's mapping is one entry among many
- The falsification protocol is public

**7.2 Successor parties.** If AquaUrsa Research wishes to transfer or wind down its operational role, it shall do so by:

- Publishing a final accounting of any outstanding obligations
- Releasing all internal artifacts under the substrate's licenses
- Identifying (where appropriate) successor parties who have accepted the same commitments
- Not transferring any name-control or authority-claim, because none exists to transfer

**7.3 No fallback dependency.** No component of the substrate shall require AquaUrsa's continued existence to function. The Fork Protocol provides the mechanism for any party to maintain the substrate independently.

---

## Article 8 — Limits of this Charter

**8.1 This Charter governs the substrate, not AquaUrsa's commercial work.** AquaUrsa Research may offer paid services (hosted validation, professional certification, runtime gate SDK, AI-agent transaction firewall, enterprise integrations, etc.) on commercial terms. These services build on the substrate; they do not constrain it. Commercial offerings are governed by their own terms of service, not this Charter.

**8.2 Distinction between substrate and AquaUrsa.** AquaUrsa Research's reputation, its mapping calibrations (e.g., `aquaursa-v1`), its certificate-issuance services, and any premium products it offers are AquaUrsa's commercial property. They are governed by AquaUrsa's own choices and the legal framework of its incorporation. The substrate itself is a public good and is not.

**8.3 This Charter does not bind third parties.** Other parties — adopters, integrators, calibration authors, certificate issuers, audit firms, insurers, wallets — make their own commitments under their own governance. This Charter governs only AquaUrsa Research's commitments to the substrate.

---

## Article 9 — Amendment

**9.1** This Charter may be amended only by:

- Issuing a new version (e.g., Charter v1.1) under the same CC0 license
- Depositing the new version on Zenodo with a distinct DOI
- Documenting the amendment in a public changelog that explains what changed and why
- Preserving the prior version as historical record

**9.2** No amendment may introduce a control point, a proprietary mechanism, a gating requirement, a trademark claim, a governance body, or any other capture surface. Amendments that would do so are by definition outside the Charter and would constitute a renamed derivative variant under the Fork Protocol, not an amended Charter.

**9.3** The intent of this Article is that the Charter cannot be amended into capture. Strengthening commitments is permitted; weakening structural non-capturability is not.

---

## Article 10 — Acknowledgment

This Charter is informed by:

- The principles of credible neutrality articulated by Vitalik Buterin (notably in the 2020 essay "Credible Neutrality As A Guiding Principle")
- The CROPS framework articulated by the Ethereum Foundation
- The "walkaway test" as a heuristic for application-layer trust
- Long-running work in the formal-methods community on substrate-shaped open-source projects
- The licensing commitments of Linux, the Lean theorem prover, and the Ethereum protocol itself

The Charter does not, however, depend on the endorsement of any of these. It stands on the structural mechanisms it documents.

---

## Article 11 — Citation

```bibtex
@misc{duncan2026parallaxcharter,
  author    = {{AquaUrsa Research}},
  title     = {{Non-Capturability Charter: PARALLAX-5}},
  year      = {2026},
  version   = {1.0},
  publisher = {AquaUrsa Research},
  license   = {CC0},
  url       = {https://parallax.xyz/charter}
}
```

---

## Signature

This Charter is published by:

**AquaUrsa Research**
The Charter takes effect immediately upon its first Zenodo deposit and remains in force in perpetuity, modified only by amendments compliant with Article 9.

The substrate's non-capturability is enforced not by this signature, but by the structural commitments documented above. The signature is a public statement of intent; the structure is what makes the intent credible.

---

**End of Charter.**

This document is CC0. No rights are reserved. Anyone may copy, modify, distribute, or republish without permission. Reference back to the parent deposit (doi:10.5281/zenodo.20386868) is appreciated where applicable but not required.
