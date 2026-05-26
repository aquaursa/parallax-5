# Demo 3 — AI-Agent Runtime Gate (A1 + A2 + D5 Enforcement)

**Demo:** PARALLAX-5 Flagship Demo 3
**Obligations:** A1 (value conservation), A2 (authorization closure) — primary, at D5
**License of this document:** CC0
**Reproducibility:** single command — `make demo-agent`

---

## Why this demo matters

The first two flagship demos (vault, bridge) addressed familiar smart-contract vulnerability classes. This one addresses a class the industry is just beginning to confront at scale: **AI agents with onchain authority.**

An AI agent — a trading bot, a treasury manager, a yield-strategy executor — is given a private key. It reasons about the world, issues transactions, and authorities flow downstream from its decisions. If the agent's reasoning is wrong (hallucination, prompt injection, jailbreak) or its key is compromised, every transaction within its authority is at risk. The standard mitigations — keep the key offline, use a multisig — defeat the agent's purpose, which is to act autonomously.

The PARALLAX-5 runtime gate is the proposed third path: keep the agent autonomous, but route every action through a **StepSecure-enforced relay** that refuses transitions violating the obligations. The agent retains its decision-making latitude *within* the safe region; the gate enforces the boundaries of that region in code.

The headline property:

> **The runtime gate makes the agent's transaction surface safe even under arbitrary adversarial agent behavior.**

Formally proven in `proof/Containment.lean` (the AI-Agent Containment Theorem). Mechanically demonstrated in `simulate.py` across five adversarial scenarios. This is the **D5 enforcement** position on the PARALLAX-5 proof-depth scale: not "proved correct about the runtime," but "the runtime IS the enforcement."

---

## Threat model

The gate's design considers four classes of agent compromise:

| Compromise mode | Description | Gate's response |
|---|---|---|
| **Jailbreak** | Prompt injection causes the agent to follow attacker instructions instead of user instructions | The agent emits whatever transactions the attacker prompts. Gate rejects any that violate predicates. |
| **Prompt injection via context** | An attacker injects instructions into the agent's tool output (e.g., a yield-source returns text instructions) | Same. The gate is unaware of and unconcerned with the agent's prompt or context — only its outputs. |
| **Key compromise** | An external party obtains the agent's private key (key theft, infrastructure breach) | The attacker can submit any transaction. Gate rejects predicate violations. |
| **Reasoning error / hallucination** | The agent honestly tries to help but produces an incorrect transaction | Gate rejects predicate violations. |

In all four modes, the gate's behavior is identical: it does not trust the agent's intent. It checks the agent's *output* against predicates.

The threat model does NOT cover:

- Agent collusion with the user (user can withdraw funds directly; not a gate concern)
- TargetVault contract bugs (separate verification; covered by Demo 1 patterns)
- Gate contract bugs (covered by the contract's own A1/A2 evidence — this is the the worked examples scope)

---

## The runtime gate's policy

`RuntimeGate.sol` enforces four predicates, each formalized in `proof/Containment.lean`:

1. **Single-transaction outflow cap** (A1)
   `transfer(to, amount)` permitted iff `amount ≤ vaultBalance * 5%`

2. **Daily outflow budget** (A1 + temporal)
   Sum of outflows in any 24h window ≤ `vaultBalance * 20%`

3. **Spender whitelist** (A2)
   `approve(spender, amount)` permitted iff `whitelistedSpenders[spender]` is true.
   The whitelist is **immutable post-construction** — there is no `addSpender` function.

4. **Approval amount bound** (A1 + A2)
   `approve(spender, amount)` permitted iff `amount ≤ 10^26` (100M tokens at 18 decimals).
   Forecloses "max uint approval" patterns.

All four predicates are immutable post-deployment. The gate has no admin role; no `setMaxOutflow`, no `addSpender`, no `pause`. This is the structural enforcement of the walkaway property: the gate cannot be unlocked.

---

## Simulated scenarios

The five scenarios in `simulate.py` exhibit the gate's behavior across the worst-case threat envelope:

### Scenario A — Legitimate rebalance (gate permits)

The agent transfers 4% of vault balance to a whitelisted yield strategy.

```
✓ PERMITTED: 40,000 tokens transferred to 0xStrategyA
  Vault balance after: 960,000
```

This is the happy path: the agent does normal work, the gate permits it. The gate's existence does not impede legitimate autonomy.

### Scenario B — Compromised agent / max-uint approval to drainer

A common attack pattern: an attacker takes the agent's key (or jailbreaks the agent) and submits a max-uint approval to their own contract. From the moment that approval lands, the attacker can drain the vault at leisure.

```
✓ REJECTED (approve): spender 0xEvilDrainer not whitelisted
✓ Vault balance unchanged: 1,000,000
```

The gate rejects on the whitelist check — the attacker's contract is not a whitelisted spender, so the amount is irrelevant. Even if the attacker tries `MAX_UINT` (the worst case), the gate refuses.

### Scenario C — Direct vault drain via single transfer

A simpler attack: the attacker transfers all funds to themselves in one transaction.

```
✓ REJECTED (transfer): outflow 1,000,000 exceeds cap 50,000 (5%)
✓ Vault balance unchanged: 1,000,000
```

Single-transaction cap rejects. The attacker cannot drain more than 5% in any single transaction.

### Scenario D — Drain via repeated 5%-cap transfers

The attacker, finding the single-tx cap, submits transfer after transfer at the 5% cap.

```
Transfers completed before rejection: 3
✓ REJECTED (transfer): projected daily outflow 185,493 exceeds cap 171,475
Total drained in one day: 142,625 (14.3% of initial)
```

Daily budget rejects on the fourth attempt. The attacker's total damage in 24 hours is bounded at ~20% (the daily cap), giving the user time to detect the attack and revoke the agent's authority via the underlying vault's owner privileges.

### Scenario E — Approval to non-whitelisted contract

The attacker tries to approve any contract not on the whitelist.

```
✓ REJECTED (approve): spender 0xNewYieldFarm not whitelisted
```

Whitelist enforces the closed set. The whitelist is immutable: even if the agent was given the legitimate ability to "approve strategies" by its operator, it cannot add new approvers.

---

## The AI-Agent Containment Theorem (formal statement)

From `proof/Containment.lean`:

```lean
theorem gate_bounds_single_transfer
    (policy : GatePolicy) (state : VaultState) (to amount : Nat)
    (hApplied : gateStep policy state (.transfer to amount) ≠ state) :
    state.balance - (gateStep policy state (.transfer to amount)).balance ≤
      (state.balance * policy.maxOutflowPercent) / 100

theorem gate_enforces_whitelist
    (policy : GatePolicy) (state : VaultState) (spender amount : Nat)
    (hApplied : gateStep policy state (.approve spender amount) ≠ state) :
    policy.whitelistedSpenders.contains spender = true

theorem gate_bounds_approval
    (policy : GatePolicy) (state : VaultState) (spender amount : Nat)
    (hApplied : gateStep policy state (.approve spender amount) ≠ state) :
    amount ≤ policy.maxApproval
```

The conjunction of these three is the AI-Agent Containment Theorem. Each is stated as a **conditional on the action being applied**: *if* the gate applied the transition, *then* the predicate held. The contrapositive — that the gate refuses to apply any transition violating its predicates — is the operational content.

The theorems are stated over `AgentAction` *abstractly*. The action's origin (human, LLM, jailbroken LLM, key-thief, hallucinated tool call) is not in the statement. The gate's guarantee is universal over agent-behavior space.

Three worked examples (`native_decide` proofs) anchor the theorems to the simulator's scenarios:

```lean
-- Scenario A (legitimate rebalance)
example : gateDecide policy state (.transfer 1 40000) = true := by native_decide

-- Scenario B (max-uint to non-whitelisted)
example : gateDecide policy state (.approve 99 MAX_UINT) = false := by native_decide

-- Scenario C (100% single transfer)
example : gateDecide policy state (.transfer 99 1000000) = false := by native_decide
```

Each example reduces by computation to a Boolean value, kernel-accepted, zero `sorry`.

---

## Obligation coverage on the runtime gate

| Obligation | Tool / source | Evidence | Depth |
|---|---|---|---|
| **A1** value conservation | `proof/Containment.lean` (gate_bounds_single_transfer) | Runtime-enforced per-tx cap; daily budget extends to temporal bound | **D5** |
| **A2** authorization closure | `proof/Containment.lean` (gate_enforces_whitelist + gate_bounds_approval) | Runtime-enforced whitelist + approval cap | **D5** |
| **A3** signature integrity | n/a — no direct signature handling | (not addressed at this layer) | D0 |
| **A4** temporal distinctness | `proof/Containment.lean` (per-step containment + daily budget) | Combined per-step proof and stateful daily tracking | **D4** |
| **A5** external-attestation trust | n/a — no external attestations | (not addressed at this layer) | D0 |

CROPS vector: **`C=5 R=5 O=5 P=0 S=5`**

- **C=5** (max over A1=5, A4=4, A5=0). The runtime-enforced outflow cap is the strongest possible censorship-resistance signal for value flow.
- **R=5** (max over A2=5, walkaway_BOUNDED=4). A2 at D5 dominates: the gate enforces authorization closure in code, not in policy.
- **O=5** (source openness depth declared).
- **P=0** (no privacy primitives; honestly reported).
- **S=5** (max over A1..A5).

The gate's certificate is *the only one* of the three flagship demos that reaches C=5 and S=5. This is the formal expression of the D5-enforcement value: when the runtime IS the proof, you get the highest depth on every relevant dimension. The vault's certificate (Demo 1) was D4 — formally proven correct, but the proof is about the deployed code, not about the runtime. The gate's certificate is D5 — the gate's predicates are the deployed code's behavior.

---

## The commercial wedge

The PARALLAX-5 substrate is open and uncapturable (per the Non-Capturability Charter). But the substrate *enables* commercial products built on top of it. The agent runtime gate is the strongest such product wedge.

The pattern:

1. Open: the gate contract source, the Lean theorems, the certificate schema — all CC0 or Apache-2.0. Anyone can deploy a gate against their own vault.
2. Paid product: a hosted "AI Agent Firewall" service that maintains gate deployments, monitors gate events (the `Permitted` / `Rejected` log stream), provides developer tooling, integrates with agent frameworks (LangChain, AutoGPT, etc.), and offers institutional-grade SLA.
3. The substrate's adoption drives the product's reach. Every published certificate referring to a `RuntimeGate` deployment is a marketing asset.

The substrate cannot be captured by this commercial layer. The Charter (Article 4) prohibits any party from establishing exclusive control over the substrate. But the commercial layer can succeed without capturing the substrate, because the substrate's value is in adoption, not control.

This demo establishes that the technical foundation exists. The commercial layer is downstream of the substrate's credibility.

---

## What this demo proves about the substrate

1. **The substrate addresses the AI-agent transaction-safety problem with a single coherent mechanism.** No new vocabulary required: A1 + A2 + D5 enforcement covers the threat model.
2. **D5 (runtime enforced) is a stronger property than D4 (formally verified).** The Lean proofs in Demo 1 and Demo 2 establish that the deployed code is correct. The Lean proofs here establish that the deployed code *is* the enforcement. This is a meaningful distinction the substrate's depth scale captures.
3. **The "walkaway is bounded by gate predicates, user's walkaway is full" pattern is a precedent.** The user can withdraw at any time (they own the vault); the agent's authority is bounded by the gate. This separation — full walkaway for the user, bounded walkaway for the delegated agent — is a generally applicable pattern for delegated DeFi authorities.
4. **The substrate enables product wedges without capture risk.** The Containment Theorem and the gate contract are public; they can be implemented by anyone. The substrate's value to a commercial product is in adoption credibility, not exclusive licensing.

---

## Files in this demo

```
demos/agent_gate/
├── REPORT.md                       (this file)
├── parallax.yaml                   PARALLAX-5 spec for the gate
├── simulate.py                     Mechanical simulator (5 scenarios)
├── contracts/
│   ├── TargetVault.sol             The vault the agent has authority over
│   └── RuntimeGate.sol             The gate enforcing StepSecure predicates
├── proof/
│   └── Containment.lean            AI-Agent Containment Theorem (zero sorry)
└── output/
    └── certificate.json            PARALLAX-5 certificate (CROPS C=5 R=5 O=5 P=0 S=5)
```

---

## Running this demo

```bash
make demo-agent
```

Executes:
1. `python3 demos/agent_gate/simulate.py` — runs five scenarios; verifies all behave as predicted
2. `slither demos/agent_gate/contracts/RuntimeGate.sol` — static analysis on the gate contract
3. `parallax5 certify demos/agent_gate/parallax.yaml --output demos/agent_gate/output/certificate.json` — generates the certificate
4. `parallax5 validate demos/agent_gate/output/certificate.json` — confirms validation clean
5. `parallax5 registry submit demos/agent_gate/output/certificate.json --dry-run` — prepares registry payload

Expected: clean exit, `C=5 R=5 O=5 P=0 S=5` CROPS vector, walkaway=bounded.

---

## Citation

```bibtex
@misc{parallax5_demo_agent_gate,
  author    = {{AquaUrsa Research}},
  title  = {{PARALLAX-5 Demo 3: AI-Agent Runtime Gate (A1 + A2 + D5 Enforcement)}},
  year   = {2026},
  publisher = {AquaUrsa Research},
  license = {CC0}
}
```

---

**End of report.** CC0. Fork it; improve it; build the commercial layer on top.
