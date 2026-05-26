# PARALLAX-5 Vision


## The one-sentence vision

PARALLAX-5 is the **CVE + SOC 2 + formal-proof certificate** layer for value-bearing smart-contract transitions and AI-agent execution.

## Component analogies

| Existing | Function | PARALLAX-5 analog |
|---|---|---|
| **CVE** | Names every disclosed vulnerability uniquely | Names every obligation violation uniquely ($\sigma(t) = \{A_1, A_4\}$ etc.) |
| **SOC 2** | Auditable compliance posture for SaaS | Auditable compliance posture for on-chain protocols (P0–P5) |
| **Formal-proof certificate** | Machine-checkable correctness evidence | Per-obligation proof artifacts (Lean / Certora / halmos / Z3) |
| **Common Criteria EAL** | Levels of evaluation assurance | P0–P5 levels of obligation coverage |
| **Carfax** | Per-vehicle history report for buyers | Per-protocol trust-surface for users / insurers |
| **DNS** | Universal name resolution | Universal obligation-name resolution |
| **SSL/TLS handshake** | Pre-execution trust establishment | Pre-execution basis check (step-secure gate) |

## The eight components of a full standard

| Component | Status | Reference |
|---|---|---|
| 1. Naming system for obligation violations | ✓ | $A_1 \ldots A_5$ + $\sigma(t)$ notation |
| 2. Certificate format | ✓ | JSON Schema (Draft 2020-12) |
| 3. Registry | partial | `parallax5 serve`; future `parallax5.io` |
| 4. Validation CLI | ✓ | `parallax5 validate` |
| 5. Reporting format | ✓ | Trust-surface HTML, SVG badges |
| 6. Upgrade/revalidation process | ✓ | [GOVERNANCE.md](GOVERNANCE.md) |
| 7. Runtime enforcement option | ✓ | P5 step-secure gate (Lean + Solidity SDK in progress) |
| 8. Public incident catalog | ✓ | 53-incident catalog with bootstrap CIs |

The remaining gap is **adoption** — a real auditor publishing a real certificate, a real insurer pricing against a real one, a real protocol deploying a real runtime gate.

## What success looks like

In 24 months:

- ≥3 audit firms have issued ≥10 PARALLAX-5 certificates each.
- ≥1 DeFi insurer prices premiums against the compliance level.
- ≥1 AI-agent platform enforces a step-secure gate on production transactions.
- ≥1 chain hosts a public certificate registry.
- The standard has progressed through one major revision following community input and confirmed challenges (or zero confirmed challenges).
- The catalog has grown to ≥100 incidents with inter-rater agreement ≥0.85.

## Why this is bigger than a paper

A paper proves the substrate is sound. A standard makes the substrate usable. A registry makes the standard valuable. A runtime gate makes the value enforceable. PARALLAX-5 is designed as all four — not just the first.

The end-state is not "PARALLAX-5 is well-cited" but "every consequential value-bearing transaction in DeFi is checked against the basis before it executes, and every protocol's compliance posture is machine-readable."
