# PARALLAX-5 Catalog Classification Codebook

> Per external review §6. For replicable empirical classification.

## Purpose

The 53-incident catalog assigns each incident two axes (root cause and basis-observability) plus the observation set required for monitor coverage. To transform this from "author-created evidence" into "reproducible empirical dataset," independent reviewers must be able to replicate the classifications using only the codebook and public source material.

## Classification axes

### Axis 1 — Root cause

| Code | Meaning | Examples |
|---|---|---|
| `on-chain` | Bug in deployed contract code | Reentrancy, integer overflow, share-inflation |
| `off-chain-key` | Private key compromise | Stolen multisig key, KMS access |
| `off-chain-signer` | Social engineering of authorized signer | DPRK campaigns, phishing |
| `off-chain-infra` | Infrastructure compromise | DNS hijack, RPC, validator-node |
| `mixed` | Multiple roots material to the loss | Drift = signer + on-chain config |

### Axis 2 — Basis-observability (under stated $\Omega$)

| Code | Meaning |
|---|---|
| `yes` | A sound monitor under stated $\Omega$ would reject the malicious transition |
| `ambiguous` | Classification depends on monitor design choices |
| `no` | No monitor under stated $\Omega$ can reject without false-positives |

### Axis 3 — Minimum required observation set (new)

| $\Omega$ | Required information |
|---|---|
| `chain` | On-chain state + transaction data only |
| `config` | + declared protocol configuration (quorum, oracle sources, admin policy) |
| `intent` | + signer intent, governance proposal metadata, session policy |
| `infra` | + external infrastructure (KMS, RPC, DNS health) |
| `infra-` | Genuinely irreducible: no monitor at any Ω can resolve |

## Classification procedure

For each incident, the classifier:

1. **Reads the published postmortem** (e.g., Chainalysis, project blog, Halborn) — only public material.
2. **Identifies the root cause** using Axis 1.
3. **Identifies the loss-inducing transition** — the on-chain action that produced the loss.
4. **Determines whether a sound monitor would have rejected** the transition.
5. **Determines the minimum $\Omega$** required: what information would the monitor have needed?
6. **Records the obligation signature** $\sigma(t) \subseteq \{A_1, A_2, A_3, A_4, A_5\}$ — which obligations the transition violated.
7. **Assigns confidence** (high / medium / low) based on quality of public postmortem.

## Worked example — Drift Protocol

| Step | Outcome |
|---|---|
| Root cause | `off-chain-signer` (DPRK social engineering of multisig signers) |
| Loss-inducing transition | Whitelist CVT token as collateral, deposit 500M CVT, borrow against it |
| Sound monitor would reject? | Depends on $\Omega$ |
| Minimum $\Omega$ | `config` (the declared collateral-onboarding policy requires multi-stage review + time delay; the transition skipped these) |
| Obligation signature | $\sigma(t) = \{A_2, A_5\}$ (unauthorized listing under the declared policy; oracle for newly-listed asset has no diversity) |
| Confidence | High (detailed Chainalysis postmortem) |

## Decision rules for hard cases

### When is the root cause "mixed"?

Apply the **counterfactual test**: would the loss have occurred if any one root cause were absent?
- If yes for any one root: not mixed; assign the dominant root.
- If no for all: mixed.

Drift example: even with the signer compromise, if the declared collateral policy had been enforced on-chain (e.g., 14-day delay), the loss would not have occurred. So the signer compromise alone is not sufficient → `mixed`. We classify as `off-chain-signer + on-chain-config-missing`.

### When is basis-observability "ambiguous"?

Apply the **monitor-class disjunction test**: does the answer change across monitor classes?
- If yes (some monitor classes would reject, others not): `ambiguous`. Record the minimum $\Omega$ that resolves it.
- If no (all sound monitor classes agree): definite `yes` or `no`.

### When is loss "irreducible" (infra-unobservable)?

Apply the **trust-base-violation test**: does the only path to detection require the monitor to assume a piece of the trust base is wrong?
- CoW Swap: detection requires the monitor to know DNS is hijacked, which is a trust-base assumption. Irreducible.
- Mango Markets oracle: detection requires the monitor to know declared deviation bounds — that's $\Omega_{\mathrm{config}}$, not a trust-base assumption. Not irreducible.

## Inter-rater agreement plan

We plan to recruit two independent classifiers and compute Cohen's $\kappa$ on each axis.

- **Target**: $\kappa \geq 0.75$ on the basis-observability axis (substantial agreement).
- **Target**: $\kappa \geq 0.85$ on the root-cause axis (near-perfect agreement).
- **Disagreement protocol**: any disagreement triggers a three-way adjudication with all classifiers visible; the adjudicated classification is published; the disagreement itself is published with reasoning.

## Reviewer eligibility

Eligible reviewers:
- Smart-contract auditors (≥3 published audits)
- Formal-methods researchers (≥1 published paper in PL/security)
- DeFi protocol engineers (≥2 years deployed-protocol experience)

Conflicts of interest are declared and published. Reviewers may not classify incidents affecting protocols they have audited or are employed by.

## How to participate

Open an issue at the project repository titled `[CODEBOOK]` with your role, credentials, and proposed classifier role. Or email the reference issuer.
