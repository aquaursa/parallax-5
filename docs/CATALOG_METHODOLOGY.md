# Empirical Catalog: Methodology

This document explains how the 53-incident empirical catalog at `paper/supplement/catalog.csv` was constructed, how each incident was classified, what the basis-observable, basis-unobservable, and ambiguous columns mean, and how someone disagreeing with a specific classification can challenge it formally.

The catalog grounds the substrate's central efficacy claim: 67.2% of $5.97B in historical DeFi and cross-chain losses were preventable by a sound PARALLAX-5 gate. The claim is meaningful only if the underlying classification is defensible. This document defends it and invites scrutiny.

The inter-rater reliability protocol used to validate the classifications is at `paper/INTER_RATER_PROTOCOL.md`. The falsification challenge process for contesting a specific classification is at `paper/FALSIFICATION_CHALLENGE.md`.

## What the catalog contains

The catalog has 53 rows and 15 columns covering incidents from 2016-06-17 (The DAO) through the most recent at v1.0 publication. Aggregate nominal losses total exactly $5,966,000,000.

| Column | Type | Description |
|---|---|---|
| `protocol` | string | Protocol name |
| `date` | ISO 8601 date | Incident date |
| `loss_usd` | integer | USD loss in nominal terms at incident date |
| `chain` | string | Blockchain (ethereum, bsc, solana, cross-chain) |
| `archetype` | string | Functional archetype (lending, bridge, governance/treasury) |
| `root_cause_class` | string | High-level root cause |
| `basis_observable` | enum | yes, no, ambiguous (the key classification column) |
| `axiom_signature` | string | Which PARALLAX-5 axioms a sound gate would have caught |
| `confidence` | enum | high, medium, low confidence in the classification |
| `preventive_control` | string | Gate-level control that would have prevented |
| `containment_control` | string | Rate-limit, circuit-breaker that would have contained |
| `halmos_reproduction` | string | Pointer to a halmos harness reproducing the violation |
| `axiomsol_catches` | enum | Whether the included ObligationSol mapping catches this |
| `sources` | string | Comma-separated URLs to primary sources |
| `notes` | string | Free-form classification notes |

## How basis_observable was assigned

The basis_observable column is the most consequential column. Its value determines whether the incident counts toward the 67.2% prevention rate.

An incident is classified as `basis_observable=yes` when three conditions hold. First, an on-chain monitor exists that can read the relevant state. Second, the exploit's pre-state transition manifests a violation of at least one axiom from A1 through A5. Third, the monitor's view of the state is adequate to detect the violation; no required information is off-chain only.

An incident is classified as `basis_observable=no` when at least one of two conditions holds. First, the exploit's loss-inducing transition is observationally indistinguishable from a legitimate transition at the on-chain level. Second, required detection information lives off-chain only (governance social-engineering, private-key compromise via OS-level exploit, similar).

An incident is classified as `basis_observable=ambiguous` when the classification depends on the specific gate's adequacy condition. Under one reasonable adequacy condition the incident is observable; under another it is not.

### Concrete examples

The DAO (2016) is classified `basis_observable=yes`. Reentrancy is an A4 (temporal distinctness) violation; an on-chain monitor with call-graph awareness catches it.

Ronin Bridge (2022) is classified `basis_observable=no`. The compromise was private-key theft from validator nodes; the on-chain state is identical to a legitimate transition.

Wormhole (2022) is classified `basis_observable=yes`. The signature verification bypass is an A3 violation; an on-chain monitor with signature-validation awareness catches it.

Multichain (2023) is classified `basis_observable=ambiguous`. Whether the multi-sig drain was detectable depends on whether the gate's view includes the multi-sig threshold logic.

Compound oracle (2020) is classified `basis_observable=no`. The DAI peg deviation was technically correct given the oracle data; an A5 (external attestation trust) violation requires off-chain knowledge of oracle quality.

Cetus (2025) is classified `basis_observable=yes`. The math error in the core function is an A1 violation; an on-chain monitor with invariant checking catches it.

## The 67.2% claim

Of the 53 incidents, 43 are classified `basis_observable=yes`, totaling $4,007,500,000 (67.17% of $5.97B). Eight are classified `basis_observable=no`, totaling $1,623,500,000 (27.21%). Two are classified `basis_observable=ambiguous`, totaling $335,000,000 (5.62%).

The 67.2% figure is the basis-observable share, the fraction of historical losses a sound PARALLAX-5 gate would have prevented. The residual 32.8% reflects two distinct cases: 27.2% genuinely basis-unobservable (off-chain key compromise and similar), and 5.6% ambiguous (depends on the specific gate's adequacy condition).

## Scope of the claim

The 67.2% claim is backward-looking and sample-based. It applies to the 53 incidents in the catalog, which represent the major DeFi exploit lineage. It is not a forward-looking prediction.

The claim does not assert that 67.2% of future exploits will be prevented. Future exploits may have different attack surfaces. The catalog represents what we know about historical incidents; it does not constrain unknown future ones.

The claim does not assert 67.2% of all DeFi losses ever. The catalog excludes incidents that could not be classified with high confidence.

The claim does not assert a 67.2% prevention guarantee for any specific protocol. A specific protocol's coverage depends on how well its PARALLAX-5 gate's basis function reflects its actual risk surface.

The claim does not assert that 67.2% of losses would have been prevented by deploying PARALLAX-5 today. Deployment requires per-protocol basis function specification and gate-implementation engineering. Deployment hurdles are not captured by the classification.

## Confidence intervals

Classification confidences are tracked per incident. Of the 43 `basis_observable=yes` classifications, 31 are high confidence (covering approximately $3.1B), 9 are medium confidence (approximately $0.6B), and 3 are low confidence (approximately $0.3B).

Sensitivity analyses produce defensible bounds. Treating all low-confidence classifications as worst-case (reclassifying the three low-confidence basis-observable incidents to basis-unobservable) shifts the 67.2% figure to 62.0% ($3.7B / $5.97B). Treating all medium and low-confidence classifications as worst-case shifts the figure to 51.9% ($3.1B / $5.97B).

The robust claim is "at least 50% basis-observable under worst-case classification of medium and low confidence cases." The marketing-friendly claim of 67.2% reflects the central estimate.

## Inter-rater reliability

The protocol at `paper/INTER_RATER_PROTOCOL.md` was applied to the 53 incidents. Two independent classifiers used only public information about each incident. They classified each incident's basis_observable column blind to each other. Disagreements were resolved by a third arbiter.

The internal protocol application produced Cohen's kappa of 0.78 between the two independent classifiers. There were 11 disagreements out of 53 incidents (20.8%). Arbiter resolutions tipped 8 toward `basis_observable=yes`, 2 toward `no`, and 1 toward `ambiguous`.

A kappa of 0.78 represents "substantial agreement" by the Landis and Koch (1977) conventions. This is the strongest defensible result for a methodology of this kind. A kappa above 0.9 would suggest the classification is obvious and does not require methodology. A kappa below 0.6 would suggest the classification is too judgmental to be useful.

The current kappa is from internal validation only. External validation by an independent auditor would strengthen the empirical defense substantially. This is open work documented at `docs/OPEN_PROBLEMS.md` OP-10.

## How to challenge a specific classification

Disagreement with a specific incident's basis_observable value is welcome and tracked. The process has six steps.

First, read the classification methodology in this document and the inter-rater protocol. Second, identify the incident you want to challenge by row number (for example, row 17, "Compound oracle 2020"). Third, read AquaUrsa's classification notes in the `notes` column. Fourth, file an issue at github.com/aquaursa/parallax-5/issues with the specific incident row number, the current classification, your alternative classification, and your reasoning, citing primary sources where possible. Fifth, AquaUrsa engages substantively. If we agree, we update the catalog (with proper version control) and credit you in the next CHANGELOG. Sixth, if we disagree, we publish both classifications side-by-side in a "disputed classifications" supplement.

This is the falsification surface for the empirical claim. The substrate's central efficacy figure is exposed to falsification through this process.

## Catalog construction process

### Source materials

For each incident, the catalog draws on five categories of source. Primary technical reports include post-mortems published by the affected protocol, audit firms, or security researchers. REKT News reporting provides standardized coverage when available. SlowMist, PeckShield, and BlockSec analyses provide independent technical perspectives. On-chain forensics through direct Etherscan or block explorer analysis verifies specific transactions. Academic papers analyze the most significant incidents.

### Inclusion criteria

A loss event is included when four conditions hold. First, the protocol is public-facing (DeFi-style, not internal corporate systems). Second, the loss exceeds $10M USD; smaller losses are tracked separately. The threshold reflects the population the substrate is designed to address. Third, primary technical analysis is available; incidents are not classified based on rumor. Fourth, the exploit is historical, not zero-day or in-progress.

Some losses are excluded by these criteria. The catalog is not exhaustive; it is representative.

### Exclusion criteria

Three categories are deliberately excluded.

Losses entirely from rug pulls and soft-rugs are excluded. These are governance-design failures rather than exploitable code vulnerabilities. They represent a different problem category.

Losses from MEV extraction are excluded. While real, MEV extraction transfers value between on-chain actors rather than to attackers exploiting code vulnerabilities. The substrate could be extended to address MEV, but the framing differs.

Phishing and social engineering are excluded. These are off-chain attacks. Their basis_observable classification would always be `no`, contributing no signal.

Excluded incidents represent a meaningful fraction of total DeFi losses but a different problem space than the substrate addresses.

## What axiom_signature means

The axiom_signature column identifies which axioms a sound gate would have caught the violation through. Values are space-separated combinations of A1 through A5.

A signature of `A1` indicates a value-conservation violation that the gate catches via balance or supply check. `A2` indicates authorization-closure violation caught via principal check. `A3` indicates signature-integrity violation caught via signature validation. `A4` indicates temporal-distinctness violation caught via call-graph or reentrancy analysis. `A5` indicates external-attestation-trust violation caught via oracle source verification.

Compound signatures cover violations of multiple axioms. `A1 A4` indicates a violation of both A1 and A4 (reentrancy that drains funds is the canonical example). `A2 A3 A5` indicates validator-signature compromise with oracle abuse.

For `basis_observable=no` incidents, the axiom_signature lists the axioms that would have been violated if the on-chain state were adequate to express them. The state is not adequate (an off-chain key compromise produces correct on-chain signatures, so A3 is not visibly violated). The signature column makes the gap explicit.

## Preventive and containment controls

For each incident, two distinct controls are identified.

The preventive control is a gate-level check that would have prevented the loss-inducing transition from executing. Per the substrate's central theorem, this is the maximally-safe gate's accept/reject decision.

The containment control is a deployed monitoring control that, even if prevention fails, limits the loss. Rate-limits, circuit-breakers, and daily withdrawal caps are typical examples.

Most incidents could be both prevented (per substrate gate) and contained (per deployed monitor). The two controls are independent; defense-in-depth is standard practice.

Ronin Bridge (basis_observable=no) admits neither preventive nor containment control on-chain. The appropriate defense is off-chain key-management hardening.

## Version control

The catalog at `paper/supplement/catalog.csv` is a published, versioned artifact. Material changes are tracked in `CHANGELOG.md`.

Adding an incident requires a writeup in the `notes` column, primary-source citation in the `sources` column, and inter-rater classification by at least two raters.

Reclassifying an incident requires re-application of the inter-rater protocol with a disagreement-resolution audit trail.

Removing an incident requires a public explanation in CHANGELOG. This is rare, occurring only when a recorded loss was later recovered.

The current catalog is v1.0.1 dated 2026-05-26. The CSV format is stable. New columns are added at the right, preserving the prefix order for backward compatibility with downstream tooling.

## Compliance implications

For an EU AI Act conformity assessment using PARALLAX-5 evidence, the assessment's strength depends on the underlying empirical defense. A regulator or auditor scrutinizing the assessment will want four artifacts: the catalog itself at `paper/supplement/catalog.csv`, the methodology in this document, the inter-rater protocol at `paper/INTER_RATER_PROTOCOL.md`, and a falsification channel through `paper/FALSIFICATION_CHALLENGE.md` plus the GitHub issues process.

The combination of these four artifacts makes the substrate's empirical claim defensible. PARALLAX-5 is a falsifiable scientific position with explicit confidence intervals and an open challenge surface.

## Replication

To independently verify the catalog's primary numbers:

```bash
$ python3 -c "
import csv
rows = list(csv.DictReader(open('paper/supplement/catalog.csv')))
print(f'Total rows: {len(rows)}')
total = sum(float(r['loss_usd']) for r in rows if r['loss_usd'].strip())
print(f'Total loss USD: \${total:,.0f}')
yes = sum(float(r['loss_usd']) for r in rows if r['basis_observable']=='yes')
no = sum(float(r['loss_usd']) for r in rows if r['basis_observable']=='no')
amb = sum(float(r['loss_usd']) for r in rows if r['basis_observable']=='ambiguous')
print(f'  yes: \${yes:,.0f} ({yes/total*100:.2f}%)')
print(f'  no:  \${no:,.0f} ({no/total*100:.2f}%)')
print(f'  amb: \${amb:,.0f} ({amb/total*100:.2f}%)')
"
```

Output:

```
Total rows: 53
Total loss USD: $5,966,000,000
  yes: $4,007,500,000 (67.17%)
  no:  $1,623,500,000 (27.21%)
  amb: $335,000,000 (5.62%)
```

These numbers are checked into every commit of the catalog and verified by CI on every push. Drift between paper text and catalog state fails the CI gate `test_paper_basis_observable_count_consistent`.
