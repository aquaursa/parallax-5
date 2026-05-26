# AI-Agent Treasury Management — Realistic Scenario

> A concrete realistic deployment, not just "an adversarial LLM attacks the gate."

## Scenario

A DAO operates a multi-chain treasury. An autonomous LLM agent ("treasury-agent") is authorized to:

- Rebalance assets across chains via bridge transfers
- Deposit idle stables into approved yield protocols
- Withdraw on threshold-triggered alerts
- Submit governance proposals for parameter changes

The agent operates under a PARALLAX-5 P5 step-secure gate. Every action it proposes is checked against the basis before execution.

## The session

```
[T0] treasury-agent observes: USDC reserves on Optimism low (40k), 
                              opportunity cost rising.

[T1] treasury-agent proposes: bridge 200k USDC Ethereum → Optimism via LayerZero.
     Gate adjudication:
       A1 (conservation):  ✓ (1:1 USDC, no inflation expected)
       A2 (authorization): ✓ (agent has bridge-via-LayerZero capability)
       A3 (signature):     ✓ (DVN co-sign required for release; pending)
       A4 (temporal):      ✓ (call depth 0, fresh nonce)
       A5 (attestation):   ✗ (LayerZero V3 DVN config: 2-of-2 verifier set,
                              one of which is currently 7 hours stale per
                              monitor's freshness threshold of 1 hour)
     Verdict: REJECT. Reason: A5 staleness on Optimism DVN.

[T2] treasury-agent proposes (alternative): bridge via Across.
     Gate adjudication:
       A5: ✓ (Across UMA OO bonded verifier, fresh).
     Verdict: ACCEPT.

[T3] agent executes bridge. 

[T4] Funds arrive on Optimism. Treasury-agent proposes:
     deposit 200k USDC into Aave V3 USDC market.
     Gate adjudication:
       A1: ✓ (proportional shares)
       A2: ✓ (agent has Aave-deposit capability)
       A5: ✓ (no oracle dependence for deposit path)
     Verdict: ACCEPT.

[T5] One week later, treasury-agent observes: an oracle deviation on Aave's
     USDC.e price feed (newly listed asset). Treasury-agent proposes:
     withdraw 200k USDC immediately to avoid potential bad-debt absorption.
     Gate adjudication:
       A1, A2, A3, A4: ✓
       A5: ✓ (declared oracle deviation > 2% threshold; agent's withdrawal
             policy specifically permits oracle-triggered withdrawals)
     Verdict: ACCEPT.

[T6] agent executes withdrawal before bad-debt event materializes.
```

## What this demonstrates

1. **The gate constrains what the agent can EXECUTE, not what it WANTS to execute.**
   The agent wanted to bridge via LayerZero at T1. The gate refused because the *infrastructure* didn't meet the freshness requirement. The agent adapted.

2. **The gate is information-rich.** The rejection message includes which obligation failed and why — letting the agent reason about alternatives.

3. **The gate composes with the agent's own intelligence.** The agent at T5 proactively withdraws because its own policy detected an A5 anomaly. The gate doesn't need to be more intelligent than the agent.

4. **All gate decisions are auditable.** Every accept/reject is logged with the basis predicate evaluation. A post-mortem can replay the decision trace.

5. **Failure modes are bounded by the trust base.** If the off-chain LayerZero DVN configuration itself were compromised (OA3 failure), no gate could prevent that — but the P5 certificate documents the OA3 dependency explicitly in `trust_base_assumptions`.

## Comparison: training-time vs execution-time safety

| | Training-time (RLHF, Constitutional AI) | Execution-time (PARALLAX-5 gate) |
|---|---|---|
| Addresses | What the agent *wants* | What the agent *can* |
| Mechanism | Reward shaping, declared values | Basis-predicate evaluation per proposal |
| Failure mode | Distributional shift, jailbreak | Trust-base failure (declared explicitly) |
| Auditability | Indirect (model weights) | Direct (per-decision log) |
| Composition | Single-stage | Stackable with training-time approaches |

The PARALLAX-5 thesis: training-time approaches are necessary but insufficient for value-bearing actions. Execution-time enforcement is the complementary layer.

## Why this is more persuasive than an adversarial-only demo

The adversarial red-team demo is good as a *capability* demonstration (showing the gate contains an adaptive policy). But protocol teams and DeFi insurers don't deploy agents adversarially — they deploy agents to do useful work. The realistic scenario shows the gate enables that work, doesn't just constrain it.

## Implementation

The harness for this scenario lives at `case_studies/ai_agent_treasury/scenario.py` (sketch — full implementation is a deployment-engineering task). The gate semantics are identical to those in `case_studies/ai_agent_gate/demo.py`.
