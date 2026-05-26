# PARALLAX-5 Basis Counterexample Challenge

> The framework is intentionally falsifiable. We invite the community to attempt to refute it.

## The challenge

Find a transition $t$ in a real or model value-bearing system and a world state $w$ such that:

$$\mathrm{TrustBase}(w) \wedge \mathrm{Loss}(t, w) \wedge B(t)$$

That is:
1. The trust base holds (no off-chain key/signer/infrastructure failure).
2. The transition produces protected-value loss.
3. The transition satisfies all five obligations: $A_1$, $A_2$, $A_3$, $A_4$, $A_5$.

A confirmed counterexample either:
- Refines the basis: a sixth obligation must be added or one of the five must be sharpened.
- Refines the observation set: the loss was outside the declared $\Omega$ — the framework is sound under stated $\Omega$ but the practical $\Omega$ must be enlarged.
- Refines the adequacy assumption: the basis is sound for a narrower class than claimed.

In all cases, the framework is strengthened, not invalidated.

## Submission format

```json
{
  "challenge_id": "self-assigned UUID",
  "submitted_at": "2026-MM-DDTHH:MM:SSZ",
  "submitter": "did:web:your.org",

  "transition": {
    "protocol": "name or model",
    "pre_state_description": "...",
    "transition_description": "what the candidate transition does",
    "post_state_description": "...",
    "loss_description": "what value was lost; magnitude if applicable"
  },

  "trust_base_check": {
    "OA1_key_integrity_held": true,
    "OA2_signer_sovereignty_held": true,
    "OA3_infrastructure_integrity_held": true,
    "evidence": "..."
  },

  "five_obligation_check": {
    "A1_value_conservation": {"satisfied": true, "evidence": "..."},
    "A2_authorization_closure": {"satisfied": true, "evidence": "..."},
    "A3_signature_integrity": {"satisfied": true, "evidence": "..."},
    "A4_temporal_distinctness": {"satisfied": true, "evidence": "..."},
    "A5_external_attestation": {"satisfied": true, "evidence": "..."}
  },

  "observation_set_used": "Ω_chain | Ω_config | Ω_intent | Ω_infra",

  "reproducibility": {
    "code": "URL or attachment",
    "tool_outputs": ["sha256:..."]
  }
}
```

## Review process

1. **Triage** (≤7 days): The reference issuer reviews completeness.
2. **Replication** (≤30 days): Two independent reviewers attempt to reproduce.
3. **Adjudication** (≤60 days): A panel decides:
   - **Confirmed**: framework is refined, all certificates issued against the refuted basis are flagged for revalidation.
   - **Rejected**: counterexample documented as "considered, not refuting" with public reasoning.

All submissions and adjudications are public.

## Bounty

We offer a community bounty for the first three confirmed counterexamples:

| Order | Bounty | Notes |
|---|---|---|
| 1st | (TBD — sponsorship-dependent) | First refutation reshapes the framework |
| 2nd | (TBD) | Confirms that the first was not a one-off |
| 3rd | (TBD) | Confirms that the framework has remaining failure modes |

A symbolic bounty (e.g., $1) preserves the falsifiability commitment even before sponsorship. **No legitimate confirmed counterexample will be ignored regardless of bounty status.**

## What counts as a refutation

**Yes**:
- A real-world incident where the basis was respected, all obligations satisfied, the trust base held, and value was lost
- A model-world transition that satisfies all formal predicates in our Lean module but causes loss in the operational semantics
- An empirical demonstration that one of our 53 catalog entries was misclassified

**No**:
- An exploit where the trust base failed (off-chain key compromise) and the on-chain consequence was basis-observable (Resolv-style) — this is a basis hit, not a miss
- An exploit at $\Omega < \Omega_{\mathrm{used}}$: e.g., showing a DNS hijack defeats an $\Omega_{\mathrm{chain}}$ monitor — the framework already labels this $\Omega_{\mathrm{infra}}$-unobservable
- A novel attack on a protocol whose certificate explicitly excluded the relevant component in `known_exclusions`

## Current status

| Status | Count | Total Loss |
|---|---|---|
| Confirmed refutations | **0** | **\$0** |
| Considered, not refuting | 53 (catalog) + 13 (forward-test) | \$6.69B |
| Pending review | 0 | — |

Last updated: 2026-05-25.

## How to submit

Open an issue at the project repository (URL omitted for review version) titled `[CHALLENGE]` with the JSON submission as the body.

Or email the canonical PARALLAX-5 issuer DID with subject `[CHALLENGE] <challenge_id>`.

---

The challenge is permanent. As the framework gains adoption, the bar for refutation will rise — confirmed counterexamples will become rarer and more valuable, in the same way that CVE-worthy bugs in well-audited cryptographic libraries become rarer and more valuable over time. The challenge mechanism keeps the framework honest.
