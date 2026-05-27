# Theorem Index

A 95-theorem Lean development is difficult to navigate without an annotated index. This index identifies the load-bearing theorems (carrying the substrate's main claims), the supporting theorems (witnesses and lemmas), and the runtime instantiations (theorems lifting the abstract substrate to specific VMs).

Line numbers reference `parallax/formal/lean/Parallax5.lean` at v1.1.0.

## Theorem inventory

| Category | Count | Role |
|---|---|---|
| Axiom predicates | base definitions | A1 through A5 as predicates over state machines |
| Preservation under guarded transitions | 4 | Specific transition relations preserve specific axioms |
| Independence witnesses | 16 | Each axiom independent of the others (basis minimality witnesses) |
| Basis minimality theorem | 1 | A1, A2, A4, A5 mutually independent |
| Compositional preservation | 4 | Axioms preserved under product compositions |
| Sequence preservation | 1 | A1 preserved under arbitrary deposit sequences |
| Agent-session safety | 2 | Agent operating behind gate cannot violate axioms over a session |
| Generic agent gate | 1 | AI-Agent Containment Theorem at typeclass level |
| Multi-runtime instances | 2 | Solana, Move/Sui instances of the generic theorem |
| Conditional completeness | 1 | Every trust-base-respecting loss-inducing transition violates some axiom |
| Falsification criterion | 1 | Falsifiable predicate definition and closure inhabitation |
| Maximal-safe-gate | 1 | Step-secure gate is the maximally permissive accept/reject shield |
| Monitor soundness | 1 | Monitor soundness suffices for system safety |
| Adaptive session safety | 1 | Gate composes with adaptive (LLM-style) policies |
| Refinement / simulation | 1 | Cross-VM theorem transport via refinement |
| Off-chain indistinguishability | 1 | Irreducible scope boundary at the on-chain/off-chain interface |
| Patch-correctness | several | Patch-level theorems for specific exploit archetypes |
| EVMYulLean instance refinement | 19 abstract + 5 concrete | Substrate composition with EVMYulLean |

Eight load-bearing theorems are described in detail below. A reviewer with limited time should read these first.

## The load-bearing theorems

### Basis minimality (line 189)

```lean
theorem basis_minimal : -- four axioms are mutually independent
```

There exist states `witnessA1`, `witnessA2`, `witnessA4`, `witnessA5` such that each violates exactly one axiom while satisfying the other three. No axiom is implied by the conjunction of the others.

This theorem justifies the minimality of the five-obligation set. Without it, a reviewer can reasonably ask whether one of the axioms is redundant. The witnesses are constructive: the proof exhibits each independence by explicit example. The 16 supporting witness theorems at lines 98 through 184 prove that each witness violates exactly one axiom.

The theorem is the answer to "is the axiom set minimal?" A reviewer can verify by running the Lean kernel on the witnesses.

### Conditional completeness (line 925)

Under the security-interface adequacy condition (defined explicitly in the file), every trust-base-respecting transition that decreases the basis value must violate at least one axiom in {A1, A2, A4, A5}.

This is the substrate's central claim. In plain language: if the gate's interface is adequate, the gate catches every loss-inducing transition.

The adequacy condition requires that the gate's view of the world include all features the obligation predicates need to evaluate. If the adequacy condition fails for a particular deployment, the theorem does not bind for that deployment. The paper states this scope limit explicitly.

The 67.2% basis-observable share from the empirical catalog is the share of historical losses for which adequacy holds and the theorem applies. The residual 33% includes cases where the adequacy condition fails (information required to detect the violation is off-chain only) or is ambiguous.

### Generic agent gate (line 572)

```lean
theorem generic_agent_gate_preserves_security {S α : Type}
```

For any value-bearing state machine `S` and any agent policy `α`, the composition of the agent with a PARALLAX-5 step-secure gate cannot violate the obligations regardless of the agent's policy.

This is the AI-Agent Containment Theorem in its abstract form. The theorem is the concrete mechanized instance of Tegmark's "provably safe systems" thesis for the value-bearing-state slice.

The theorem is parameterized over the state type and the agent type. It specializes to concrete cases automatically: EVM state with an LLM agent (the agentic-DeFi case), banking ledger with an automated trading system (the institutional finance case), Solana account with an MEV bot (the cross-VM case), and so on.

The worked example at `demos/agent_gate/proof/Containment.lean` instantiates this theorem for an explicit adversarial agent against a specific vault contract.

### Maximal-safe-gate (line 1020)

Among all accept/reject shields that preserve the basis under {A1, A2, A4, A5}, the step-secure gate accepts the strict superset of transitions. No safer shield preserving the same axioms is more permissive.

The theorem distinguishes PARALLAX-5 from a "deny everything" gate that would also preserve all axioms but be operationally useless. It establishes that the gate is optimal in a specific sense: as permissive as possible while remaining sound.

For a reviewer asking "isn't the gate too restrictive?" the answer is no. The gate accepts the maximally large set of transitions a sound gate could accept.

### Monitor soundness (line 1065)

If the monitor's view of state and transitions is sound (in the technical sense defined in the file), the monitor's safety guarantees lift to the underlying system's safety.

This theorem allows PARALLAX-5 certificates to be issued by external monitors (audit firms, on-chain monitors) without requiring the substrate's authors to verify every deployment. The monitor's soundness is the precondition; the system's safety is the conclusion.

For audit firms (Trail of Bits, OpenZeppelin, ChainSecurity), this is the formal underpinning of "after a sound audit, we can issue a PARALLAX-5 certificate."

### Adaptive session safety (line 1093)

An agent policy that adapts based on observed transitions (an LLM-style agent that learns from execution) cannot violate axioms when operating behind the gate.

A static-policy theorem is insufficient for AI agents because real agents adapt. This theorem extends the containment claim to adaptive policies. The gate's safety property is independent of the policy, so no policy adaptation can break enforcement.

For a reviewer asking "what if the agent is smart and adapts to find a way around the gate?", the answer is that policy adaptation cannot break the obligation enforcement.

### Falsification criterion (line 959)

The substrate's main claim is falsifiable in a specific way. A counterexample is a (state, transition) pair satisfying all axioms but exhibiting a loss-inducing trust-base violation. The criterion is constructive: if a counterexample exists, it can be exhibited concretely.

This distinguishes PARALLAX-5 from unfalsifiable security claims. Anyone finding such a counterexample can publish it; AquaUrsa provides a verification procedure and explicit bounty in `paper/FALSIFICATION_CHALLENGE.md`.

For Popperian critique, this is the answer. The substrate is a falsifiable scientific claim.

### Off-chain indistinguishability (line 1150)

Two distinct trust-base-violating off-chain events that produce identical on-chain effects are formally indistinguishable to any on-chain gate. The gate cannot distinguish between them.

The theorem establishes the scope boundary of the substrate. The substrate does not detect off-chain attacks (social engineering, governance attacks via off-chain coordination, private-key compromise through OS-level exploits). It bounds the on-chain manifestation of such attacks. The scope limit is formally proved rather than asserted.

The 32.8% basis-unobservable plus ambiguous share of the empirical catalog reflects this limit. For a reviewer asking "what about off-chain attacks?", the answer is that there are losses mapping to identical on-chain states from distinct off-chain causes; the gate cannot tell them apart, and this is an inherent limit of any on-chain gate.

## Supporting theorem groups

The four preservation-under-guarded-transitions theorems at lines 63 through 90 prove that specific transition relations (`adminGuarded`, `oracleReadGuarded`) preserve specific axioms. These are building blocks for the more general preservation theorems below.

The four compositional preservation theorems at lines 383 through 410 prove that if state machine `A` preserves an axiom and state machine `B` preserves the same axiom, the product `A × B` also preserves it. Required for modular reasoning about composed protocols.

The sequence preservation theorem at line 435 proves that A1 is preserved under arbitrary-length sequences of deposit operations. The induction handles unbounded transaction histories.

The agent pre-action safety theorem at line 481 proves that an agent's pre-action proposal phase is safety-checked before commit. This is the building block for `agent_session_safe` (the per-session safety theorem) which composes to `generic_agent_gate_preserves_security`.

## Runtime instances

### EVM (production refinement)

The EVMYulLean instance is the production-grade refinement. The instance declaration lives at `parallax/formal/lean/Parallax5_EvmYulLean.lean`; the abstract refinement theorems are at `parallax/formal/lean/Parallax5.lean` lines 1744 onwards.

The instance covers 19 abstract proof terms parameterized over the basis function plus 5 concrete proof terms instantiated for the ERC-4626 vault basis. The total is 24 compiled proof terms over `EvmYul.EVM.State`.

External verification artifact: [doi:10.5281/zenodo.20386868](https://doi.org/10.5281/zenodo.20386868).

### Solana (typeclass level)

```lean
theorem solana_agent_safe ...  -- line 666
```

Solana account model instance of the generic theorem. Typeclass-level only; full Solana SVM semantic refinement is open work documented in `docs/OPEN_PROBLEMS.md` OP-6.

### Move (typeclass level)

```lean
theorem move_agent_safe ...  -- line 671
```

Move resource model instance. Typeclass-level only; production-grade Move semantic refinement is open work documented in `docs/OPEN_PROBLEMS.md` OP-5.

### Banking ledger (typeclass level)

The substrate's typeclass formulation accepts a banking-ledger instance, useful for compliance mapping under DORA and EU AI Act for financial institutions. A sample instance is in `parallax/standard/` for illustration. Jurisdiction-specific semantics are deferred.

## Navigation

The 95-theorem file is organized as follows.

Lines 1 through 50 cover imports and axiom definitions.

Lines 51 through 90 cover transition relations and preservation theorems.

Lines 98 through 186 contain the 16 independence witnesses, organized in four groups of four (one group per axiom).

Lines 187 through 203 prove the basis minimality theorem.

Lines 204 through 249 cover runtime sanity checks and safe-state proofs.

Lines 250 through 410 cover compositional and sequence preservation.

Lines 411 through 580 cover generic agent gate machinery, culminating in `generic_agent_gate_preserves_security` at line 572 (the AI-Agent Containment Theorem).

Lines 581 through 810 contain vault-specific refinements.

Lines 811 through 924 contain the transition-level model.

Lines 925 through 958 prove the conditional completeness theorem.

Lines 959 through 981 prove the falsification criterion.

Lines 982 through 1019 prove constructive closure inhabitation.

Lines 1020 through 1064 prove the maximal-safe-gate theorem.

Lines 1065 through 1092 prove monitor soundness.

Lines 1093 through 1113 prove adaptive session safety.

Lines 1114 through 1149 cover refinement and simulation.

Lines 1150 through 1179 prove off-chain indistinguishability.

Lines 1180 through 1214 cover patch-correctness theorems.

Lines 1215 through 1530 contain the theorem-inventory namespace (introspection support).

Lines 1744 onwards cover the EVMYulLean refinement at typeclass level.

Comments throughout the file labeled "reviewer #N" reflect the structure of the paper's peer-review process. Reading them as "what would a careful reviewer ask?" is a useful navigational aid.

## Theorem count verification

```bash
$ grep -cE "^theorem |^lemma " parallax/formal/lean/Parallax5.lean
95

$ find . -name "*.lean" -exec grep -hE "(^|\s)sorry(\s|$)" {} \; | grep -vE "^\s*(--|/\*)" | wc -l
0
```

The 95 in Parallax5.lean is what the paper cites in its main claim. The 135 figure in the CHANGELOG aggregates the core with the substrate sub-modules (`lean/Parallax5/Compositional.lean`, `Walkaway.lean`, `Registry.lean`) and the three demo proofs (Vault, Bridge, Agent-gate). The 177 figure in `CANONICAL_FACTS.md` adds the exploratory notebook theorems. The zero `sorry` count holds across all 177. The three counts represent different scopes; `CANONICAL_FACTS.md` documents the distinction.

## For Lean experts scrutinizing specific proofs

The proofs are largely tactic-based with explicit term constructions where the tactic mode would be unclear. The basis-minimality witnesses use `by decide` for boolean predicate evaluations. The conditional completeness theorem uses case analysis on the failed axiom (a finite set, so structural induction works). The maximal-safe-gate theorem uses a constructive demonstration: for any proposed shield more permissive than the step-secure gate, the proof exhibits a transition the candidate would accept that violates an axiom.

Three specific proofs invite particular scrutiny.

First, `adaptive_iteration_preserves_security`: does the proof generalize to all reasonable definitions of "adaptive"? The theorem statement uses a specific adaptive model; a critic could propose a different model and ask whether the proof still goes through.

Second, the off-chain indistinguishability theorem: is the indistinguishability argument's quantifier ordering correct? The theorem statement involves nested quantifiers, and the order matters for the strength of the claim.

Third, the EVMYulLean refinement: does the parametricity argument actually transfer abstract theorems to the concrete VM in the way claimed? A critic familiar with Lean's parametricity could check that the typeclass instance does not introduce hidden assumptions that weaken the transferred theorems.

Critique that finds a substantive issue earns co-authorship on v1.1 or higher and an entry in the security hall of fame.
