# IP Provenance

This document is for M&A due diligence analysts, law firms preparing definitive acquisition agreements, Big 4 audit firms conducting third-party risk assessments, and corporate development teams evaluating PARALLAX-5 as an acquisition or partnership target.

It states the IP situation across the full repository: ownership, license layering, contributions, third-party dependencies, patent posture, trademark posture, and structural non-capturability commitments. It is written to support legal review without requiring document discovery beyond the repository itself.

For the underlying licenses, see `LICENSE` (Apache-2.0 for code), `LICENSE-CC0` (CC0 1.0 Universal for Standard text), and `LICENSE-PAPER` (CC-BY 4.0 for the paper). For the Charter establishing structural commitments, see `docs/CHARTER.md`.

## Ownership

AquaUrsa Research LLC, a Wyoming limited liability company, owns the copyright on all original work in this repository. The LLC is solely owned by Ben Duncan (founder).

The repository's commit history is the authoritative attribution record. Every commit on `main` is authored by `AquaUrsa Research <research@aquaursa.io>`. No external contributors have committed to `main` as of v1.1.0.

Pull request branches authored by external contributors are accepted under the contribution terms in `CONTRIBUTING.md`, which require either Apache-2.0 contributions (for code) or CC0 dedication (for Standard text contributions). The contribution agreement is documented at the time of pull-request acceptance.

## License layering

The repository uses a three-license layered structure. The boundary is by file type, not by directory.

Code components (Python, Solidity, Lean, shell scripts, build tooling, configuration files) are licensed under Apache-2.0. The full text is at `LICENSE`. Apache-2.0 is OSI-approved and contains a patent grant.

Standard-text components (the PARALLAX-5 specification including the obligation vocabulary, depth scale, CROPS dimensions, walkaway taxonomy, certificate field semantics, and `paper/PARALLAX-5-Standard.md`) are dedicated to the public domain under CC0 1.0 Universal. The full text is at `LICENSE-CC0`. CC0 is the strongest dedication available; it waives all rights to the maximum extent permitted by law.

Academic-paper components (`paper/parallax-5.tex`, `paper/parallax-5.pdf`, and related supplements explicitly marked as paper content) are licensed under Creative Commons Attribution 4.0 International. The full text is at `LICENSE-PAPER`. CC-BY-4.0 permits commercial use and modification with attribution.

Individual files indicate their license through SPDX-License-Identifier headers where present. Where headers are absent, the layer-by-file-type rule applies.

The licensing posture is intentional. The Standard text is a public good and must remain so; CC0 is the strongest possible dedication. The reference implementation is Apache-2.0 to preserve attribution while permitting commercial derivative work. The paper is CC-BY-4.0 to encourage academic citation.

## Compatibility analysis

Apache-2.0, CC0, and CC-BY-4.0 are all permissive licenses compatible with most downstream uses including commercial closed-source distribution. The combination has no known compatibility issues with each other or with major downstream license families (MIT, BSD, ISC, MPL-2.0, LGPL-3.0).

The substrate has no GPL-licensed code. The substrate has no AGPL-licensed code. The substrate has no copyleft contamination.

The CC0 Standard text can be incorporated into any downstream project without restriction. The Apache-2.0 code requires attribution and the patent-grant terms to be carried forward. The CC-BY-4.0 paper requires attribution if redistributed.

For an acquisition where the acquirer wishes to keep proprietary derivative implementations, this license layering supports that posture. The Apache-2.0 license permits proprietary derivatives; the CC0 Standard text is unencumbered.

## Third-party dependencies

The substrate depends on several third-party Lean and Python packages. Each is documented for license compatibility.

EVMYulLean (Nethermind, Apache-2.0) is the production EVM semantics used in the composition documented at `parallax/formal/lean/Parallax5_EvmYulLean.lean`. Apache-2.0 is compatible with Apache-2.0. The composition's dependency is documented in the `lakefile.lean` of the integration verification artifact.

Mathlib (Lean community, Apache-2.0) provides the standard mathematical library for Lean 4. Apache-2.0 compatibility is direct.

forge-std (Foundry team, MIT licensed) is included as a git submodule at `registry/lib/forge-std` for Foundry tests. The pinned version is v1.16.1. MIT is compatible with Apache-2.0; attribution requirements are met by the submodule pointer and forge-std's own LICENSE file.

Python runtime dependencies (jsonschema, pyyaml, ecdsa, z3-solver, cvc5, yices-solver, click, pytest) are all permissively licensed. Their license terms are documented in `pyproject.toml`. The dependency graph contains no GPL or AGPL components.

Cryptographic library dependencies for the Ed25519 certificate-signing path use Python's `cryptography` package (Apache-2.0 / BSD dual-licensed). The library is widely used in commercial deployments.

## Patent posture

AquaUrsa Research LLC has filed zero patent applications covering any aspect of the substrate. AquaUrsa makes no patent claims over the disclosed techniques, including the five-obligation decomposition, the step-secure gate, the basis-observability predicate, the CROPS vector, the certificate schema, or the EVMYulLean composition.

The Apache-2.0 patent grant in `LICENSE` (Section 3) extends to all contributors. Any patent owned by AquaUrsa or future contributors that reads on the licensed work is licensed automatically to all users under Apache-2.0 terms.

`docs/CHARTER.md` (Article 2) makes the no-patent commitment a structural commitment of the project. The Charter is published under CC0 and is structurally irrevocable; future leadership of AquaUrsa cannot withdraw the commitment without abandoning the project's identity.

The patent posture is intentional. The substrate is designed to be widely adoptable by audit firms, AI safety platforms, and tooling vendors without patent licensing risk.

## Trademark posture

AquaUrsa Research LLC has filed no trademark applications on "PARALLAX-5", "PARALLAX-CROPS", "Co-Pilot", or related marks. The Charter (Article 2) commits AquaUrsa to not assert trademark rights over the PARALLAX-5 name or related Standard-text terms.

"AquaUrsa" is the corporate identity. The corporate identity is distinct from the substrate. Acquisition of the substrate does not convey rights to the AquaUrsa corporate identity; acquisition of the AquaUrsa corporate entity is a separate transaction with separate terms.

## Non-capturability commitments

`docs/CHARTER.md` documents eleven structural commitments that make the substrate non-capturable by any single entity, including AquaUrsa. The commitments are intentionally irrevocable: the CC0 dedication of the Standard text cannot be withdrawn, the no-patent commitment is structurally tied to Apache-2.0, the no-trademark commitment is structurally tied to the CC0 dedication, and so on.

For an M&A analyst evaluating PARALLAX-5 as an acquisition target, this is the critical posture point. AquaUrsa cannot sell exclusive rights to the substrate; the rights are publicly dedicated and structurally irrevocable. What AquaUrsa can sell is the corporate entity, the founder (Ben Duncan) as employee or advisor, the commercial Co-Pilot SaaS layer, the brand and customer relationships of AquaUrsa, and the engineering work product around the substrate.

This is intentional. The substrate gains value as it becomes more widely adopted. Wide adoption requires non-capturability. Non-capturability is the foundation of the strategic position.

For acquirers, the relevant value is the commercial wrapper (Co-Pilot SaaS, customer relationships, founder time, ongoing development capacity) rather than the substrate itself.

## Contributor License Agreement

External contributions are accepted under the terms in `CONTRIBUTING.md`. Contributions of code are licensed under Apache-2.0; contributions to Standard text are dedicated under CC0. A Developer Certificate of Origin sign-off is required on each commit.

There is no separate CLA document. Contributors are not asked to assign copyright. The Apache-2.0 + DCO model is the same model used by the Linux kernel, Kubernetes, and most major open-source projects. This model is broadly understood by enterprise legal teams.

For acquirers preparing definitive agreements, the contribution audit consists of two checks. First, verify that every commit on `main` has a valid DCO sign-off (Apache-2.0 contributions) or is to Standard-text files (CC0 dedication). Second, verify that no commit is authored by an unaffiliated individual outside the AquaUrsa Research identity. Both checks pass at v1.1.0; the audit trail is the git history.

## Litigation and disputes

No litigation is pending against AquaUrsa Research LLC related to PARALLAX-5 or any other matter as of 2026-05-27.

No claims of trademark infringement, patent infringement, copyright violation, or trade-secret misappropriation are pending or threatened.

No prior agreements survive that would constrain AquaUrsa's ownership or rights over the work. The work was developed entirely after AquaUrsa Research LLC was formed; no prior employer claims survive.

## Acquisition treatment

For an acquirer purchasing AquaUrsa Research LLC, the IP situation is as follows.

The acquirer obtains the commercial wrapper (Co-Pilot SaaS source code, customer relationships, brand and marketing assets, infrastructure, founder employment under negotiated terms).

The acquirer does not obtain exclusive rights to the substrate. The substrate remains publicly dedicated under CC0 (Standard text), Apache-2.0 (code), and CC-BY-4.0 (paper). The acquirer can continue to develop the substrate under the same open-source licenses; the acquirer cannot stop others from doing so.

The Charter's commitments survive acquisition. The acquirer cannot reverse the CC0 dedication, file patents on the substrate techniques, or trademark the substrate names, because these commitments are structurally tied to the existing licenses and the existing Charter publication.

Definitive acquisition documentation should include four standard clauses on this point. First, an acknowledgment that the substrate is publicly licensed and the acquirer's rights are the same as any other licensee's. Second, a confirmation that the acquirer will not attempt to file patents on the disclosed techniques. Third, an acknowledgment that the Charter's commitments survive the transaction. Fourth, an enumeration of the assets the acquirer does obtain (the commercial wrapper and corporate entity).

For an acquirer preferring exclusive substrate rights, no acquisition structure can provide them. The substrate is not for sale exclusively because it is already given away. An acquirer wanting exclusivity should pursue a different target.

## Engagement

For acquisition or partnership conversations involving IP review, contact `research@aquaursa.io`. AquaUrsa is open to NDA-covered IP diligence conversations after a substantive first contact.

For M&A counsel preparing definitive agreements, AquaUrsa can refer to its own counsel for direct engagement. The relevant context is that the substrate's IP posture is intentional and not subject to negotiation. The commercial wrapper's IP terms are negotiable per standard M&A practice.

For Big 4 third-party risk assessments, this document provides the standard answers. Specific questions beyond this document can be directed to `research@aquaursa.io`.

## Document version

This document reflects the IP posture as of PARALLAX-5 v1.1.0 dated 2026-05-27. Material changes (new contributors, new dependencies, new license claims) trigger an update to this document coordinated with `CHANGELOG.md`.
