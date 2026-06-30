# Open Problems

PARALLAX-5 v1.1.0 leaves several research problems unresolved. This document lists them and invites collaboration from the formal methods, AI safety, and security research communities.

The problems are organized by category: substrate-internal questions about the formalization, runtime-extension work carrying the framework to additional VM semantics, empirical questions about the catalog and observability, and adjacent problems whose solution would compose with PARALLAX-5.

For each problem, the description covers what the problem is, what makes progress difficult, and what would constitute progress. Co-authorship on v1.1 and later paper revisions is open to substantive contributors. Research Fellow listing on AquaUrsa Research is available for sustained collaboration. Contact `research@aquaursa.ai`.

## Substrate-internal

### Minimality proof versus independence

The substrate currently proves that the axiom set {A1, A2, A4, A5} is *independent*: no axiom is implied by the conjunction of the others. The relevant Lean theorem is `basis_minimal` at line 189 of `parallax/formal/lean/Parallax5.lean`. Independence is necessary but not sufficient for minimality.

True minimality would prove that no strictly smaller obligation set covers the same loss space. The claim becomes: for every 3-element subset of {A1, A2, A4, A5}, there exists a loss-inducing trust-base violation not covered by that subset.

The difficulty is empirical. The "loss space" is the universe of possible loss-inducing transitions, which is open-ended. A constructive minimality proof requires either a formal characterization of the loss space (very hard) or explicit counterexamples for each 3-subset showing the substrate becomes insufficient when any axiom is removed (more tractable).

Progress would be four explicit Lean theorems exhibiting counterexample states `losing_state_3subset_A1A2A4` and the three other 3-subsets, each showing that removing the missing axiom from the substrate makes it incapable of detecting the example.

This is the most-asked academic question.

### A3 generalization

A3 (signature integrity) is the most narrowly-scoped axiom in the basis. The current formulation captures EVM-specific signature validation (`ecrecover`, EIP-712 typed data, account abstraction). For non-EVM runtimes (Solana, Move), the natural analog is structurally similar but the abstract formulation should make this clear.

The difficulty lies at the boundary between "what is a signature" (abstract) and "what is a valid signature" (concrete cryptographic verification). The abstract formulation must avoid baking in EVM-specific assumptions without becoming so abstract that the predicate loses operational meaning.

Progress would be a refactored A3 predicate in Parallax5.lean that is genuinely runtime-agnostic, plus instance proofs for at least three concrete runtimes (EVM, Solana ed25519 signatures, Move/Sui transfer policies).

### Information-theoretic basis-observability bound

The catalog empirically shows 67.2% basis-observable losses. No theoretical upper bound on this share is known. A substantially richer obligation set, say 12 obligations covering off-chain coordination, governance attacks, and oracle compromises, might push the share toward 90%. Whether an information-theoretic limit exists is open.

The difficulty is that bounds of this form usually require channel capacity arguments. Such arguments presuppose a model of the information leak from off-chain to on-chain. A nascent model exists in the four-observability-set hierarchy (Ω_chain ⊆ Ω_config ⊆ Ω_intent ⊆ Ω_infra), but the model is not fully formalized.

Progress would be an information-theoretic theorem of the form: any on-chain-only gate has at most X% loss-coverage for adversaries with access to off-chain channels, where X is a specific function of the channel capacity. The result would frame what is achievable for any future obligation framework, not just PARALLAX-5.

### Composition with separation logic

The substrate's obligations are predicates over state. Iris-style separation logic provides a richer framework for reasoning about resources, ownership, and concurrent access. A natural question is whether PARALLAX-5 obligations can be expressed as Iris-style assertions and whether the resulting framework gains expressive power.

The difficulty is that Iris has a steep learning curve. The integration must produce genuine new capability rather than notational re-skinning.

Progress would be an Iris-based reformulation of A1 and A2 that admits proofs of concurrent-access properties not currently expressible. A canonical example: two concurrent agents both behind the gate preserve A1 in the joint state.

## Runtime extension

### Production Move semantic refinement

The substrate has typeclass-level Move support: a `ValueBearingMachine` instance for the Move resource model. Missing is a production-grade semantic refinement analogous to the EVMYulLean composition for EVM. The target is a Lean module providing concrete proof terms over the Move semantics.

The difficulty is that no Lean formalization of Move semantics exists. The path to progress requires either building such a formalization, translating from existing Move formalizations (Move Prover, K-Move) into Lean, or collaborating with the Sui or Aptos teams to fund the work.

Progress would be `parallax/formal/lean/Parallax5_Move.lean` analogous to `Parallax5_EvmYulLean.lean`, with concrete proof terms for at least five obligations over a Sui-specific Move resource state. The Sui Foundation grant application targets this work.

### Solana SVM semantic refinement

Same shape as the Move problem, applied to the Solana SVM. The Solana account model is more constrained than the EVM (no shared mutable state across contracts), which simplifies some obligations but complicates others. The cross-account transfer pattern differs from EVM `transfer` at the semantic level.

The difficulty is similar to Move: no public Lean formalization of the Solana SVM exists. The closest related work is the K-Solana effort. Progress would be a partial formalization covering Solana SPL token transitions, sufficient to demonstrate the composition pattern for the substrate.

### zkEVM semantic refinement

Polygon zkEVM, zkSync Era, Scroll, and Linea each provide variant EVM semantics with zero-knowledge proof generation. The substrate could compose with these and lift its safety guarantees from "verified by trusted prover" to "verified by zk-proof."

The difficulty is that zkEVMs differ subtly from mainnet EVM in opcodes, gas accounting, and precompiles. Composition requires a per-zkEVM refinement that documents the differences.

Progress would be `Parallax5_zkEVM.lean` for at least one production zkEVM. Polygon zkEVM is the most likely first candidate given its formal-methods backbone (Pil2) and the relationship to the EVMYulLean integration AquaUrsa already maintains.

### Banking-ledger semantic refinement

For DORA-regulated financial entities, a PARALLAX-5 binding over a traditional banking ledger (account-based, double-entry, with central authority) would address a high-leverage use case. The Move and Solana refinements are token-balance-based. Banking ledgers add journal entries and the duality of debits and credits.

The difficulty is that this work requires close collaboration with a financial institution to ensure the abstract model matches concrete operational reality. The model needs to handle the regulatory specifics of double-entry conservation, dual-control authorization, and audit-trail requirements.

Progress would be `Parallax5_BankingLedger.lean` with concrete proof terms for at least the double-entry conservation law and the account-authorization closure.

## Empirical

### Catalog expansion to 100+ incidents

The 53-incident catalog at `paper/supplement/catalog.csv` covers 2016 through 2026. Expanding to over 100 incidents requires collecting additional incidents from 2024 through 2026, maintaining the rigorous classification methodology documented in `docs/CATALOG_METHODOLOGY.md`, and ensuring the basis-observable share remains a meaningful empirical estimate.

The work is effort-bound rather than insight-bound. Classification is judgment-dependent; the inter-rater reliability methodology in `paper/INTER_RATER_PROTOCOL.md` applies to each new incident.

Progress would be 50 additional incidents classified using the established methodology with inter-rater kappa above 0.7. Collaboration with security researchers who already track DeFi exploits (REKT News, BlockSec, SlowMist, PeckShield) would accelerate this substantially.

### Inter-rater reliability validation by external auditors

The inter-rater protocol has been applied internally. External validation by an independent auditor would strengthen the empirical claim substantially.

Progress would be an external auditor independently classifying 20 or more incidents using `paper/INTER_RATER_PROTOCOL.md` and reporting the kappa statistic against the original AquaUrsa classification. AquaUrsa provides the protocol, the raw data, and our classifications. The auditor classifies blind. The kappa is computed. The result is published regardless of value.

This is low-effort, high-credibility work.

### Adversarial catalog construction

The current catalog is selected for largest losses and most-cited incidents. An adversarially-constructed catalog of minimum-cost exploits would test the substrate's robustness more rigorously.

The difficulty is that this requires deep security expertise plus willingness to publish, which sophisticated researchers may not want to do for fear of being seen as facilitating attacks.

Progress would be a published companion catalog of 20 or more adversarially-constructed exploit archetypes, each tested against the substrate's gate. Appropriate disclosure norms apply.

## Adjacent

### Integration with EF's CROPS framework

The Ethereum Foundation's 2026 strategic communications use CROPS as a four-value framework (censorship-resistant, open source, private, secure). PARALLAX-CROPS is a five-component refinement. Composing the two cleanly requires articulating the relationship explicitly.

Progress would be a published joint methodology document with the EF research community covering the relationship. The EF ESP grant application addresses this work.

### PARALLAX-5 obligations as RSP evaluation criteria

Anthropic's Responsible Scaling Policy defines capability thresholds (ASL-2, ASL-3, ASL-4) and evaluation requirements. The question is whether a PARALLAX-5 gate's accept/reject distribution can serve as an evaluation criterion for ASL-3-plus agents acting on value-bearing state.

The difficulty is that RSP capability evaluations are themselves a research frontier. Integrating PARALLAX-5 requires Anthropic-side engagement.

Progress would be a joint paper or technical report with Anthropic researchers articulating the integration. The minimum viable engagement would be deploying a current Anthropic agent (Claude or similar) behind a substrate gate for a single benchmark task and reporting the gate's output.

### PARALLAX-5 gate as a Constitutional AI safety layer

Constitutional AI shapes an agent's internal policy through training. The substrate enforces external behavioral bounds at runtime. The two compose: a CAI agent operating behind a PARALLAX-5 gate has both endogenous and exogenous safety properties.

Progress would be a worked example deploying an Anthropic-style CAI agent behind a PARALLAX-5 gate, with empirical measurement of the gate's reject rate over a benchmark workload.

### PARALLAX-5 obligations as formal AI policy

EU AI Act Annex IV requires technical documentation of risk management. A natural research question: how can PARALLAX-5 certificates serve as inputs to a formal policy-language representation of an organization's AI risk management framework?

Progress would be a formal policy language (extending Open Policy Agent or a similar framework) that consumes PARALLAX-5 certificates and produces compliance assertions. Policy-language researchers at Berkeley AFOG, Stanford HAI, and similar groups would be natural collaborators.

## Engagement

For low-effort engagement (a discussion, a critique, a pointer to related work), email `research@aquaursa.ai`. Aim for response within two weeks.

For substantive collaboration (joint paper, joint experiment, mutual citations), open a short proposal email describing what you would contribute and what you would need from us. Co-authorship on v1.1 and later paper revisions is open to substantive contributors.

For sustained collaboration (multi-month engagement, Research Fellow listing), a video call to align on scope is the next step. Research Fellows are listed on the AquaUrsa Research site with their specific contributions.

For competitive engagement (you build an alternative substrate, you publish a critique), the engagement is welcome. The standard of dialogue is that the best argument wins regardless of who makes it.

## Out of scope for this document

Engineering-only improvements (better Lean tactics, performance optimization) are tracked in GitHub issues rather than as open research problems.

Commercial roadmap items (Co-Pilot SaaS features, marketing site improvements) are tracked separately.

Specific paper revisions are handled through CHANGELOG.md and the v1.1 or v2.0 paper revision processes.

The 15 problems above represent the substantive intellectual frontier of the substrate. The list is intended as a credible academic agenda for collaboration.
