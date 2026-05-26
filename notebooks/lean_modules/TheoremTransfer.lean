/-
Parallax5Evm.TheoremTransfer

Witness module establishing that the 19 abstract refinement theorems
declared in Parallax5Evm.Refinement instantiate over Nethermind's
EvmYul.EVM.State type. The file contains 24 theorem declarations:
  - 19 direct applications of the abstract theorems (ev_T1 through ev_T19)
  - 5 theorems on concrete default-constructed EVM.State values
    (concrete_C1 through concrete_C5)

Each declaration produces a proof term that exists in the compiled
.olean file only if the Lean 4 type checker accepted both the
abstract refinement theorem and its specialization to EvmYul.EVM.State
under the EvmLikeMachine instance registered in Parallax5Evm.Instance.
-/

import Parallax5Evm.Refinement
import Parallax5Evm.Instance

open EvmYul EvmYul.EVM

namespace Parallax5Evm.TheoremTransfer

-- ────────────────────────────────────────────────────────────────
-- Concrete gate configurations over EVM.State
-- ────────────────────────────────────────────────────────────────

/-- A gate that authorizes nothing and enables every obligation. Used
to demonstrate rejection theorems. -/
def strictGate : Parallax.AbstractGate EvmYul.EVM.State where
  authorized := fun _ => false
  enabled_A1 := true
  enabled_A2 := true
  enabled_A4 := true
  enabled_A5 := true
  oracle := (default : EvmYul.AccountAddress)
  max_age := 3600

/-- A gate that authorizes everyone and disables every obligation.
Used to demonstrate acceptance theorems. -/
def permissiveGate : Parallax.AbstractGate EvmYul.EVM.State where
  authorized := fun _ => true
  enabled_A1 := false
  enabled_A2 := false
  enabled_A4 := false
  enabled_A5 := false
  oracle := (default : EvmYul.AccountAddress)
  max_age := 0

/-- A gate with A1 disabled but other obligations enabled. Used to
demonstrate monotonicity (disabling makes it more permissive). -/
def relaxedGateA1Off : Parallax.AbstractGate EvmYul.EVM.State where
  authorized := fun _ => false
  enabled_A1 := false  -- disabled vs strictGate
  enabled_A2 := true
  enabled_A4 := true
  enabled_A5 := true
  oracle := (default : EvmYul.AccountAddress)
  max_age := 3600

-- ────────────────────────────────────────────────────────────────
-- The 8 single-step abstract theorems APPLIED to EvmYul.EVM.State
-- ────────────────────────────────────────────────────────────────

/-- T1 applied: any EVM state under strictGate is rejected because
strictGate authorizes no one. -/
theorem ev_T1_unauthorized_rejected (s : EvmYul.EVM.State) :
    strictGate.decide s = false :=
  Parallax.abstract_gate_rejects_unauthorized strictGate s rfl rfl

/-- T2 applied: any EVM state with non-zero call depth is rejected
by a gate with A4 enabled. -/
theorem ev_T2_reentrancy_rejected
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s : EvmYul.EVM.State)
    (h_a4 : g.enabled_A4 = true)
    (h_depth : Parallax.EvmLikeMachine.callDepth s ≠ 0) :
    g.decide s = false :=
  Parallax.abstract_gate_rejects_reentrancy g s h_a4 h_depth

/-- T3 applied: stale oracle attestation rejected when A5 enabled. -/
theorem ev_T3_stale_oracle_rejected
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s : EvmYul.EVM.State)
    (h_a5 : g.enabled_A5 = true)
    (h_stale : Parallax.EvmLikeMachine.attestationFresh s g.oracle g.max_age = false) :
    g.decide s = false :=
  Parallax.abstract_gate_rejects_stale_oracle g s h_a5 h_stale

/-- T4 applied: any EVM transition that inflates total supply is
rejected by A1-enabled gate. -/
theorem ev_T4_inflation_rejected
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s s' : EvmYul.EVM.State)
    (h_a1 : g.enabled_A1 = true)
    (h_step : Parallax.EvmLikeMachine.step s = some s')
    (h_inflated : Parallax.EvmLikeMachine.totalSupply s'
                  > Parallax.EvmLikeMachine.totalSupply s) :
    g.decide s = false :=
  Parallax.abstract_gate_demands_conservation g s s' h_a1 h_step h_inflated

/-- T5 applied: fully-disabled gate accepts any EVM state. -/
theorem ev_T5_disabled_accepts (s : EvmYul.EVM.State) :
    permissiveGate.decide s = true :=
  Parallax.abstract_gate_disabled_accepts permissiveGate s rfl rfl rfl rfl

/-- T6 applied: disabling A4 admits reentrancy on EVM states. -/
theorem ev_T6_disable_A4_admits
    (s : EvmYul.EVM.State)
    (h_depth : Parallax.EvmLikeMachine.callDepth s ≠ 0) :
    permissiveGate.decide s = true :=
  Parallax.abstract_gate_disable_A4_admits_reentrancy
    permissiveGate s rfl rfl rfl rfl h_depth

/-- T7 applied: the EvmLikeMachine typeclass is non-empty. -/
theorem ev_T7_typeclass_inhabited :
    ∃ (S : Type), Nonempty (Parallax.EvmLikeMachine S) :=
  Parallax.evm_like_machine_inhabited

-- ────────────────────────────────────────────────────────────────
-- The 7 multi-step / trace-safety theorems applied
-- ────────────────────────────────────────────────────────────────

/-- T8 applied: zero-length trace = single-state check. -/
theorem ev_T8_trace_zero
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s : EvmYul.EVM.State) :
    Parallax.TraceSafe g s 0 = g.decide s :=
  Parallax.trace_safe_zero g s

/-- T9 applied: trace-safety on EvmYul.EVM.State is compositional. If a
trace of length n+1 is safe and the head state transitions to some successor,
then both (i) the gate accepts the head state and (ii) the tail trace of
length n is safe. This is the compositional decomposition of trace safety. -/
theorem ev_T9_trace_compositional
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s s' : EvmYul.EVM.State) (n : Nat)
    (h_safe : Parallax.TraceSafe g s (n+1) = true)
    (h_step : Parallax.EvmLikeMachine.step s = some s') :
    g.decide s = true ∧ Parallax.TraceSafe g s' n = true :=
  ⟨Parallax.trace_safe_implies_head g s n h_safe,
   Parallax.trace_safe_implies_tail g s s' n h_safe h_step⟩

/-- T10 applied: trace-safety implies the head state is gate-accepted. -/
theorem ev_T10_trace_implies_head
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s : EvmYul.EVM.State) (n : Nat)
    (h_safe : Parallax.TraceSafe g s (n+1) = true) :
    g.decide s = true :=
  Parallax.trace_safe_implies_head g s n h_safe

/-- T11 applied: trace-safety extends to the successor. -/
theorem ev_T11_trace_implies_tail
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s s' : EvmYul.EVM.State) (n : Nat)
    (h_safe : Parallax.TraceSafe g s (n+1) = true)
    (h_step : Parallax.EvmLikeMachine.step s = some s') :
    Parallax.TraceSafe g s' n = true :=
  Parallax.trace_safe_implies_tail g s s' n h_safe h_step

/-- T12 applied: a fully-disabled gate accepts ALL traces of any length
on any EVM state. -/
theorem ev_T12_disabled_accepts_all_traces (s : EvmYul.EVM.State) (n : Nat) :
    Parallax.TraceSafe permissiveGate s n = true :=
  Parallax.disabled_gate_accepts_all_traces permissiveGate s n rfl rfl rfl rfl

/-- T13 applied: reentrancy blocks the entire trace, not just one state. -/
theorem ev_T13_reentrancy_blocks_trace
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s : EvmYul.EVM.State) (n : Nat)
    (h_a4 : g.enabled_A4 = true)
    (h_depth : Parallax.EvmLikeMachine.callDepth s ≠ 0) :
    Parallax.TraceSafe g s n = false :=
  Parallax.reentrancy_blocks_trace g s n h_a4 h_depth

/-- T14 applied: unauthorized sender blocks the entire trace. -/
theorem ev_T14_unauthorized_blocks_trace
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s : EvmYul.EVM.State) (n : Nat)
    (h_a2 : g.enabled_A2 = true)
    (h_unauth : g.authorized (Parallax.EvmLikeMachine.sender s) = false) :
    Parallax.TraceSafe g s n = false :=
  Parallax.unauthorized_blocks_trace g s n h_a2 h_unauth

-- ────────────────────────────────────────────────────────────────
-- The 2 monotonicity / refinement theorems applied
-- ────────────────────────────────────────────────────────────────

/-- T15 applied: disabling A1 on EVM-state gates is strictly more
permissive — every state accepted by the stricter gate is accepted
by the relaxed gate. -/
theorem ev_T15_monotone_disable_A1 (s : EvmYul.EVM.State)
    (h_strict : strictGate.decide s = true) :
    relaxedGateA1Off.decide s = true :=
  Parallax.gate_monotone_disable_A1 strictGate relaxedGateA1Off s
    rfl rfl rfl rfl rfl rfl rfl h_strict

/-- T16 applied: gate decisions transfer across instances via an
address mapping. (Demonstrated with EVM.State → EVM.State identity.) -/
theorem ev_T16_refinement_via_mapping
    (g₁ g₂ : Parallax.AbstractGate EvmYul.EVM.State) (s : EvmYul.EVM.State)
    (h_a1 : g₁.enabled_A1 = false ∧ g₂.enabled_A1 = false)
    (h_a2 : g₁.enabled_A2 = false ∧ g₂.enabled_A2 = false)
    (h_a4 : g₁.enabled_A4 = false ∧ g₂.enabled_A4 = false)
    (h_a5 : g₁.enabled_A5 = false ∧ g₂.enabled_A5 = false) :
    g₁.decide s = g₂.decide s :=
  Parallax.refinement_via_address_mapping (fun s => s) (fun a => a)
    g₁ g₂ s h_a1 h_a2 h_a4 h_a5

-- ────────────────────────────────────────────────────────────────
-- The 2 decidability / determinism theorems applied
-- ────────────────────────────────────────────────────────────────

/-- T17 applied: gate decisions on EVM states are total. -/
theorem ev_T17_decision_total
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s : EvmYul.EVM.State) :
    g.decide s = true ∨ g.decide s = false :=
  Parallax.gate_decision_total g s

/-- T18 applied: gate decisions on EVM states are deterministic. -/
theorem ev_T18_decision_deterministic
    (g : Parallax.AbstractGate EvmYul.EVM.State) (s : EvmYul.EVM.State)
    (b₁ b₂ : Bool)
    (h₁ : g.decide s = b₁) (h₂ : g.decide s = b₂) :
    b₁ = b₂ :=
  Parallax.gate_decision_deterministic g s b₁ b₂ h₁ h₂

-- ────────────────────────────────────────────────────────────────
-- T19: demoState non-vacuity (the instance witnesses inhabitance)
-- ────────────────────────────────────────────────────────────────

theorem ev_T19_instance_witness :
    Nonempty (Parallax.EvmLikeMachine EvmYul.EVM.State) :=
  ⟨inferInstance⟩

-- ════════════════════════════════════════════════════════════════
-- THEOREMS ON CONCRETE EVM.STATE VALUES (beyond parametric)
-- 
-- These go further than "for all s : EVM.State". They construct
-- specific EVM.State values and apply the gate to them, producing
-- proof terms about specific, named states.
-- ════════════════════════════════════════════════════════════════

/-- The default-constructed EVM state. `EVM.State` derives `Inhabited`,
so this is well-typed. -/
def defaultEvmState : EvmYul.EVM.State := default

/-- C1: the permissive gate accepts the default EVM state. -/
theorem concrete_C1_permissive_accepts_default :
    permissiveGate.decide defaultEvmState = true :=
  Parallax.abstract_gate_disabled_accepts permissiveGate defaultEvmState
    rfl rfl rfl rfl

/-- C2: a trace of length 100 starting from the default state is
accepted by the permissive gate. -/
theorem concrete_C2_trace_100_safe :
    Parallax.TraceSafe permissiveGate defaultEvmState 100 = true :=
  Parallax.disabled_gate_accepts_all_traces
    permissiveGate defaultEvmState 100 rfl rfl rfl rfl

/-- C3: a trace of length 1000 — also accepted. The proof is the same
shape regardless of trace length; the abstract theorem is uniform. -/
theorem concrete_C3_trace_1000_safe :
    Parallax.TraceSafe permissiveGate defaultEvmState 1000 = true :=
  Parallax.disabled_gate_accepts_all_traces
    permissiveGate defaultEvmState 1000 rfl rfl rfl rfl

/-- C4: the strict gate rejects the default EVM state.
This follows because strictGate.authorized always returns false, and
strictGate enables A2 — so by T1, the gate rejects. -/
theorem concrete_C4_strict_rejects_default :
    strictGate.decide defaultEvmState = false :=
  Parallax.abstract_gate_rejects_unauthorized strictGate defaultEvmState rfl rfl

/-- C5: two applications of decide on the same state give the same answer
(determinism, applied concretely). -/
theorem concrete_C5_default_deterministic
    (b₁ b₂ : Bool)
    (h₁ : strictGate.decide defaultEvmState = b₁)
    (h₂ : strictGate.decide defaultEvmState = b₂) :
    b₁ = b₂ :=
  Parallax.gate_decision_deterministic strictGate defaultEvmState b₁ b₂ h₁ h₂

end Parallax5Evm.TheoremTransfer
