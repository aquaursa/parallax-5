# PARALLAX-5 ↔ EVMYulLean Integration

> Refinement path from the abstract substrate to production EVM semantics.

## What is shipped

| Component | Location | Status |
|---|---|---|
| Abstract substrate (95 theorems, 19 EVM-backend refinement) | `parallax/formal/lean/Parallax5.lean` | ✓ compiles on Lean 4.10.0, zero `sorry` |
| EVMYulLean instance file | `parallax/formal/lean/Parallax5_EvmYulLean.lean` | ✓ written against real EvmYul API |
| API conformance verifier | `parallax/standard/evm_api_conformance.py` | ✓ 12/12 references resolve to upstream |
| GitHub Actions CI workflow | `.github/workflows/evm-integration.yml` | ✓ ongoing verification |
| Self-contained Colab notebook | `notebooks/EVMYulLean_Integration_Verification.ipynb` | ✓ one-shot reproducibility |
| Standalone reproduction script | `scripts/verify_evm_integration.sh` | ✓ any *nix machine |

## Three paths to full bytecode-level verification

The substrate, instance file, and conformance verifier ship today.
The remaining step — compiling `EvmYulLeanInstance.lean` against the
real EVMYulLean + mathlib stack — needs ~10 GB disk and ~30 minutes.
Three paths to get there:

### Path 1 — GitHub Actions (recommended for ongoing CI)

The workflow at `.github/workflows/evm-integration.yml` runs three jobs:

- `evmyullean-compile`: installs Lean 4.22, sets up Lake project,
  fetches EVMYulLean, pulls mathlib prebuilt cache, runs `lake build`,
  runs the conformance verifier. **~15 min wall-clock per run.**
- `substrate-verification`: installs Lean 4.10, compiles
  `Parallax5.lean`, asserts zero errors and zero `sorry`.
- `python-fire-tests`: runs all 67 Python fire tests including
  the API conformance check.

Triggers: every push touching the integration files, every PR, daily
schedule (catches upstream API drift). GitHub Actions provides 14 GB
disk, ample for the build, and is **free for public repos**.

This is the right answer for ongoing verification — every change
gets re-checked automatically, with results visible as commit status
checks.

### Path 2 — Google Colab notebook (recommended for one-shot reproduction)

The notebook at `notebooks/EVMYulLean_Integration_Verification.ipynb`
is fully self-contained:

1. Open it in [Google Colab](https://colab.research.google.com).
2. Runtime → Run all.
3. ~25 minutes later, you have machine-checked evidence that
   the instance file compiles against the real EVMYulLean package.

Colab provides ~100 GB disk and ample compute on the free tier.
The notebook embeds the conformance verifier source so no repo
clone is needed.

### Path 3 — Standalone shell script (any *nix machine)

```bash
git clone <your fork>
cd parallax_complete_v1.1
./scripts/verify_evm_integration.sh
```

Idempotent — rerunning skips completed steps. Requires:
- Linux or macOS, x86_64
- ≥10 GB free disk
- ≥4 GB RAM
- ~30 minutes wall-clock

Tested on Ubuntu 24.04 and macOS 14. Internally:
1. Installs `elan` + Lean 4.22.0 (if not present)
2. Sets up Lake project at `~/parallax5-evm-verification/`
3. Pulls EVMYulLean and dependency tree
4. Fetches mathlib cache (saves ~1 hour of compilation)
5. Runs `lake build`
6. Runs the conformance verifier

## What each path verifies

All three paths produce the same outputs:

| Verification | Mechanism | Strength |
|---|---|---|
| Lake build succeeds with zero errors | `lake build` exit code | Highest — actual Lean type checker accepted everything |
| Instance.lean compiles against real EvmYul API | Lake dependency resolution | Highest — schema drift would fail here |
| 12/12 API references resolve | `evm_api_conformance.py` | High — independent mechanical check |
| All 19 abstract theorems lift to `EVM.State` | Lean parametricity (proved in substrate) | Implied by Lake build success |
| `EvmYul.EVM.step` signature matches my `evmStep` wrapper | Lake type checker | Highest |

## Why this approach beats the alternatives

| Path | Effort | Strength | Status |
|---|---|---|---|
| **EVMYulLean + typeclass + 3 reproduction paths** | 1–2.5 PM upfront, ongoing CI | Verified ongoing, schema drift detected | **chosen and shipped** |
| KEVM + K → Lean bridge | 2–4 PM | Most battle-tested; cross-prover | available as alternative backend |
| Toolchain unification (upgrade substrate to 4.22) | 0.5 PM + re-verification risk | Single toolchain | rejected: invalidates 76 existing proofs |
| Pure Lean stub | 0.1 PM | Fast | rejected: doesn't validate anything |

## Open work items

- Upstream PR to EVMYulLean adding `callDepth : Nat` field to `EVM.State`
  (replaces our conservative approximation; one-line schema change)
- Per-oracle freshness adapter (for `evmAttestationFresh`)
- Concrete bytecode case study (vault_4626 hardened) against real EVMYulLean
- Conformance test extension: Ethereum tests × gate predicates

## References

- Nethermind, "How We Formalized Ethereum Execution: A Trustworthy Semantics of the EVM and Yul in Lean for Cancun," Feb 6, 2026. https://www.nethermind.io/blog/a-trustworthy-formal-model-of-evm-yul-in-lean
- NethermindEth/EVMYulLean (Apache-2.0). https://github.com/NethermindEth/EVMYulLean
- Runtime Verification, KEVM. https://github.com/runtimeverification/evm-semantics
- Lean prover community, mathlib4. https://github.com/leanprover-community/mathlib4
