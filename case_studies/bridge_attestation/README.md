# Case Study 2: Cross-Chain Bridge — Generalized A5 in Action

**Goal**: Demonstrate the value of the generalized $A_5$ External-Attestation Trust Boundary by reproducing the Kelp DAO archetype (1-of-1 verifier configuration) and proving the hardened $q$-of-$n$ configuration satisfies $A_5$ at the bytecode level.

## The Vulnerability: 1-of-1 Verifier (Kelp DAO archetype)

The $292M Kelp DAO / LayerZero incident (April 2026) involved a bridge configured with a single Decentralized Verifier Network endpoint. When that endpoint was compromised via RPC poisoning + DDoS, an attacker submitted a forged message and the bridge released reserves.

Under the **v2 narrow A_5** (price-oracle-only), this incident would have been classified as off-chain infrastructure — outside the basis. Under the **v3 generalized A_5** (external attestation with quorum, diversity, freshness, manipulation-resistance against an adversary model Adv), the 1-of-1 verifier configuration is an A_5 violation at deploy/config time, and the malicious release is a $A_5$-detectable transition.

**Obligation signature**: σ(t) = {$A_5$} under generalized formulation.

## Reproduction: `Bridge1of1.t.sol`

The vulnerable bridge:
- `address public verifier` — SINGLE verifier, quorum size 1
- No diversity requirement
- No manipulation-resistance check
- Signature check passes (A_3 holds!) but A_5 fails

halmos verdict: **FAIL** — the harness `check_NoUnilateralRelease` finds the exploit: compromise the single key, submit any message, the bridge releases funds.

The signature is structurally valid (so A_3 alone cannot catch this); the bug is in the attestation *configuration*.

## The Patch: q-of-n Quorum + Diversity + Freshness

`BridgeQuorum.t.sol` enforces:

1. **Quorum** $q \geq 2$: rejected at construction if $q = 1$.
2. **Diversity** $n \geq 3$: rejected if verifier set too small.
3. **Freshness**: `block.timestamp - issuedAt <= maxAge`.
4. **Domain binding**: signed hash includes `domain || msgHash || issuedAt || to || amount`.
5. **Replay protection**: `consumed[msgHash]` mapping.
6. **No double-counting**: a single verifier's signature counted at most once.

halmos verdict on `check_NoUnilateralRelease`: **PASS** — a single compromised verifier cannot release funds.

## The PARALLAX-5 Certificate

This bridge can claim **P3** compliance (Symbolically Checked) at minimum. With Lean theorem `a5_compositional` (already discharged in `ParallaxAxioms.lean`), it can claim **P4**.

```json
{
  "compliance_level": "P4",
  "obligation_map": {
    "release(address,uint256,bytes32,uint256,bytes[])": ["A2", "A3", "A5"]
  },
  "proof_artifacts": {
    "A5": {
      "tool": "halmos",
      "verdict": "PASS",
      "paths_explored": 12,
      "configuration": {
        "quorum": 3,
        "diversity": 5,
        "domain": "PARALLAX-BRIDGE-V1",
        "max_age_seconds": 3600
      }
    }
  },
  "trust_base_assumptions": {
    "OA3_infrastructure_integrity": {
      "controls": [
        "verifiers run on 5 independent cloud providers",
        "independent RPC paths per verifier",
        "DNS DNSSEC on each provider",
        "quarterly key rotation per verifier"
      ]
    }
  }
}
```

## What This Case Study Demonstrates

1. **A_3 alone is insufficient** for bridge security. Per-signature integrity does not prevent compromise of a singleton verifier. Generalized A_5 is the right level.
2. **Configuration is in the basis**. The 1-of-1 verifier choice is itself a basis violation at deploy time, before any transaction.
3. **Diversity matters** beyond quorum. A_5 requires both $q \geq 2$ and the underlying verifier set to be independent (different cloud providers, jurisdictions, key custodians).
4. **Cost of A_5 compliance is bounded**. The hardened contract is ~50 lines longer than the vulnerable one, with explicit constructor-time guards.
5. **Backward compatibility with off-chain controls**. The certificate's `trust_base_assumptions.OA3` block records the operational controls (cloud diversity, DNSSEC, key rotation) — making the off-chain trust base auditable alongside the on-chain code.
