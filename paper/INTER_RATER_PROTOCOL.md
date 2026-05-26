# INTER_RATER_PROTOCOL.md

## PARALLAX-5 inter-rater agreement study — external human classification protocol

This document specifies the operational procedure that the PARALLAX-5 paper commits to in Section §16.1 (Inter-Rater Agreement) for validating the 53-incident catalog's obligation-classification consistency. The protocol is the external follow-on to the internal codebook-driven inter-rater harness already implemented at `parallax/formal/inter_rater.py`.

The internal harness reports a Cohen's $\kappa$ of $0.334$ between two automated reasoning orders. This is a disciplined internal lower bound; the protocol below is what is required to convert that lower bound into a credible external validation claim.

## Scope and falsifiability

This protocol is structured as a falsification test. Its pre-registered thresholds determine the catalog's validation status:

| Inter-rater Cohen's $\kappa$ (human-human) | Status |
|---|---|
| $\kappa \geq 0.6$ (substantial agreement) | Catalog classifications externally validated |
| $0.4 \leq \kappa < 0.6$ (moderate agreement) | Codebook refinement required; specific items flagged |
| $\kappa < 0.4$ (fair / poor agreement) | Codebook usability claim falsified; classification methodology must be revised |

The protocol commits to publishing all per-incident classifications, the full Cohen's $\kappa$ analysis (overall and per-axis), and any disagreement-resolution actions, regardless of outcome.

## Recruitment

**Eligibility.** Two independent classifiers, each meeting all of:
- Prior smart-contract security experience (audit-firm associate, academic researcher in the area, or two years post-bachelor's industry experience reviewing DeFi protocols).
- No prior involvement with the PARALLAX-5 codebook authorship.
- Willing to publish their individual classifications under attribution.

**Blinding.** Each classifier:
- Receives only `paper/CLASSIFICATION_CODEBOOK.md` as the procedure document.
- Receives the catalog's source materials (incident postmortems, on-chain transaction hashes, audit reports) but **NOT** the catalog's existing classifications.
- Submits classifications independently with no knowledge of the other classifier's outputs until the disagreement-resolution step.

**Compensation.** Pre-agreed at $1,500 per classifier for the full $n = 25$ stratified sample (approximately 6 hours of work at industry-standard consultancy rates), paid in fiat or stablecoin at the classifier's election. Compensation is **not** contingent on agreement outcomes.

## Sampling

A stratified random sample of $n = 25$ incidents drawn from the 53-incident catalog. Stratification ensures coverage of:

| Stratum | Population in catalog | Target sample |
|---|---|---|
| $A_1$-rooted (value conservation) | 24 | 12 |
| $A_2$-rooted (authorization) | 14 | 7 |
| $A_3$-rooted (signature integrity) | 4 | 2 |
| $A_5$-rooted (external attestation) | 11 | 4 |

The sampling is performed once by an uninvolved third party (e.g., an academic statistician), seed-bound, and published with the protocol's pre-registration.

## Classification instrument

Each classifier classifies each sampled incident on three axes:

1. **Root cause class** — which obligation $A_i$ is violated (one of $A_1, A_2, A_3, A_4, A_5$, or "compound" / "ambiguous").
2. **Basis-observability** — whether the violation's loss is recoverable from chain-observation alone ($\Omega_{\text{chain}}$), or requires off-chain context ($\Omega_{\text{off-chain}}$).
3. **Observation set assignment** — the minimal $\Omega_*$ that suffices for the loss to be recoverable.

Classifications are recorded in a structured CSV (template at `paper/supplement/inter_rater_template.csv`); free-text justifications are required for each.

## Disagreement resolution

After both classifiers submit independently, disagreements are surfaced and the protocol proceeds as follows:

1. **Per-axis disagreement inventory.** Compile every (incident, axis, classifier-A choice, classifier-B choice) tuple where the two classifiers differ.

2. **Codebook adjudication.** For each disagreement, the codebook itself is consulted; if the codebook unambiguously specifies which classification is correct, the codebook decides and the disagreement is recorded as a classifier error.

3. **Codebook-ambiguous cases.** If the codebook admits both classifications as defensible, the disagreement is recorded as **codebook-ambiguous**. These cases are the primary input to codebook refinement and are published separately.

4. **Disagreement publication.** All disagreements, their resolution category (classifier-error / codebook-ambiguous), and the resolution rationale, are published in the paper's revision following the inter-rater study.

## Analysis

The following statistics are computed and published:

- **Pairwise Cohen's $\kappa$**: human-A vs human-B (overall and per-axis).
- **Human-vs-catalog Cohen's $\kappa$**: each human vs the catalog's existing classifications.
- **Human-pair vs automated-pair**: the two human classifiers' agreement set vs the automated harness's (Classifier A / Classifier B from `parallax/formal/inter_rater.py`).
- **Per-axis decomposition**: $\kappa$ separately for root-cause class, basis-observability, and observation-set assignment.
- **Bootstrap 95% confidence intervals** on each $\kappa$ via 10,000 resamples.

All analysis code is published at `parallax/formal/inter_rater_external.py` (added in the paper revision that reports the external study).

## Timeline

The protocol is operational; the substrate commits to executing it within twelve months of the paper's first public deposit. Earlier execution is possible if funding or volunteer classifiers become available sooner. The substrate's public dashboard (parallax5.org or the GitHub README, when launched) tracks the execution status.

## Pre-registration

This protocol document is the pre-registration of the inter-rater study. Its publication at the time of the paper's first Zenodo deposit binds the substrate to the analysis pre-specified above. Any deviation from this protocol that occurs during execution must be disclosed in the paper revision that reports the study.

## Status

| Step | Status |
|---|---|
| Internal codebook-driven harness (lower bound, $\kappa = 0.334$) | Complete; see `parallax/formal/inter_rater.py` |
| Protocol pre-registration (this document) | Complete |
| Sampling (third-party, $n = 25$) | Pending |
| Classifier recruitment | Pending |
| Classification | Pending |
| Disagreement resolution | Pending |
| Analysis publication | Pending (target: within 12 months of v9.4 deposit) |

## Related artifacts

- Codebook: `paper/CLASSIFICATION_CODEBOOK.md`
- Internal harness: `parallax/formal/inter_rater.py`
- Catalog source: `paper/supplement/catalog.csv`
- Paper §16.1 (Inter-Rater Agreement): `paper/parallax-5.tex`
