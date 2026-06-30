# Tool Comparison

This document compares PARALLAX-5 to the operational smart-contract security tools in common use. It is for engineering leads at audit firms, runtime monitoring vendors, and AI safety platforms who need to position PARALLAX-5 against tools their teams already use.

The substrate is not competitive with any of the tools listed. The substrate provides the obligation vocabulary (A1 through A5) that findings from these tools can be tagged with, so that claims compose across tools, vendors, and runtime environments. A protocol audited with Slither plus Mythril plus Certora plus a manual review benefits from PARALLAX-5 as a unifying language; the substrate does not replace any of the four.

## Coverage by obligation

The table below summarizes which obligations each tool catches and at what depth. Depth values follow the CROPS scale: D0 (no coverage), D1 (heuristic), D2 (rule-based), D3 (semi-formal), D4 (formal property), D5 (Lean kernel-checked refinement).

| Tool | A1 Value | A2 Auth | A3 Sig | A4 Temporal | A5 Attest | Mapping doc |
|---|---|---|---|---|---|---|
| Slither (Trail of Bits) | D2 | D3 | D1 | D3 | D1 | `mappings/aquaursa-v1.json` |
| Mythril (ConsenSys) | D2 | D2 | D2 | D2 | D1 | `mappings/aquaursa-v1.json` |
| halmos (a16z) | D3 | D3 | D2 | D2 | D1 | `mappings/aquaursa-v1.json` |
| Foundry / forge | D3 | D2 | D2 | D2 | D0 | (community pending) |
| Manticore (Trail of Bits) | D3 | D2 | D2 | D2 | D0 | (community pending) |
| Echidna (Trail of Bits) | D3 | D1 | D0 | D2 | D0 | (community pending) |
| Aderyn (Cyfrin) | D2 | D2 | D1 | D2 | D1 | (community pending) |
| Certora Prover | D4 | D4 | D4 | D4 | D3 | (commercial pending) |
| Trail of Bits Manticore | D3 | D2 | D2 | D2 | D0 | (community pending) |
| ObligationSol (this work) | D3 | D3 | D3 | D3 | D2 | `mappings/aquaursa-v1.json` |
| PARALLAX-5 Lean refinement | D5 | D5 | D5 | D5 | D4 | n/a (the substrate itself) |

Depth values reflect the substrate's assessment of what each tool's published detectors achieve when integrated against typical EVM smart contract codebases. Specific deployments may achieve higher depth with custom rules, custom Certora specifications, or domain-specific tooling.

## Detector-level mapping (Slither example)

The reference mapping at `mappings/aquaursa-v1.json` defines the specific detector-to-obligation mapping for Slither. Selected entries (abbreviated):

```json
{
  "tool": "slither",
  "capability": {
    "A1": {
      "detectors": [
        "incorrect-equality",
        "weak-prng",
        "uninitialized-storage",
        "tautology"
      ],
      "depth": "D2"
    },
    "A2": {
      "detectors": [
        "arbitrary-send-erc20",
        "arbitrary-send-eth",
        "controlled-delegatecall",
        "tx-origin",
        "suicidal"
      ],
      "depth": "D3"
    },
    "A3": {
      "detectors": [
        "missing-zero-check"
      ],
      "depth": "D1"
    },
    "A4": {
      "detectors": [
        "reentrancy-eth",
        "reentrancy-no-eth",
        "reentrancy-benign",
        "events-access"
      ],
      "depth": "D3"
    },
    "A5": {
      "detectors": [
        "uninitialized-state"
      ],
      "depth": "D1"
    }
  }
}
```

The mapping is the public artifact that a Slither user can cite when issuing a PARALLAX-5 certificate. The detector list is not exhaustive; the mapping document at `docs/mappings/aquaursa-v1.md` explains which detectors are included and why others are excluded.

## What each tool is best at

Slither excels at fast static analysis with high signal-to-noise ratio on common vulnerability patterns. It is the standard first-line tool for any production audit. Its detectors are pattern-based; deep semantic properties require additional tooling.

Mythril performs symbolic execution to find arithmetic bugs, transaction-ordering vulnerabilities, and exception states. It is slower than Slither but catches a different class of issues. Its symbolic engine is the foundation for many other tools.

halmos applies symbolic execution to property-based testing for Solidity. It bridges between Foundry's invariant testing and full symbolic execution, providing a sweet spot for developers comfortable with Forge but wanting more rigorous verification of specific properties.

Foundry's forge framework provides property and invariant tests in a familiar developer workflow. It excels at protocol-specific testing where the developer knows the invariants and can express them in Solidity.

Manticore (Trail of Bits) and Echidna (Trail of Bits) are deeper-investigation tools used during specialized audits. Manticore performs symbolic execution with concolic testing. Echidna fuzzes for property violations. Both are heavyweight; both produce high-quality findings when used.

Aderyn (Cyfrin) is the newer Rust-based static analyzer. Its detector library is growing and includes patterns not in Slither's set. The Rust foundation makes it suitable for integration into Rust-based audit toolchains.

Certora Prover is the production-grade formal verifier. With a custom Certora Verification Language (CVL) specification, it can prove deep properties that other tools cannot. Engagement is consultant-driven and expensive ($30K to $100K per protocol); the result is a property satisfaction report with formal guarantees.

ObligationSol (developed within PARALLAX-5) is the included static checker that catches obligation violations directly. It is designed for fast obligation-level pre-screening before more expensive tools run.

The PARALLAX-5 Lean refinement is the substrate itself: kernel-checked theorem proofs over abstract state machines, composed with EVMYulLean to produce 24 compiled proof terms over production EVM state. This is the strongest depth (D5 for axioms A1 through A4; D4 for A5) but operates at the substrate level rather than the per-contract level.

## How tools compose

A typical full-coverage audit deploys multiple tools in sequence. The substrate gives a vocabulary for combining their outputs into a single coherent certificate.

Pre-screening at D1 to D2 uses Slither, ObligationSol, and Aderyn. These run in seconds to minutes and catch the majority of low-hanging fruit. Findings tagged with obligation labels feed into the certificate's evidence base.

Property verification at D3 uses halmos, Foundry invariants, and Echidna. These take minutes to hours and verify specific properties the developer cares about. Properties are tagged with the obligations they support.

Deep symbolic at D3 to D4 uses Mythril and Manticore. These can take hours to days for complex contracts. Findings and counterexamples are highest-quality evidence.

Formal verification at D4 to D5 uses Certora (with CVL specifications) or direct Lean proofs over EVMYulLean. These are commitment-driven; the engagement is large but the resulting certificate is the strongest possible.

The substrate's certificate format unifies findings from any combination of the above. A protocol can issue a P3 certificate based on Slither plus halmos plus Foundry, a P3+ certificate adding Mythril and Manticore, or a P5 certificate based on Certora plus EVMYulLean-Lean proofs. The certificate schema is at `schemas/certificate_v1.json`.

## Engagement cost comparison

For a protocol team evaluating which tools to use, the practical decision involves engineering time, tool cost, and depth required.

Slither, Mythril, halmos, Foundry, Aderyn, Echidna, and ObligationSol are open-source and free. Their engagement cost is engineering time only; expect 1 to 5 engineering days per tool to set up properly and analyze a non-trivial protocol.

Manticore is open-source but heavyweight; expect 2 to 10 engineering days plus computational resources.

Certora is commercial. Engagement is typically a paid consulting relationship rather than self-service. Expect $30K to $100K per protocol depending on complexity and the depth of specifications required. Engagement timeline is typically 4 to 12 weeks.

PARALLAX-5 substrate is open-source (Apache-2.0 for code, CC0 for Standard text, CC-BY-4.0 for paper). The substrate itself is free. The Co-Pilot SaaS is a commercial product at $10K (Individual), $50K (Team), or $100K (Enterprise) per year. The SaaS automates obligation analysis, certificate generation, and integration with the tools above.

## When PARALLAX-5 alone is sufficient

For development teams wanting to issue P1 certificates documenting their security posture without the full audit overhead, the substrate's ObligationSol checker plus the certificate generator at `parallax5-coordinator` produces a defensible certificate quickly. Total engineering time is 1 to 5 engineering days for the first certificate, then 1 to 2 hours per subsequent certificate.

P1 certificates are not equivalent to professional audits. They document that the protocol has been analyzed against the obligation framework with available open-source tooling. They are appropriate for low-risk protocols, for early-stage protocols seeking initial documentation, and for protocols supplementing a professional audit with continuous certification.

## When PARALLAX-5 plus existing tools is sufficient

For production protocols that already engage Slither, Foundry, Mythril, and similar tooling, adding PARALLAX-5 obligation labels to existing findings produces a P3 certificate. The substrate's role is to give the existing findings a unified vocabulary; the engineering cost is incremental.

P3 certificates are appropriate for production protocols at moderate value-at-risk, for protocols seeking EU AI Act or DORA compliance documentation, and for protocols whose customers or partners value the certificate format.

## When PARALLAX-5 plus Certora is required

For protocols at very high value-at-risk (treasury management, major lending protocols, cross-chain bridges with substantial TVL), a P5 certificate produced by combining PARALLAX-5 Lean proofs with Certora-verified properties provides the strongest possible assurance.

P5 certificates require commercial engagement with Certora (for the property verification) and with AquaUrsa (for the substrate-specific verification work, if the protocol requires custom integration). Total engagement cost typically ranges from $50K to $250K per protocol; engagement timeline is 8 to 16 weeks.

## Engagement

For tool authors interested in publishing a mapping for their tool, see `docs/MAPPING_PROTOCOL.md`. The community mappings track is open. Trail of Bits, OpenZeppelin, Cyfrin, and Certora are explicitly invited to author their own mappings rather than relying on the AquaUrsa-authored reference.

For audit firms interested in issuing PARALLAX-5 certificates as deliverables, see `docs/FOR_INTEGRATORS.md` Pattern 2.

For protocol teams evaluating which combination of tools to use, the Co-Pilot SaaS includes a depth-coverage calculator that recommends tool combinations for target depth and budget.

Contact `research@aquaursa.ai` for partnership conversations, mapping submissions, or commercial engagement.
