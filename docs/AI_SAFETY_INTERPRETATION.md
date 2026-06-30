# AI Safety Interpretation

PARALLAX-5 was developed in formal-methods vocabulary. Most of its potential users in the AI safety research community speak a different vocabulary. This document translates one to the other, with the intended audience being researchers at Anthropic, OpenAI, DeepMind, MIRI, ARC, Apollo Research, METR, the UK AISI, and academic AI safety groups.

The mapping is exact where it can be exact and approximate where it cannot. Concepts borrowed from other research traditions are credited to the originators. Concepts that are novel to PARALLAX-5 are flagged as such, with the reasoning for why a new concept was needed.

For the formal core, see `docs/THEOREM_INDEX.md`. For positioning against adjacent formal methods work, see `docs/RELATED_WORK.md`. The present document focuses on the AI safety angle.

---

## Tegmark, Omohundro et al. (2023): provably safe systems

The argument in arXiv:2309.01933 is that controllable AGI requires *external containment systems* with mathematical guarantees, rather than relying on alignment via training. The authors propose this as a research program; PARALLAX-5 is one concrete instance.

The mapping:

A *containment system* in Tegmark's vocabulary is, in our vocabulary, a step-secure gate. The gate is a function from agent proposals (transitions) to accept-or-reject. Its accept/reject decision is independent of the agent's internal policy.

A *mathematical guarantee* in their vocabulary is, in our vocabulary, a Lean 4 theorem with zero `sorry`. The relevant theorem is `generic_agent_gate_preserves_security` at line 572 of `parallax/formal/lean/Parallax5.lean`. The theorem states that any agent operating behind the gate cannot violate the obligations A1-A5 regardless of policy.

A *domain restriction* in their vocabulary is the scope condition. Our scope is value-bearing state transitions. This covers AI agents acting on smart contracts, custodied assets, governance votes, token transfers, and other artifacts where "value" is well-defined. It does not cover information-environment manipulation, deception of human principals, or any other slice of AI risk outside the value-bearing-transition layer.

The Tegmark research program needs many such containment systems for many such slices. We provide one. Other groups (Apollo, MIRI, academic teams) work on others.

The substrate's claim is narrower than the program's claim. We do not address AGI safety in general. We address the specific question of what mathematical bounds can be enforced on the value-bearing actions of an AI agent. The 67.2% basis-observable share of historical DeFi losses is empirical evidence that this slice is large enough to matter.

---

## Anthropic's Responsible Scaling Policy

The RSP defines capability thresholds (ASL-2, ASL-3, ASL-4) and corresponding evaluation requirements. PARALLAX-5 contributes to the *evaluation* problem for agents that reach ASL-3 capabilities involving value-bearing action.

At ASL-2, the substrate is overkill for most deployments. The certificate format is occasionally useful for documentation of deployments that touch financial state, but most ASL-2 agents do not.

At ASL-3 (autonomous task completion), the substrate becomes operationally relevant. An ASL-3 agent acting autonomously on value-bearing tasks can be deployed behind a PARALLAX-5 gate during evaluation phase. The gate's per-transition accept/reject decision produces a logged record of every action the agent attempted; the gate's reject distribution becomes an evaluation metric. This is more rigorous than running the agent without bounds and inspecting outputs.

At ASL-4 (autonomous research and similar high-capability operation), the substrate's scope is too narrow to address most of what the RSP would require for capability bounding. The gate remains relevant for any ASL-4 agent's value-bearing actions, but the bulk of an ASL-4 capability evaluation lives outside the substrate's reach.

For Anthropic specifically, integrating PARALLAX-5 obligations into the RSP evaluation criteria is open research; see `docs/OPEN_PROBLEMS.md` OP-13. The minimum viable engagement would be deploying a current Anthropic agent (Claude or similar) behind a substrate gate for a single benchmark task and reporting the gate's evaluation output.

---

## Constitutional AI

CAI shapes an agent's internal policy through constitutional principles applied during training. The substrate operates externally to the agent and enforces transition-level bounds regardless of training.

The two compose cleanly at different layers. CAI handles the modal case: most decisions an agent makes should be safe by virtue of the trained policy. The substrate handles the worst case: any value-bearing transition the policy attempts is bounded by the gate.

What CAI achieves and the substrate does not: informational behavior (what the agent discusses, what it refuses, how it engages), task-selection behavior (which tasks the agent agrees to undertake), tone and manner.

What the substrate achieves and CAI does not: mathematical guarantees on value-bearing transitions independent of the policy, audit trails of value-bearing decisions, behavior bounds that survive policy adaptation (whether learning-based, adversarial-prompt-driven, or training-distribution-shift).

A CAI agent deployed behind a substrate gate has both layers. For high-stakes deployments touching custodial transactions, governance, or token movements, the combination is more deployable than either approach alone.

---

## Mechanistic interpretability

Mechinterp work (Anthropic's circuits research, OpenAI Microscope, Apollo's deceptive-alignment investigations) aims to predict model behavior through inspection of internal representations.

The substrate operates at a different layer. It does not inspect the model. It evaluates the action proposed by the model against the obligations. The substrate is policy-blind: what the model's representations encode does not affect the gate's decision; what matters is whether the proposed transition satisfies A1-A5.

The two combine usefully. Mechinterp work characterizes likely behavior before deployment, including known failure modes. The substrate enforces mathematical bounds during deployment. Operational gate logs become evaluation data for further mechinterp research.

Mechinterp predicts; the substrate reacts. Neither replaces the other.

---

## Scalable oversight

Scalable oversight research (Bowman et al. 2022 on debate, Christiano on IDA, Sandbrink et al. 2023 on RRM) asks how human supervision can scale with AI capability. Common methods involve recursive human evaluation of model outputs.

The substrate offers a different kind of scaling for the value-bearing-transition slice: supervision can be mechanical. The gate's accept/reject decision is computed at sub-millisecond latency for billions of transactions per day. Human judgment is not required for each decision.

This is not an alternative to scalable oversight in general. It is a specific case where the supervision problem reduces to mechanical evaluation because the obligation predicates are decidable. The 33% of historical losses that the catalog classifies as basis-unobservable or ambiguous is the residual case where mechanical supervision is insufficient.

The substrate moves the scalable oversight problem rather than solving it. The 67% reduction is real; the 33% residual is where human judgment remains necessary.

---

## Dangerous capability evaluation

Apollo Research, METR, the UK AISI, and others measure dangerous capabilities by running models in controlled environments. A natural question: can a substrate gate serve as the bounded environment?

Yes. A model deployed behind a gate has the capability to attempt any value-bearing transition. It does not have the capability to execute any transition that violates the obligations. The capability evaluator measures attempts; the gate enforces bounds on executions.

The output of such an evaluation is sharper than running the model unbounded. The evaluator obtains a complete log of attempted actions (the model's capability surface) and a complete log of rejected actions (the capability surface bounded by the substrate). The difference between the two is the evaluated capability gain that would result from removing the substrate.

For evaluations specifically focused on value-bearing actions (financial fraud, theft, market manipulation, smart contract exploitation), the substrate gate is a particularly clean evaluation harness. For evaluations focused on other capabilities (information manipulation, autonomous research), the substrate adds no value.

---

## Deceptive alignment

Apollo Research's deceptive-alignment investigations and the ARC Theory program ask: can a sufficiently capable misaligned agent conceal its misalignment during training and execute on it after deployment?

The substrate is structurally robust to deceptive alignment, in the following specific sense. A deceptively-aligned agent behind the gate receives the same accept/reject decisions as a genuinely-aligned agent. Deceptive alignment provides no path to violating A1-A5; the gate's policy-blindness eliminates the relevant attack surface.

This is an upper bound that holds for arbitrarily capable agents, provided the gate's adequacy condition holds and the gate's basis function correctly captures the protocol's value invariants.

It does not address the off-gate attack surface: a deceptively-aligned agent might influence the gate's specification through social engineering against the protocol's governance, identify edge cases where the gate's adequacy condition fails through off-chain coordination, or wait for opportunities outside the gate's scope. These require complementary defenses at the social and governance layers.

The substrate eliminates one attack surface (capability-driven violation of value-bearing transitions) and leaves others (governance compromise, off-chain coordination, social engineering). It is one defense among many that any serious deployment should compose.

---

## Long-term safety frameworks

Older AI safety literature (Bostrom's *Superintelligence*, MIRI's agent foundations program) frames safety in terms of long-term existential concerns about transformative AI. The substrate operates at a different timescale and addresses a narrower problem.

The substrate is a near-term, narrow-scope safety system deployable today for AI agents touching value-bearing state. The claim is bounded: this is one instance of the Tegmark research program for one specific slice. The substrate does not address AGI takeover, long-term corrigibility, value loading, or any of the other concerns in the long-term safety canon.

This is the right scope for the substrate to occupy. Safety claims that exceed scope undermine the claims that hold. Researchers working on long-term safety problems should treat the substrate as an example of the kind of narrow-scope, mathematically-rigorous, near-term-deployable artifact that the field benefits from accumulating, rather than as a competitor for the long-term problem.

---

## Engagement with specific organizations

For Anthropic, the direct compositions are CAI-plus-gate as a defense-in-depth pattern, the gate as an RSP evaluation harness for ASL-3 capability-bounding involving value-bearing actions, and OP-13 in the open-problems list as a research project.

For MIRI and ARC, the substrate is too narrow for the primary research interests but the methodology of concretizing a safety primitive in Lean with explicit adequacy conditions may transfer. Critique on the formal-methods quality of the substrate is welcome and likely high-leverage for both sides.

For Apollo Research, the substrate is complementary to deceptive-alignment work. A gate paired with Apollo's evaluation methodology produces stronger overall safety bounds than either component alone. The specific composition is sketched in this document.

For METR, the UK AISI, and other dangerous-capability evaluators, the substrate provides bounded environments for evaluations involving value-bearing artifacts. The evaluation output is sharper than unbounded evaluation.

For academic AI safety groups (CHAI, FHI, Berkeley CSAIL, MIT CSAIL), the open problems in `docs/OPEN_PROBLEMS.md` items OP-3, OP-13, and OP-14 are explicit research questions that the substrate is positioned to support but cannot resolve internally.

---

## What the substrate is and is not

The substrate is a concrete, mechanized, falsifiable contribution to the AI safety problem space. It is deployable today and produces safety gains for AI agents acting on value-bearing state machines. It composes with Constitutional AI, the RSP, mechinterp work, and scalable oversight research without conflict.

The substrate is not a solution to alignment, a defense against existential AI risk, a replacement for any existing safety methodology, or a competitor to any research program. It addresses one specific slice. The slice is large enough to matter and small enough to be tractable today.

The right portfolio framing: the AI safety field benefits from accumulating more concrete, mechanized, narrow-scope artifacts of this kind, alongside the broader research programs that address larger questions.

---

## How to engage

Researchers interested in the formal core should start with `docs/THEOREM_INDEX.md` and then read `parallax/formal/lean/Parallax5.lean` for the central theorems. The paper at `paper/parallax-5.pdf` provides the complete development.

Researchers considering collaboration should review `docs/OPEN_PROBLEMS.md` and contact `research@aquaursa.ai` with proposed scope.

Organizations considering the substrate for operational use should review `docs/FOR_INTEGRATORS.md` for the three integration patterns. The runtime-gate pattern is the most relevant for AI safety deployments.

Anthropic and similar organizations interested in exploratory conversation about RSP integration, CAI composition, or AI safety alignment can reach AquaUrsa at `research@aquaursa.ai`. The substrate's open-source posture means no commercial relationship is required for evaluation, integration, or research use.
