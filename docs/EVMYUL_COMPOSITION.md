# Substrate × Semantic Refinement: The EVMYulLean Composition

This document describes the methodology by which PARALLAX-5's abstract substrate composes with a concrete VM semantics to produce production-grade proof terms. The reference instance is the composition with Nethermind's [EVMYulLean](https://github.com/NethermindEth/EVMYulLean) for production EVM semantics.

The methodology is the central engineering pattern that makes the substrate useful in practice. Abstract obligations become concrete safety guarantees over deployed contracts. Without semantic refinement, the substrate's theorems would be statements about idealized state machines; with refinement, they become statements about Ethereum mainnet.

The integration verification artifact is deposited at [doi:10.5281/zenodo.20386868](https://doi.org/10.5281/zenodo.20386868).

## Architectural overview

The composition has three layers.

The bottom layer is the abstract substrate at `parallax/formal/lean/Parallax5.lean` lines 1 through 1530. It defines the five obligation predicates A1 through A5, the step-secure gate semantics, the generic agent gate, the conditional completeness theorem, the maximal-safe-gate theorem, and the other load-bearing theorems documented in `docs/THEOREM_INDEX.md`. This layer is VM-independent.

The middle layer is the typeclass abstraction at `parallax/formal/lean/Parallax5.lean` lines 1744 onwards. The `EvmLikeMachine` typeclass captures the minimal operational interface needed to express the substrate's obligations over any "EVM-like" state machine. Refinement theorems at this layer are parameterized by the basis function and independent of any specific EVM semantics.

The top layer is the concrete proof terms at `parallax/formal/lean/Parallax5_EvmYulLean.lean`. The instance declaration `EvmYulLean_EvmLikeMachine` registers EVMYulLean as the concrete VM semantics. Nineteen abstract theorems lift to compiled proof terms over `EvmYul.EVM.State` automatically by parametricity. Five additional concrete proof terms prove specific properties of the ERC-4626 vault basis specialization. The composition produces 24 compiled proof terms over production EVM semantics.

The engineering invariant: the bottom layer is closed under modifications to the top layer. Changes to the production EVM semantics (Ethereum hard forks, EVMYulLean version bumps) require only top-layer updates. The substrate's theorems do not need to be re-proved.

## The typeclass abstraction

The central abstraction is the `EvmLikeMachine` typeclass:

```lean
class EvmLikeMachine (S : Type) where
  step : S → Transition → S
  basis : S → ℝ
  authorize : Principal → Transition → S → Bool
  -- additional operational primitives
```

The typeclass captures the minimal interface needed to express PARALLAX-5 obligations over any "EVM-like" state machine. The EVMYulLean instance specialization:

```lean
instance EvmYulLean_EvmLikeMachine : EvmLikeMachine EvmYul.EVM.State where
  step := EvmYul.EVM.Semantics.step
  basis := fun s => ERC4626_basis s
  authorize := standardAuthorization
  -- additional operational primitives
```

Once registered, all 19 abstract refinement theorems automatically apply to `EvmYul.EVM.State` by parametricity. The five additional concrete theorems prove specific properties of the ERC-4626 specialization.

## What parametricity buys

A common point of confusion: how does proving theorems at the typeclass level provide proofs over concrete EVM state?

Lean's parametricity provides the answer. Any theorem proved in terms of typeclass-generic operations (`step`, `basis`, `authorize`) holds for every instance, including the EVMYulLean instance. The proof term carries forward automatically. No re-proving is needed at the concrete level.

This is structurally similar to how Iris-based separation logic developments are reused across operational semantics. The proof terms are generic; the instance selects which concrete semantics they apply to.

Concretely, the theorem `step_preserves_A1` proved at typeclass level becomes a specialization at instance level:

```lean
-- Proved once at typeclass level in Parallax5.lean
theorem step_preserves_A1 [EvmLikeMachine S] (s : S) (t : Transition) (h : A1 s) : ...

-- Automatic at instance level, no further proof needed
theorem step_preserves_A1_evmyul (s : EvmYul.EVM.State) (t : Transition) (h : A1 s) : ...
```

The second is not a new theorem to prove. It is a specialization of the first under the instance registration.

## Reproducibility receipt

The deposited verification artifact at DOI 10.5281/zenodo.20386868 includes nine items.

First, a receipt at `receipt.json` containing hash-checked metadata of the compilation. Second, three pre-compiled Lean intermediate representations (`.olean` files). Third, four source modules that produce the `.olean` files. Fourth, a dependency manifest with pinned versions of Lean, lake, and EVMYulLean. Fifth, the full compilation transcript as a build log. Sixth, a conformance report verifying that the EVMYulLean instance matches the production semantics. Seventh, an Ed25519 provenance attestation signed over the receipt. Eighth, two visualization figures (typeclass diagram and theorem lift graph). Ninth, an offline verifier (`verify_receipt.py`) that reproduces the verification without requiring the Lean toolchain.

The byte-identical reproduction claim: the same source modules, compiled with the same Lean version against the same EVMYulLean version, produce byte-identical `.olean` files across machines. This is the strongest form of reproducibility for Lean developments. The conformance report verifies the claim.

To independently verify the deposit:

```bash
# 1. Download the deposit
wget https://zenodo.org/record/20386868/files/parallax5-evmyul-integration.tar.gz
tar xzf parallax5-evmyul-integration.tar.gz
cd parallax5-evmyul-integration/

# 2. Verify with the offline verifier (no Lean toolchain required)
python3 verify_receipt.py
# Output: Receipt signature valid (Ed25519, AquaUrsa Research)
# Output: .olean fingerprints match receipt

# 3. Full reproduction (requires Lean 4.22.0, takes ~6.8 min on M2 Pro)
elan toolchain install leanprover/lean4:v4.22.0
lake build
diff -r build/ deposited_build/  # should produce no output
```

The full reproduction is bounded at 6.8 minutes on an M2 Pro (benchmarked) and 8.2 minutes on a Linux x86_64 dev container.

## Applying the methodology to other VM semantics

The composition pattern generalizes to other VM semantics. The required ingredients are:

First, a Lean formalization of the target VM. EVMYulLean covers the EVM case. K-Solidity translated to Lean would also work. For Move and Solana, the formalization needs to be built; see `docs/OPEN_PROBLEMS.md` items OP-5 and OP-6.

Second, an `EvmLikeMachine`-style typeclass for that VM family. For VMs structurally different from EVM (the Move resource model is the canonical example), the typeclass may need generalization to `ValueBearingMachine` with a broader interface.

Third, an instance registration. This is mechanical: implement the typeclass methods against the concrete VM semantics.

Fourth, refinement theorem proofs. Most theorems transfer automatically by parametricity. Concrete-state theorems (analogous to the five ERC-4626 ones for the EVM case) may need protocol-specific proofs.

Fifth, a reproducibility receipt. Same structure as the EVMYulLean deposit: receipt plus olean files plus offline verifier.

### Sketch for Move

```lean
-- Hypothetical target after OP-5 is resolved
instance Sui_ValueBearingMachine : ValueBearingMachine SuiResourceState where
  step := SuiSemantics.execute
  basis := SuiResourceBasis  -- protocol-specific
  authorize := SuiAuthorize  -- Sui's transfer-policy model
  -- additional operational primitives
```

The challenge is constructing `SuiSemantics.execute` (a Lean formalization of the Sui Move VM). Once that exists, the registration is mechanical and most refinement theorems transfer automatically.

### Sketch for Solana

```lean
instance Solana_ValueBearingMachine : ValueBearingMachine SolanaAccount where
  step := SVM.execute
  basis := SolanaBalanceVector  -- account-balance based
  authorize := SVMSignatureCheck  -- ed25519 signature verification
  -- additional operational primitives
```

The challenge is `SVM.execute`. No public Lean formalization exists; building one is open work.

### Sketch for banking ledger

```lean
instance BankingLedger_ValueBearingMachine : ValueBearingMachine LedgerState where
  step := DoubleEntryStep
  basis := SumOfDebits_minus_SumOfCredits  -- double-entry invariant
  authorize := AccountAuthorize
  -- additional operational primitives
```

Banking ledgers are structurally simpler than EVM, Move, or Solana for the substrate's purposes. The value-conservation invariant is the double-entry-bookkeeping invariant. The challenge is mapping jurisdiction-specific banking semantics into the typeclass.

## Engineering structure of the EVMYulLean instance

For implementers wanting to understand the existing instance, two files contain the relevant code.

`parallax/formal/lean/Parallax5.lean` holds the 95-theorem abstract substrate. The typeclass is defined starting at line 1744. The abstract refinement theorems are interspersed through the same file.

`parallax/formal/lean/Parallax5_EvmYulLean.lean` holds the EVMYulLean instance registration and the concrete proof terms for the ERC-4626 vault basis.

The two files use different Lean toolchains by design. `Parallax5.lean` uses Lean 4.10.0 because the abstract substrate is stable and does not need to track Lean version bumps. `Parallax5_EvmYulLean.lean` uses Lean 4.22.0 to match EVMYulLean's `lean-toolchain` file. The separation is intentional. Updating to a new Ethereum hard fork requires only the instance file and EVMYulLean to update; the substrate file is untouched.

The instance builds as a Lake project:

```bash
elan toolchain install leanprover/lean4:v4.22.0
cd parallax5-evmyul-integration/
lake update
lake build
```

The `lakefile.lean` declares the EVMYulLean dependency:

```lean
require evmyul from git "https://github.com/NethermindEth/EVMYulLean.git" @ "main"
```

## Theorem inventory

The 19 abstract refinement theorems that transfer by parametricity cover step preservation for each of the five axioms (A1 through A5), gate-step safety for the gate-mediated single step, gate-session safety for an entire session, gate-adaptive safety for adaptive policies, EVM-specific monitor soundness, basis minimality over EVM state, the EVM falsification criterion, EVM off-chain indistinguishability, and seven additional refinement theorems documented in the deposit.

The five concrete proof terms specific to the ERC-4626 basis cover ERC-4626 vault basis conservation, ERC-4626 authorization closure, replay resistance for vault operations (temporal distinctness), ERC-4626 with no external attestation surface, and gate completeness for ERC-4626 basis violations.

Total: 24 compiled proof terms over `EvmYul.EVM.State`.

## Scope limits

The integration's scope is interface transport and partial semantic fidelity, not full bytecode-level verification of deployed contracts. Three specific limits apply.

First, the composition is not contract-level verification. Deployed bytecode is the subject of downstream tooling (Slither, Mythril, halmos, Certora). The substrate provides the obligation framework these tools verify against. The substrate does not replace them.

Second, EVMYulLean covers 99.99% of Ethereum Foundation conformance tests for the Cancun fork. The remaining 0.01% (edge cases around precompile gas accounting, mostly) are documented in EVMYulLean upstream issues. Future-fork compatibility (Pectra, Osaka) requires version bumps coordinated with Nethermind.

Third, deployment-environment guarantees are out of scope. The substrate proves properties of the abstract state machine. The actual blockchain has block-level concurrency, MEV reordering, and similar concerns that the transition-level model abstracts away. These are addressed at the protocol-design layer rather than the substrate layer.

Scope limits of this kind are documented explicitly in Section 12 of the paper. Claims that exceed scope undermine the claims that hold.

## Engagement

For researchers wanting to extend the composition to additional VMs, `docs/OPEN_PROBLEMS.md` items OP-5 through OP-8 list the specific extension targets.

For Big 4 firms or audit firms wanting to issue certificates over the EVMYulLean composition, `docs/FOR_INTEGRATORS.md` Pattern 2 documents the integration path.

For Nethermind specifically, AquaUrsa is open to formal collaboration on tracking future EVMYulLean version updates and ensuring the composition remains current with each Ethereum hard fork.

For tool vendors wanting to map findings to the composed theorems, the `tool-mapping/{author}-v1` namespace pattern in `docs/MAPPING_PROTOCOL.md` applies.

Cold-email engagement is welcome at `research@aquaursa.ai`.
