# PARALLAX-5 Product Tiers


## Free / Open

Everything required to adopt and use PARALLAX-5. Permanently free; code is Apache-2.0 and standard text is CC0.

- The standard (PARALLAX-5-Standard.md)
- JSON Schema (Draft 2020-12)
- CLI: `parallax5` (validate, init, score, quote, doctor, catalog, schema, example, trust-surface, serve)
- 53-incident empirical catalog
- Example certificates (5 archetypes)
- GitHub Action for CI validation
- Local trust-surface server (`parallax5 serve`)
- Lean theorems, halmos contracts, Z3/CVC5/Yices2 SMT models
- The academic paper

**Purpose**: adoption velocity. The standard is worthless if it's gated.

## Professional

For protocol teams, audit firms, and insurance underwriters.

- Hosted certificate registry with custom domain (e.g., `myprotocol.parallax5.io`)
- Continuous monitoring: any change to source triggers a revalidation alert
- Certificate-versioning UI with diff between versions
- Insurance-quote API with confidential parameters
- Audit-to-certificate conversion service (input: narrative audit; output: P-level certificate)
- Premium support and SLA
- Private SVG badge endpoints with usage analytics
- Standards bridge: automated conversion from EthTrust / SCSVS / ToB reports

**Pricing model**: per-certificate or annual subscription. Typical: \$5–25K per protocol per year.

**Purpose**: capture revenue from protocols and auditors who need more than the open tooling provides.

## Enterprise / P5

For protocols deploying runtime gates and AI-agent platforms enforcing PARALLAX-5 at execution time.

- Runtime step-secure gate SDK (Solidity + Move + Solana SBPF)
- Pre-transaction simulator: every tx is dry-run against the basis before signing
- AI-agent transaction firewall: wraps the agent's action set, enforces gate
- Insurer integration API: real-time certificate state + premium adjustments
- Custom proof integrations (Certora, ToB, internal verifier)
- Dedicated technical support
- Co-development of new obligations or observation sets
- Compliance attestation for regulatory filings

**Pricing model**: annual subscription + per-tx or per-execution fee.

**Purpose**: serious revenue. Comparable: Fireblocks, Forta, Chainalysis.

## Tier comparison

| Capability | Free | Professional | Enterprise |
|---|---|---|---|
| Schema validation | ✓ | ✓ | ✓ |
| CLI tools | ✓ | ✓ | ✓ |
| GitHub Action | ✓ | ✓ | ✓ |
| Self-hosted registry | ✓ | ✓ | ✓ |
| Hosted registry | — | ✓ | ✓ |
| Continuous monitoring | — | ✓ | ✓ |
| Insurance quote API | — | ✓ | ✓ |
| Audit-to-cert conversion | — | ✓ | ✓ |
| Runtime gate SDK | — | — | ✓ |
| Pre-tx simulator | — | — | ✓ |
| Agent transaction firewall | — | — | ✓ |
| Custom proof integration | — | — | ✓ |
| Co-development | — | — | ✓ |

## Pricing principles

- **Open standard, paid tooling.** The standard itself is never gated.
- **No artificial limits.** Free-tier limits exist only where infrastructure has marginal cost (e.g., hosted-registry bandwidth).
- **Insurance-aligned.** Tier price scales with the value the customer protects.
- **Reproducibility-first.** Even Enterprise customers get full reproducibility — no proprietary verdicts.

## Why this works commercially

The Free tier captures developer mindshare without revenue extraction. Professional captures incremental value for protocols that have outgrown self-hosting. Enterprise captures the per-execution premium associated with on-chain runtime enforcement and AI-agent gating — comparable to how Fireblocks charges per-transaction for hot-wallet security.

Total addressable market: see [MARKET_THESIS.md](MARKET_THESIS.md). Steady-state ARR: \$100–500M across all three tiers, with Enterprise providing the bulk of revenue.
