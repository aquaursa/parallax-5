# Related Work

PARALLAX-5 sits in an active research and engineering landscape spanning formal verification, smart-contract security tooling, and AI agent safety. This document positions the substrate against the most relevant adjacent work so that adopters, reviewers, and collaborators can assess the substrate's scope, novelty, and complementarity quickly.

Where the substrate overlaps with prior work, the overlap is stated. Where it diverges, the divergence is named. Where work is competitive, the competition is acknowledged.

## Layer model

The substrate occupies a specific position in the stack between concrete VM semantics and operational security tools.

Above the substrate sit runtime AI policy enforcement systems (Cisco AI Defense, CyberArk Conjur, the post-Robust-Intelligence AI Firewall lineage, Truera, Arize) and operational security and assurance tools (Slither, Mythril, halmos, Certora, Trail of Bits Manticore, OpenZeppelin Defender, Sherlock, Cyfrin Aderyn). The substrate provides the obligation vocabulary that findings from these tools can be tagged with.

Below the substrate sit concrete VM semantics: EVMYulLean for production EVM, K-based semantics for Move and Solana, CertiK's CertiKOS lineage for verified-kernel formalization, traditional banking-ledger semantics for DORA-regulated financial systems. The substrate provides the abstract framework into which these concrete semantics can be plugged.

The substrate does not replace any layer above or below. It fills the formal vocabulary gap that prevents layers from composing with explicit soundness claims.

## Certora Prover

Certora provides a production-grade prover with a custom specification language (CVL). Engagements typically range from $30K to $100K per protocol and produce property-checking reports with formal guarantees on the verified properties.

The relationship between Certora and PARALLAX-5 is structurally complementary. Certora is a tool that proves specific properties of specific contracts; PARALLAX-5 is a substrate that provides obligation vocabulary tools can map findings to. A Certora engagement can produce findings tagged with PARALLAX-5 obligation labels (A1 through A5), giving Certora customers a vocabulary that persists across tool switches or auditor changes. The substrate does not replace CVL and does not compete with Certora's prover.

For a Certora user, integration is at the reporting layer rather than the verification layer. The prover's output remains unchanged; the certificate emitted alongside the report cites the prover's verified properties as evidence for the relevant obligations.

## K Framework

K is a semantic framework developed at UIUC and commercialized by Runtime Verification, Inc. K has produced K-EVM (the formal EVM semantics that informed EVMYulLean's design), K-Solidity, and K-Move.

The intellectual lineage between K and PARALLAX-5 is direct. Where K separated semantics from analysis (define a language, get parsers, interpreters, and model checkers automatically), PARALLAX-5 separates obligations from semantics (define an obligation set, get gate semantics, refinement theorems, and runtime instances automatically).

A CROPS instance built using K-Solidity as the EVM refinement, instead of EVMYulLean, would compose cleanly with the substrate. The substrate is semantics-agnostic at the typeclass level; specific instances select the concrete semantic foundation. Building such an alternative instance is explicit future work and a natural collaboration with Runtime Verification.

## Move Prover and MIRAI

Move Prover (Aptos, formerly Diem) and MIRAI (Facebook/Meta) target language-specific safety verification for Move and Rust respectively. Both work at the source-language level with pre- and post-condition specifications.

The substrate's relationship to these tools mirrors its relationship to Certora: a `ValueBearingMachine` instance over the Move type system gives Move Prover users a target vocabulary at the transition level rather than the function level. Typeclass-level Move support exists in the substrate today; production-grade semantic refinement analogous to the EVMYulLean composition for EVM is open work.

## CertiK and the CertiKOS lineage

CertiK was founded by Zhong Shao (Yale) and Ronghui Gu (Columbia) and evolved from the CertiKOS verified-kernel project. CertiK now offers runtime monitoring (Skynet), audits, and verified on-chain monitoring.

The intellectual heritage is similar to PARALLAX-5's: starting from formal-methods foundations, working toward operational deployment. The posture differs. CertiK's methodology and risk score are proprietary; PARALLAX-5's substrate is published under CC0 with structural non-capturability commitments. Where CertiK monetizes the methodology, AquaUrsa monetizes the commercial wrapper (Co-Pilot SaaS) over an open substrate.

The two are not directly competitive. CertiK customers who want a published obligation vocabulary their findings can be tagged with would benefit from PARALLAX-5 alongside their CertiK engagement.

## EVMYulLean

EVMYulLean is the production-grade Lean 4 formalization of the EVM developed by Nethermind. It achieves 99.99% Ethereum Foundation conformance test coverage on the Cancun fork.

PARALLAX-5 composes with EVMYulLean as the reference instance of the substrate's typeclass abstraction. The composition lifts 19 abstract refinement theorems to compiled proof terms over `EvmYul.EVM.State`. This is the central engineering claim of the integration verification artifact at [doi:10.5281/zenodo.20386868](https://doi.org/10.5281/zenodo.20386868) and the cleanest example of the substrate-semantic-refinement composition pattern that generalizes to other VM semantics.

`docs/EVMYUL_COMPOSITION.md` documents the composition methodology in detail.

## Operational security tooling

The static analyzers, symbolic executors, and fuzzing tools in common use across the DeFi audit ecosystem are not competitive with the substrate. They are tools that PARALLAX-5 certificates can cite as evidence, and tools that can adopt PARALLAX-5 obligation labels to improve composability of findings across the ecosystem.

| Tool | What it catches | Default obligation mapping |
|---|---|---|
| Slither (Trail of Bits) | Pattern-based static analysis: re-entrancy, uninitialized state, missing event emission | `reentrancy-eth` to A4; `arbitrary-send` to A2; `incorrect-equality` to A1 |
| Mythril (ConsenSys) | Symbolic execution: integer underflow, transaction-ordering dependence, exception state | underflow to A1; TOD to A4; exception state to A2 |
| halmos (a16z) | Symbolic property-based testing for Solidity | property witnesses to obligation-specific evidence |
| Foundry / forge | Property and invariant tests | invariants to A1, A2, A4 |
| Manticore (Trail of Bits) | Symbolic execution with concolic testing | counterexamples to obligation violation witnesses |
| Echidna (Trail of Bits) | Fuzzing for property violations | counterexamples to A1, A4 |
| Aderyn (Cyfrin) | AST-based static analysis (Rust) | detector outputs to obligation findings |

The reference mapping at `mappings/aquaursa-v1.json` covers Slither, Mythril, halmos, and ObligationSol. Authors can publish their own mappings under the `tool-mapping/{author}-v{major}` namespace following the process in `docs/MAPPING_PROTOCOL.md`. Trail of Bits authoring a `tool-mapping/trailofbits-v1` covering Manticore, Echidna, and slither-flat would formalize a long-standing implicit relationship between their tooling and obligation-level reasoning.

## AI safety landscape

Tegmark et al. (arXiv:2309.01933) articulated a research direction in 2023: AGI controllability runs through external containment systems with mathematical guarantees, rather than alignment via training. The substrate's AI-Agent Containment Theorem is a concrete mechanized instance of this thesis for a specific tractable slice. The agent operating behind the substrate's step-secure gate cannot violate the obligations regardless of policy. The result generalizes to any AI agent making decisions about money, tokens, NFTs, governance votes, or other value-bearing artifacts. It does not generalize to full AGI safety.

The relevant Lean theorem is `generic_agent_gate_preserves_security` at line 572 of `parallax/formal/lean/Parallax5.lean`. The proof composes with the adaptive-session-safety theorem at line 1093 to cover agents that learn from execution.

Anthropic's Constitutional AI methodology and Responsible Scaling Policy frame AI safety in terms of policy training and capability thresholds. The substrate operates at a different layer than CAI. CAI shapes an agent's policy through training; the substrate enforces transition-level bounds at runtime regardless of policy. The two compose. A Constitutional AI agent operating behind a substrate gate has endogenous safety properties from training and exogenous safety properties from the gate. For Anthropic-affiliated researchers, the substrate gate could serve as a per-deployment evaluation harness for ASL-3-plus agents acting on value-bearing state. `docs/AI_SAFETY_INTERPRETATION.md` covers this in detail.

OpenAI's Operator, DeepMind's SIMA, and similar broad-domain agentic systems are orthogonal to the substrate. The substrate does not constrain agency. It constrains value-bearing transitions an agent may propose. An Operator agent making purchases is a natural use case for a substrate gate; the gate adds no capability constraints and contributes mathematical bounds on outcomes.

## Regulatory standards

The EU AI Act (Regulation (EU) 2024/1689) enters enforcement on August 2, 2026. Annex III high-risk systems require conformity assessment with technical documentation, logging, transparency, human oversight, and accuracy/robustness/cybersecurity per Articles 11 through 15. PARALLAX-5 certificates contribute machine-checkable evidence for these articles. `docs/COMPLIANCE_MAPPING.md` provides the article-by-article mapping.

DORA (Regulation (EU) 2022/2554) has been in force since January 17, 2025. Articles 28 through 30 on ICT third-party risk management require formal documentation of automated decision-making in financial services. PARALLAX-5 certificates are the documentation artifact.

NIST AI Risk Management Framework 1.0 provides a US-aligned voluntary framework structured around Govern, Map, Measure, and Manage functions. PARALLAX-5 contributes to the Measure and Manage functions specifically.

ISO/IEC 42001:2023 is the international standard for AI management systems. PARALLAX-5 certificates serve as documented evidence for risk treatment under clause 6.1.4 and operational controls under clause 8.3.

## Substrate-design lineage

The "substrate over semantics" architectural pattern PARALLAX-5 uses has identifiable lineage in formal methods. Hoare logic (1969) separated proof rules from program semantics. Abstract interpretation (Cousot, 1977) separated abstract domains from concrete semantics. Separation logic (Reynolds, 2002) introduced modular reasoning about heap state. Iris (Jung et al., 2018) provided higher-order separation logic frameworks. K Framework (Roşu et al., 2010 onwards) demonstrated semantic frameworks with property-orthogonal tooling.

PARALLAX-5 contributes a specific instance of this pattern: an obligation substrate with VM-orthogonal tooling for value-bearing state transitions. The novelty is the specific obligation set (A1 through A5) chosen empirically from the 53-incident catalog, combined with the composition with production semantic refinement to yield concrete proof terms rather than abstract guarantees.

## What the substrate is not

The substrate is not a smart contract auditor; Slither, Mythril, halmos, Certora, and Trail of Bits Manticore occupy that role. The substrate is not a runtime monitoring system; CertiK Skynet, OpenZeppelin Defender, and Forta occupy that role. The substrate is not a property specification language; CVL, K, Solidity NatSpec, and Move Prover spec occupy that role. The substrate is not an AI training methodology; Constitutional AI, RLHF, and similar techniques occupy that role. The substrate is not a regulatory compliance certification; notified bodies under EU AI Act issue those.

The substrate is the formal vocabulary that any of the above can map findings to, so claims compose across tools, vendors, and runtime environments.

## Future work and collaboration

CROPS instances using alternative semantic refinements (K-Solidity, K-Move, K-Solana) would extend the substrate beyond the current EVM-only production refinement. `docs/EVMYUL_COMPOSITION.md` documents the methodology.

Additional tool mappings under the `tool-mapping/{author}-v{major}` namespace are welcome. `docs/MAPPING_PROTOCOL.md` documents the registration process.

Independent verification of the empirical catalog is open. `paper/FALSIFICATION_CHALLENGE.md` and `docs/CATALOG_METHODOLOGY.md` provide the falsification surface and the methodology for challenge.

Co-authorship on the v1.1 paper revision is available for substantive contributors in any of the above categories. Cold-email engagement is welcome at `research@aquaursa.ai`.

## How to position your work

For tools in smart-contract security, the substrate provides a published obligation vocabulary your findings can cite. Mapping is straightforward; `mappings/aquaursa-v1.json` is the reference example.

For AI agents acting on value-bearing state, a PARALLAX-5 gate is a complementary safety layer that operates independently of the agent's policy. `demos/agent_gate/` provides a worked example.

For runtime monitoring systems, PARALLAX-5 certificate state transitions give you a published lifecycle (issued, active, suspended, revoked, reissued) to integrate with.

For academic work in this space, the substrate cites Tegmark (2023), Sagiv (2018), Park, Roşu, and Stefanescu (2017), Shao (2018), and others. Reciprocal citation and explicit conversation about positioning are welcome.
