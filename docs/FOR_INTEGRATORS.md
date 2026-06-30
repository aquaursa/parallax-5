# For Integrators

This document is for engineering leads at audit firms, runtime monitoring vendors, AI safety platforms, and security tooling companies considering integration of PARALLAX-5 into their products. It assumes familiarity with smart-contract security tooling at the level of Slither and Certora.

The document covers three integration patterns: tool-mapping integration, certificate-issuing integration, and runtime-gate integration. Each is independently useful; many integrators adopt two or three over time.

## Pattern 1: Tool-mapping integration

This pattern suits audit firms (Trail of Bits, OpenZeppelin, ChainSecurity, Cyfrin, Spearbit, Certora, CertiK) and static analyzer vendors (Slither, Mythril, Aderyn). The concept is straightforward: a tool already produces findings tagged with detector names and severity. The integration adds a layer mapping each finding to a PARALLAX-5 obligation label (A1 through A5).

This is the lowest-friction integration available. No changes to existing detection logic are required. The integration adds metadata to the output format. Customers receive findings tagged with a published obligation vocabulary that survives switching tools or auditors.

The implementation has four steps. First, read the reference mapping at `mappings/aquaursa-v1.json`. This maps Slither, Mythril, halmos, and ObligationSol findings to obligation labels. An engineer spends roughly an hour with it. Second, author a mapping in the `tool-mapping/{your-name}-v1` namespace. The schema is at `schemas/mapping_protocol_v1.json`; the registration protocol is in `docs/MAPPING_PROTOCOL.md`. A typical mapping document is 100 to 300 lines of structured JSON. Third, submit a pull request to `aquaursa/parallax-5` adding your mapping to `mappings/` and your mapping document to `docs/mappings/`. The 11-test fire-test suite at `tests/test_mapping_registry.py` validates the mapping against the schema automatically. Fourth, update the tool's output format to emit obligation labels alongside existing finding metadata. Most tools do this via a `--output-format=sarif-parallax5` flag or equivalent, requiring 50 to 200 lines of code in the tool itself.

Total engineering cost is one to three engineering days: four to eight hours authoring the mapping, four to sixteen hours extending the tool's output format, two to four hours updating documentation. Pull request turnaround is typically less than one week once submitted. After merge, the mapping is queryable through `parallax5 capability --mapping tool-mapping/{your-name}-v1` and discoverable via `parallax5 capability --list-mappings`.

The return on this investment includes composability of findings (any combination of tools tagged with PARALLAX-5 labels can be aggregated by axiom), customer-facing certificate issuance (your customers can issue PARALLAX-5 certificates citing your tool's evidence), public visibility in the canonical mapping registry, and joint marketing opportunities for substantive partnerships.

For a Slither example, the `aquaursa-v1` mapping declares (simplified):

```json
{
  "tool": "slither",
  "capability": {
    "A1": {
      "detectors": ["incorrect-equality", "weak-prng", "uninitialized-storage"],
      "depth": "D2"
    },
    "A2": {
      "detectors": ["arbitrary-send-erc20", "controlled-delegatecall", "tx-origin"],
      "depth": "D3"
    },
    "A4": {
      "detectors": ["reentrancy-eth", "reentrancy-no-eth", "events-access"],
      "depth": "D3"
    }
  }
}
```

A Trail of Bits-authored mapping at `tool-mapping/trailofbits-v1` could add Manticore findings, Echidna invariants, and slither-flat findings to this schema. Submission formalizes the long-standing implicit relationship between ToB's tooling and obligation-level reasoning.

## Pattern 2: Certificate-issuing integration

This pattern suits audit firms, formal verification consultancies, and runtime monitoring vendors that want to issue PARALLAX-5 certificates as deliverables. After an audit or assurance engagement, the integrator issues a certificate (19-field JSON document, optionally on-chain-anchored) attesting to the protocol's compliance with one or more obligations at a specific depth.

This is the most operationally valuable integration. A "ChainSecurity audit plus PARALLAX-5 P3 certificate" deliverable is materially more valuable than an audit alone because the certificate is machine-checkable and on-chain-anchorable.

Implementation has five steps. The first is reading the certificate schema. `schemas/certificate_v1.json` defines the 19 fields; `docs/CERTIFICATE_SCHEMA.md` is the human-readable narrative. Second, decide the issuing depth. The four-level scheme is P1 (audit-style review), P3 (semi-formal verification with property tests), and P5 (Lean kernel-checked refinement). Most audit firms initially issue at P3. Third, implement the issuance pipeline. The `parallax5 certify` CLI in `parallax5-coordinator` is the reference implementation. It takes the contract bytecode, findings from one or more tools in the tool's native format, a mapping namespace, and the issuing organization's signing key, and emits a certificate. Implementation is 200 to 500 lines of integration code for most audit firms. Fourth, set up signing infrastructure. Each certificate is signed with the issuer's Ed25519 key. For audit firms, this is typically a dedicated certificate-signing key with HSM backing. Fifth, optionally anchor certificates on-chain through the `ParallaxRegistry` contract. The Sepolia reference deployment is at `0x8015A98dF9037Cd79a03B291a6fF3C2841992D5b`. Mainnet deployment is planned; until then, Sepolia-anchored certificates are valid evidence (the schema treats testnet anchoring as `attestation_strength = development`).

Total engineering cost is one to three engineering weeks: four to eight hours understanding the data model, two to five engineering days for the integration code, one to three engineering days for signing infrastructure (depending on existing key management), one to two engineering days for the optional on-chain registry integration.

Most audit firms issue their first PARALLAX-5 certificate within 30 days of starting integration. After the initial setup, certificate issuance per engagement adds one to two hours to an existing audit process.

The return on investment includes a machine-checkable deliverable customers can verify against the issuer's published public key, differentiation from non-certificate-issuing competitors, an on-chain audit trail with cryptographic provenance, and compliance positioning. PARALLAX-5 certificates map to EU AI Act and DORA evidence requirements, as documented in `docs/COMPLIANCE_MAPPING.md`.

For a complete worked example, see `examples/certificate_uniswap_v3_core.json`. The certificate is the entire deliverable. Anyone with the issuer's public key can verify it independently. Anyone with the bytecode and tool outputs can reproduce the evidence.

## Pattern 3: Runtime-gate integration

This pattern suits AI safety platforms (Cisco AI Defense, CyberArk Conjur, the post-Robust-Intelligence successor lineage), runtime monitoring vendors (CertiK Skynet, OpenZeppelin Defender, Forta), and developers building bespoke AI agent infrastructure. The concept is runtime enforcement: before an AI agent or smart contract executes a value-bearing transition, the PARALLAX-5 gate evaluates whether the transition satisfies the obligations. If yes, accept. If no, reject.

This is the highest-value integration. It converts the substrate from documentation evidence into a runtime control plane. A runtime-gated AI agent has mathematical bounds on what it can do, independent of its policy.

Implementation has five steps. First, read the worked example at `demos/agent_gate/`. This is a complete end-to-end implementation: Lean proof at `demos/agent_gate/proof/Containment.lean`, Solidity reference contract at `demos/agent_gate/AgentGate.sol`, Python driver at `demos/agent_gate/driver.py`. Second, define the basis function. The gate is parameterized by a function capturing the value being preserved. For an AI agent making token transfers, the basis is the token balance vector. For a governance proposal evaluator, the basis is the protocol state plus voting outcomes. Third, implement the obligation predicates for the runtime. Five predicates, one per obligation, each returning a boolean given the pre-state, transition, and post-state. Most predicates run 20 to 100 lines of code. Fourth, wire into the runtime. The gate's API is direct:

```python
accepted = gate.evaluate(
    pre_state=current_state,
    proposed_transition=agent_proposal,
    basis_fn=lambda s: protocol_invariants(s)
)
if accepted:
    execute(agent_proposal)
else:
    reject_with_reason(gate.last_failure)
```

Fifth, optionally issue runtime certificates. For each accepted transition, optionally emit a runtime PARALLAX-5 certificate attesting to the gate's evaluation. This produces an on-chain or off-chain audit trail of every value-bearing decision the AI agent made.

Total engineering cost is three to six engineering weeks: one to two engineering days reading and understanding the worked example, two to five engineering days defining the basis function for the protocol, one to two engineering weeks implementing obligation predicates, three to ten engineering days wiring into the runtime depending on existing architecture, two to five engineering days for performance optimization to achieve sub-millisecond gate evaluation.

The gate adds 0.1 to 5 milliseconds overhead per transition depending on the basis function complexity and obligation predicate complexity. This is typically negligible relative to network latency for on-chain transactions and acceptable for off-chain AI agent decisions.

For Cisco AI Defense specifically, the gate slots in between the policy decision point and the policy enforcement point in the standard runtime architecture. The gate adds mathematical bounds on what the policy can authorize, complementing the policy's learned bounds.

The return on this investment includes mathematical guarantees on agent behavior regardless of policy training, compliance evidence for EU AI Act Article 14 (human oversight) and Article 15 (cybersecurity, robustness), a defensible answer to "what if the AI does something unexpected?" (by construction, it cannot violate the obligations), and a per-transition audit trail through runtime certificates for post-hoc analysis.

For a concrete example, consider an LLM-based agent authorized to spend up to $1000 per day from a treasury account, deployed behind a PARALLAX-5 gate. The agent proposes a transfer of 500 USDC to address X. The gate evaluates A1 (does the transfer preserve the treasury's relevant invariants? yes, treasury -500, X +500, total preserved), A2 (is the agent authorized? yes, within daily budget), A4 (is this transition replay-distinct? yes, unique nonce), and A5 (does the agent's view come from sound sources? yes, chain-state read directly). The gate emits ACCEPT. The transaction executes; a runtime certificate is optionally emitted.

If the agent later proposes a transfer that would violate A2 (exceeds daily budget) or A4 (reuses a nonce, suggesting a replay attack from a malicious wrapper), the gate emits REJECT and the transaction does not execute. The agent's policy can be any LLM, any RL agent, or any rule-based system. The gate's decision is independent of the policy.

## Integration matrix

| Pattern | Suited for | Engineering cost | Time to first value | Recurring effort |
|---|---|---|---|---|
| Tool-mapping | Audit firms, static analyzers | 1-3 days | 1 week | Low (annual mapping updates) |
| Certificate-issuing | Audit firms, FV consultancies | 1-3 weeks | 30 days | Per-engagement (~2h) |
| Runtime-gate | AI safety platforms, runtime monitors | 3-6 weeks | 60-90 days | Ongoing (operational) |

Most integrators start with Pattern 1 (lowest cost, clearest value), then add Pattern 2 as customer demand emerges, then evaluate Pattern 3 for the most ambitious deployments.

## Partnership engagement

For audit firms and tooling vendors, the open-source substrate is freely usable without engagement. The reference mapping at `aquaursa-v1` is in the canonical registry as a public good. For commercial Co-Pilot SaaS subscriptions, see parallax.aquaursa.ai. For joint case studies, mapping document publication, and co-branded compliance materials, contact `research@aquaursa.ai`.

For AI safety platforms (Cisco AI Defense and similar), the same open-source posture applies. Substantive engineering integration benefits from a formal partnership agreement. For exploratory conversation about runtime-gate integration, the Singer, Sampath, or Gillis cold-email channel is open. Contact `research@aquaursa.ai`.

For Big 4 firms (Deloitte, PwC, KPMG, EY), see `docs/COMPLIANCE_MAPPING.md` for the regulatory-evidence framing. For Big 4 partnerships, contact `research@aquaursa.ai`.

For research collaborators, `docs/OPEN_PROBLEMS.md` lists the explicit research roadmap. Co-authorship on v1.1 and later paper revisions is open to substantive contributors.

## Scope notes

Custom integration consulting fees are case-by-case. Contact AquaUrsa for specifics.

AquaUrsa is not a notified body or accredited certifier. For binding regulatory certifications, work with your accredited auditor.

SLA terms for the SaaS Co-Pilot are documented in the Enterprise MSA template. The substrate is structurally non-capturable (no AquaUrsa patent claims). For tooling around the substrate, standard commercial indemnity terms apply per MSA.

## Reference adopters

The adopter list is empty at v1.1.0 launch. As adopters integrate, they will be listed here with their explicit permission. Earliest adopters receive joint case-study positioning, named mention in the v1.1 paper revision, and priority on Co-Pilot SaaS feedback channels.
