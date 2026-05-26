# Walkaway Theorem — Companion Note

**Document version:** 1.0
**License:** CC0
**Companion to:** `lean/Parallax5/Walkaway.lean`
**Parent project DOI:** 10.5281/zenodo.20386868

---

## Abstract

The walkaway test, articulated informally by Vitalik Buterin in early 2026 as a criterion for DeFi protocol legitimacy, asserts that a protocol must continue to function correctly even if its founders, administrators, and governance participants disappear. This note formalizes that intuition as a mathematical property and mechanizes it in Lean 4. The result is the **Walkaway Theorem**: a sound, decidable test that classifies any protocol with a transcribable state machine into one of five spectrum positions.

The refined definition, adopted per external review, is: *no irreplaceable off-chain control over protected behavior*. This admits protocols with governance, multisigs, and timelocks that nevertheless do not depend on any specific identity continuing to act. The classification spectrum reflects nuance that a binary test would erase.

---

## 1. Motivation

Decentralized protocols make a foundational claim: that they continue to provide service without dependence on any single trusted party. The reality is heterogeneous. Some protocols (Uniswap V3 Core) deploy without admin keys at all. Some have timelock-protected admin functions. Some have multisigs with bounded scope. Some have single-key administrators who can pause, upgrade, or drain the protocol at will. And some claim decentralization while quietly depending on off-chain oracles, sequencers, or governance backstops.

Without a formal test, users cannot tell these apart. The walkaway theorem provides the test.

---

## 2. Informal statement

> A protocol $P$ satisfies the **walkaway property** if there exists a future history of $P$ in which all current administrators are removed from the active control set AND, for every protected obligation $A_i$, the obligation continues to hold in that history and in every state reachable from it.

The "active control set" is the set of principals (key holders, multisig participants, governance token holders with effective control) who can take actions that would falsify a protected obligation. The "protected obligations" are the five PARALLAX-5 obligations (A1–A5).

The property is existential ("there exists a future history"): we need only exhibit one path forward in which the admins are removed and the obligations hold. Most protocols do not actually need to take this path; the theorem provides assurance that they *could*.

---

## 3. Formal statement (Lean 4)

```lean
def walkawayProperty (sStart : ProtocolState) (admins : List Principal) : Prop :=
  ∃ h : History, witnessesWalkaway sStart admins h
```

where `witnessesWalkaway sStart admins h` requires:
1. `h.head? = some sStart` (the history starts at sStart)
2. `∀ a ∈ admins, ∀ sFinal ∈ h.getLast?, a ∉ sFinal.controlSet` (final state contains no admin)
3. `historyPreservesObligations h` (every state in h has all obligations satisfied)

The mechanization is in `lean/Parallax5/Walkaway.lean`. Kernel-accepted; zero `sorry`.

---

## 4. The five-level classification spectrum

| Class | Definition | Example |
|---|---|---|
| **Full** | No admin role exists within the protocol's certified obligation scope. The control set is empty under that scope. | A minimal admin-free CPMM; Uniswap V3 Core pool under scoped pool-safety obligations |
| **Bounded** | Admin role exists but is bounded by transparent timelock with verifiable parameters. | Aave V3 with timelocked governance |
| **Partial** | Admin role exists with multi-party quorum (multisig) and bounded operational scope. | A protocol with a 5-of-9 multisig limited to non-economic parameters |
| **Centralized** | Single point of failure exists: one principal whose removal would falsify obligations. | A protocol with single-key emergency pause |
| **Fake** | The protocol *claims* walkaway but has hidden off-chain dependencies. | A "decentralized" protocol whose price feed is a single off-chain oracle |

The `fake` classification is reserved for **third-party challengers**, not self-classification. A protocol cannot honestly classify itself as `fake`; this classification is the outcome of a successful Falsification Challenge of type `wrong_walkaway_classification` (per Vision and Roadmap §11 Move 11).

---

## 5. Worked example: minimal admin-free CPMM (Full, by construction)

The cleanest positive example is a minimal constant-product AMM with no factory, no protocol fee, no admin role at all. Swap, mint, and burn are the only entry points; all are driven by user transactions with no privileged caller. The control set is empty by construction, so full walkaway holds trivially.

```lean
def minimalCPMMState : ProtocolState where
  controlSet := []
  obligationsSatisfied := [true, true, true, true, true]

theorem minimal_cpmm_is_full_walkaway :
    walkawayProperty minimalCPMMState [] := by
  apply walkaway_trivial_for_empty_admins
  simp [allObligationsSatisfied, minimalCPMMState, List.all]
```

This is the substrate's canonical positive example. The proof discharges via `walkaway_trivial_for_empty_admins`, which is the theorem that an empty admin set trivially satisfies walkaway.

---

## 5.1 Scoped real-world example: Uniswap V3 Core pool

Uniswap V3 Core (factory at `0x1F98431c8aD98523631AE4a59f267346ea31F984` on mainnet) is the closest real-world analogue, but it requires careful scoping. The factory contract creates pool contracts; the pool contracts have no admin role affecting swap/mint/burn invariants. The factory itself, however, has a `setOwner` function and a protocol-fee switch the owner can configure (per Uniswap V3's published governance design).

The full walkaway claim for Uniswap V3 Core therefore applies to **pool-level safety only**, under a scoped obligation set that EXCLUDES factory-level protocol-fee configuration. Pool swap/mint/burn behavior is unaffected by the fee switch's setting; the fee switch is a commercial-layer parameter, not a safety-layer parameter.

```lean
def uniswapV3CorePoolScopedState : ProtocolState where
  controlSet := []  -- no admin role within pool's swap/mint/burn scope
  obligationsSatisfied := [true, true, true, true, true]

theorem uniswap_v3_core_pool_scoped_walkaway :
    walkawayProperty uniswapV3CorePoolScopedState [] := by
  apply walkaway_trivial_for_empty_admins
  simp [allObligationsSatisfied, uniswapV3CorePoolScopedState, List.all]
```

Hostile readers should challenge the scoping, not the theorem. The scoping is the substantive claim: walkaway over pool-level safety, with factory-level commercial parameters declared out-of-scope. Protocols that wish to publish a walkaway certificate need to declare their scope explicitly in the certificate's `walkaway.scope` field.

---

## 6. Worked counter-example: a centralized lending protocol

Many lending protocols (CompoundV2-era, early Aave, most newer DeFi) have an admin role with broad powers: pause withdrawals, modify interest rate models, change collateral parameters, upgrade implementation contracts. Removing the admin in these protocols would either:
- Render the protocol unable to respond to market emergencies (perhaps acceptable)
- Render the protocol unable to upgrade away from discovered vulnerabilities (concerning)
- Render the protocol's protected obligations unfalsifiable (acceptable only if obligations don't depend on admin)

The classifier:

```lean
def centralizedLendingState : ProtocolState where
  controlSet := [⟨1⟩]   -- single admin
  obligationsSatisfied := [true, true, true, true, true]

example : classifyWalkaway centralizedLendingState false false false = WalkawayClass.centralized := by
  simp [classifyWalkaway, centralizedLendingState, List.isEmpty]
```

This is honest. A protocol with single-key admin and no timelock is *centralized*. The certificate makes this explicit; the protocol may have other virtues (security, liquidity, user experience), but it cannot claim walkaway.

---

## 7. The Fake classification: detection of hidden dependencies

The `fake` classification is the substrate's mechanism for catching protocols that present a decentralized facade over centralized infrastructure.

Examples of hidden dependencies that would trigger `fake`:
- An "admin-free" smart contract that depends on a single off-chain price oracle controlled by the founding team
- A "permissionless" rollup whose sequencer is a single centralized entity
- A "DAO-governed" protocol whose actual upgrade authority sits with a multisig held by company employees
- A "decentralized bridge" whose validator set is controlled by a single party

The classification is necessarily a *judgment* informed by off-chain investigation, not a direct on-chain check. The Falsification Challenge framework operationalizes this: any third party can submit a challenge of type `wrong_walkaway_classification` with evidence of hidden dependencies. If the challenge is upheld, the certificate is updated and the `fake` classification is recorded.

Self-classification as `fake` is structurally impossible — no protocol issuer would honestly classify themselves this way. The classification's existence in the spectrum is what makes the challenge framework meaningful: there is a place for the truth to be recorded once discovered.

---

## 8. Theorems and their content

The Lean file contains four theorems plus a classification function:

### Theorem 1: `walkaway_trivial_for_empty_admins`

If the starting state has an empty control set and obligations are satisfied, then walkaway holds trivially.

**Significance**: this is the mathematical content of "full" walkaway. The empty admin set means admin removal is a no-op, and the satisfied obligations are preserved by the no-op transition.

### Theorem 2: `admin_removal_preserves_obligations`

Removing a principal from the control set does not change the obligation-satisfaction status of any state.

**Significance**: this captures the core walkaway intuition — admin presence and obligation satisfaction are independent properties. If a protocol's obligations *depend* on admin presence, this theorem's premise fails for that protocol, and the protocol is by definition not in the walkaway-preserving regime.

### Theorem 3: `bounded_walkaway_eventually_stable`

Under a bounded admin model (admin actions only affect protected obligations within a finite timelock window), there exists a history of length at least the timelock bound in which obligations are preserved.

**Significance**: justifies the `bounded` classification. After the timelock window, admin actions cannot falsify obligations, so walkaway holds eventually.

**Limitation**: the theorem's history is constructed by repeating the starting state (the abstract treatment lacks a concrete transition relation). Per-protocol instantiation requires plugging in the protocol's actual transition relation and showing that the bounded-admin assumption holds. This is the typical "abstract-to-concrete" pattern.

### Theorem 4: `centralized_excludes_full_walkaway`

If a state is strictly centralized (some principal's removal falsifies obligations), then full walkaway does not hold.

**Significance**: ensures the classification spectrum is exclusive — a protocol cannot simultaneously be classified as `full` and `centralized`. The classifier is sound: it never classifies a centralized protocol as full.

---

## 9. Limitations and honest scope

The walkaway theorem, as mechanized, addresses:
- **On-chain control structure** (admin roles, multisigs, governance hooks)
- **Obligation preservation under control-set transitions**

It does **not** address:
- **Off-chain dependencies** (oracles, sequencers, infrastructure) — these enter via the `fake` classification but require off-chain investigation
- **Liveness** — walkaway is about safety (obligations preserved); a protocol may walkaway-safely while becoming non-functional
- **Economic incentives** — a protocol may pass walkaway formally while having economics that incentivize attacks
- **Compiler / toolchain correctness** — assumed sound; out of scope for the application-layer theorem

These limitations are honestly disclosed in every walkaway-classified certificate via the `dependencies_disclosed` field and the trust base.

---

## 10. Relationship to CROPS

The walkaway property is the application-layer formalization of the **R-dimension** (capture-resistance) in the CROPS framework. The Walkaway classification is one of the inputs to the `crops_vector.R` computation in a certificate.

Specifically:
- `walkaway: full` → R = 5
- `walkaway: bounded` → R = 4 (with timelock parameters disclosed)
- `walkaway: partial` → R = 3 (with multisig parameters disclosed)
- `walkaway: centralized` → R = 1
- `walkaway: fake` → R = 0

The R-dimension is one of five CROPS dimensions; the full mapping is documented in `docs/CROPS_VECTOR.md`.

---

## 11. Adversarial review

The walkaway theorem is subject to the Falsification Challenge framework. Specifically, challenge type `wrong_walkaway_classification` (per Vision and Roadmap §11 Move 11) provides the formal mechanism for disputing a protocol's self-claimed classification.

Three challenge patterns are particularly relevant:

1. **Hidden dependency challenge**: the challenger provides evidence that a protocol claiming `full` or `bounded` has an off-chain dependency that, if removed, would falsify obligations. If upheld, the certificate is updated to `fake`.

2. **Scope-overreach challenge**: the challenger provides evidence that a protocol's admin role can perform actions beyond the disclosed scope. The certificate's admin-bound classification is revised downward.

3. **Timelock-bypass challenge**: the challenger provides evidence that the disclosed timelock can be bypassed (via emergency procedures, upgrade hooks, etc.). The `bounded` classification fails to hold.

We invite these challenges.

---

## 12. Open problems

1. **Quantitative bounded walkaway**: the `bounded` classification currently treats timelock-protected admin as a single category. A finer-grained metric (timelock duration, scope breadth, transparency) would be more informative.

2. **Composite walkaway**: protocols composed from multiple sub-protocols (e.g., a vault on top of a lending market on top of an AMM) inherit the walkaway classification of the most centralized component. The composition rule is intuitive but not yet mechanized.

3. **Time-varying walkaway**: a protocol's walkaway classification may change as governance evolves. The certificate's validity window captures this informally; a more sophisticated treatment would version walkaway with explicit transition rules.

These are areas for v1.1 of the theorem.

---

## 13. Citation

```bibtex
@misc{duncan2026walkawaytheorem,
  author    = {{AquaUrsa Research}},
  title     = {{The Walkaway Theorem: Formalizing Capture-Resistance in PARALLAX-5}},
  year      = {2026},
  version   = {1.0},
  publisher = {AquaUrsa Research},
  license   = {CC0},
  url       = {https://parallax.xyz/walkaway}
}
```

---

**End of note.**

This document is CC0. The Lean 4 mechanization in `lean/Parallax5/Walkaway.lean` is Apache-2.0. Both are freely reusable.
