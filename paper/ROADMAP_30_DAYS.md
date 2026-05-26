# PARALLAX-5 30-Day Adoption Roadmap

> Per external review §19. The next 30 days of execution.

## Week 1 — polish & consistency

**Status: ✓ complete in this build.**

- [x] Harmonized theorem/test counts across paper (70 Lean, 115 Python)
- [x] Fixed basis-observable count sentence (5 entries, Drift separately ambiguous)
- [x] Fixed ambiguous-loss math (Option A: ambiguous treated as residual)
- [x] Removed reviewer-version language (Per round-2 item N, etc.)
- [x] Shortened abstract (focused on formal + empirical, deferred commercial)
- [x] Moved market thesis to separate document
- [x] Added mechanical regression tests pinning paper counts to artifact state

## Week 2 — standard & artifact

**Status: ✓ complete in this build.**

- [x] JSON Schema (Draft 2020-12) — `paper/supplement/parallax5_certificate.schema.json`
- [x] Example certificates (5 archetype certs + 1 canonical) — all validate
- [x] CLI installs cleanly via `pip install parallax5`
- [x] GitHub Action — `.github/actions/parallax5/action.yml`
- [x] QUICKSTART (60s / 5min / 30min paths)
- [x] Artifact map in paper §13

## Week 3 — empirical credibility

**Status: partial in this build, completion plan documented.**

- [x] Per-incident source URLs (catalog.csv)
- [x] Confidence labels (high / medium / low) per incident
- [x] Bootstrap 95% confidence intervals computed
- [x] [CLASSIFICATION_CODEBOOK.md](CLASSIFICATION_CODEBOOK.md) for replication
- [ ] Two independent reviewers re-classify the 53 incidents
- [ ] Inter-rater agreement reported (Cohen's κ target ≥ 0.75)
- [ ] Disagreements published with adjudication

External recruitment is required for the last three items. The codebook makes the work concrete.

## Week 4 — adoption package

**Status: partial in this build.**

- [x] One-page executive summary — `paper/EXECUTIVE_SUMMARY.md`
- [x] Practitioner guide — `paper/PRACTITIONER_GUIDE.md`
- [x] Before/after audit example — `paper/supplement/before_after/`
- [x] Public falsification challenge — [FALSIFICATION_CHALLENGE.md](FALSIFICATION_CHALLENGE.md)
- [x] Standards comparison — [STANDARDS_COMPARISON.md](STANDARDS_COMPARISON.md)
- [x] Vision document — [VISION.md](VISION.md)
- [x] Governance & lifecycle — [GOVERNANCE.md](GOVERNANCE.md)
- [x] Product tiering — [PRODUCT_TIERS.md](PRODUCT_TIERS.md)
- [ ] **Outreach list**: ≤10 named contacts at audit firms, ≤5 at insurers, ≤5 at AI-agent platforms, ≤3 at chains
- [ ] **First auditor commitment**: one audit firm agrees to publish a P-level certificate alongside their next narrative report
- [ ] **Advisory board**: 3–5 reviewers across audit / formal methods / DeFi risk / bridge security / AI-agent security

External recruitment for the last three items is the primary remaining work.

## After 30 days

| Quarter | Milestone |
|---|---|
| Q3 2026 | First production P3 certificate by a named protocol |
| Q4 2026 | First insurance underwriting cycle using the compliance level |
| Q1 2027 | First production P5 deployment with a runtime gate |
| Q2 2027 | First confirmed counterexample triggers framework refinement (or first 6-month period with zero submissions) |

## What can be done from a single seat

Everything in Week 1, Week 2, and most of Week 4 is implementable without external dependencies. The shipped artifact reflects this completeness.

What cannot be done from a single seat:
- External reviewer recruitment (Week 3)
- Audit firm commitment (Week 4)
- Advisory board (Week 4)
- Insurance pilot (Q4)

These are the natural next external moves.
