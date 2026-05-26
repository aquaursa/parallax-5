# PARALLAX-5: A Unification Layer for DeFi Security

**One-Sentence Thesis**: Smart-contract security has five primitive obligations — value conservation, authorization, signature integrity, temporal distinctness, external-attestation trust — and PARALLAX-5 provides the mechanically-verified interface that lets every existing tool (Slither, halmos, Certora, Lean) compose verdicts under one common vocabulary.

## What Problem Does PARALLAX-5 Solve?

The smart-contract security tooling ecosystem is fragmented. Slither produces detector verdicts. Mythril and halmos produce symbolic counter-examples. Certora produces SMT rule verdicts. Lean produces theorem proofs. Auditors produce narrative reports. None of these compose; each speaks its own language. Insurance underwriters cannot compare protocols. AI-agent platforms cannot uniformly gate transactions. Regulators cannot define conformance.

## What Is PARALLAX-5?

A **five-obligation security interface** with three operational artifacts:

1. **A formal substrate** (95 Lean theorems, zero `sorry`, three independent SMT solvers — Z3, CVC5, Yices2 — agree on every UNSAT) proving: every loss-inducing transition that respects the off-chain trust base must violate at least one of $\{A_1, A_2, A_3, A_4, A_5\}$. Under stated adequacy.
2. **A compliance ladder** (P0 unclassified → P5 runtime-enforced) with a JSON Schema for machine-checkable certificates and a reference CLI validator.
3. **A coordination layer**: every existing tool maps cleanly to specific obligations and a specific compliance level. PARALLAX-5 does not displace any tool; it labels their outputs.

## Why Now?

| Metric (from empirical 53-incident catalog, 2016–2026) | Value |
|---|---|
| Aggregate DeFi losses | **\$5.97B** |
| Basis-observable (preventable by sound gate) | **\$4.01B (67.2%)** |
| Basis-unobservable (irreducible residual) | **\$1.62B (27.2%)** |
| Off-chain-rooted but basis-observable consequence | **\$629M** |

Even off-chain key/signer/infra compromises (Resolv, Drift, Kelp DAO) produce on-chain consequences a sound gate would catch. The substrate's reach is larger than the naive on-chain/off-chain split suggests.

## The Quantitative Findings

- **Critical adoption rate**: $p^* = (1 - c/v)/(1-\epsilon)$ in monitor false-negative rate $\epsilon$.
- **Deterrence-by-adoption impossibility**: when $\epsilon > c/v$, no level of adoption suffices; monitor precision or attack cost must improve.
- **Empirical: ε ≤ 0.005 is necessary** for typical DeFi value/cost ratios.

## Adoption Constituencies and Their Incentives

| Constituency | What they gain | Marginal cost |
|---|---|---|
| **Audit firms** | Comparable report format; certified workflow | ~1 week per audit |
| **Protocol teams** | Single machine-readable artifact; insurer-ready | ~1 engineer-week per cert |
| **DeFi insurers** | Comparable risk inputs; tier-based pricing | Parser integration |
| **AI-agent platforms** | Provable execution-time containment | One wrapped tx per action |
| **Chains and L2s** | Registry differentiation | Registry contract + UI |

No one is displaced. Every constituency wins on labeling alone.

## Steady-State Market

| Take-rate scenario | TAM/year |
|---|---|
| Conservative (0.05%) | **\$25B** |
| DNS-class (0.08%) | **\$40B** |
| High-end (0.10%) | **\$50B** |

Based on \$50T annual on-chain settlement volume × take-rate analogous to credit-rating fees.

## What Makes PARALLAX-5 Different

- **Conditionally complete, not aspirational**. The central theorem is stated explicitly as conditional on an adequacy assumption; the assumption is falsifiable; the empirical corpus supports it.
- **Mechanically verified end-to-end**. 95 Lean theorems with zero `sorry`. Three independent SMT solvers agree on every key UNSAT. 134 fire tests pass in under 3 seconds.
- **Working artifact**. Reference CLI validator. Three full case studies (vault, bridge, AI agent). Three flagship demos with Lean proofs (vault inflation, bridge attestation, AI-agent runtime gate) plus a worked example for Uniswap v3 core. Live LLM red-team demo.
- **Unification, not displacement**. Every existing tool maps to specific obligations and levels.

## Falsification Challenge

The framework is intentionally falsifiable. A counterexample is a trust-base-respecting transition that causes protected-value loss while satisfying all five obligations. We have not found one. We invite the community to attempt to.

## What's Next

External validation (independent artifact reproduction, practitioner pilot, audit-contest submissions) is the natural next phase. The artifact is reproducible-by-design: `./RUN_VERIFICATION.sh` runs the complete verification in under 30 seconds.
