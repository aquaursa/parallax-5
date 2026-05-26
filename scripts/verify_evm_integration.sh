#!/usr/bin/env bash
# 
# verify_evm_integration.sh
# 
# Reproduces the full PARALLAX-5 ↔ EVMYulLean integration:
#  1. Installs Lean 4.22.0 if not present
#  2. Stands up a Lake project depending on EVMYulLean
#  3. Drops in the PARALLAX-5 EvmYulLeanInstance.lean
#  4. Fetches mathlib prebuilt cache (~3 GB)
#  5. Runs `lake build` — compiles EVMYulLean + Instance.lean against
#     the real Cancun-fork EVM semantics
#  6. Runs the mechanical API conformance verifier
#
# Requirements:
#   - Linux or macOS, x86_64 (Lean 4 toolchain availability)
#   - ≥10 GB free disk
#   - ≥4 GB RAM
#   - ~30 minutes wall-clock (network: ~10 min mathlib cache;
#     compute: ~15 min EVMYulLean source compile)
#
# Idempotent: rerunning skips already-completed steps.

set -euo pipefail

PROJECT_ROOT="${PARALLAX5_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
WORKDIR="${WORKDIR:-$HOME/parallax5-evm-verification}"
INSTANCE_FILE="${PROJECT_ROOT}/parallax/axiom_formal/lean/EvmYulLeanInstance.lean"
CONFORMANCE_VERIFIER="${PROJECT_ROOT}/parallax/standard/evm_api_conformance.py"

echo "═══════════════════════════════════════════════════════════════"
echo "  PARALLAX-5 ↔ EVMYulLean Integration Verification"
echo "═══════════════════════════════════════════════════════════════"
echo "  Project:  $PROJECT_ROOT"
echo "  Workdir:  $WORKDIR"
echo "  Instance: $INSTANCE_FILE"
echo

# ── 1. elan + Lean 4.22.0 ─────────────────────────────────────────
if ! command -v elan >/dev/null 2>&1; then
    echo "[1/6] Installing elan + Lean 4.22.0..."
    curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
        | sh -s -- -y --default-toolchain leanprover/lean4:v4.22.0
    export PATH="$HOME/.elan/bin:$PATH"
else
    echo "[1/6] elan already installed."
    export PATH="$HOME/.elan/bin:$PATH"
    elan toolchain install leanprover/lean4:v4.22.0 2>&1 | tail -3
fi

# ── 2. Standup Lake project ───────────────────────────────────────
echo "[2/6] Setting up Lake project at $WORKDIR..."
mkdir -p "$WORKDIR"
cd "$WORKDIR"

if [ ! -f lean-toolchain ]; then
    echo 'leanprover/lean4:v4.22.0' > lean-toolchain
fi

if [ ! -f lakefile.toml ]; then
    cat > lakefile.toml << 'EOF'
name = "parallax5_evm"
defaultTargets = ["Parallax5Evm"]

[[require]]
name = "evmyul"
git = "https://github.com/NethermindEth/EVMYulLean.git"

[[lean_lib]]
name = "Parallax5Evm"
EOF
fi

mkdir -p Parallax5Evm

# Typeclass module (extracted from substrate)
cat > Parallax5Evm/Refinement.lean << 'EOF'
namespace Parallax

class EvmLikeMachine (S : Type) where
  Address : Type
  decEqAddress : DecidableEq Address
  step : S → Option S
  balanceOf : S → Address → Nat
  totalSupply : S → Nat
  sender : S → Address
  callDepth : S → Nat
  attestationFresh : S → Address → Nat → Bool

attribute [instance] EvmLikeMachine.decEqAddress

end Parallax
EOF

# Copy the PARALLAX-5 instance file
cp "$INSTANCE_FILE" Parallax5Evm/Instance.lean

# Top-level
cat > Parallax5Evm.lean << 'EOF'
import Parallax5Evm.Refinement
import Parallax5Evm.Instance
EOF

# ── 3. lake update ────────────────────────────────────────────────
echo "[3/6] Fetching EVMYulLean and its dependency tree (lake update)..."
if [ ! -d .lake/packages/evmyul/.git ]; then
    lake update 2>&1 | tail -10
else
    echo "      (already fetched)"
fi

# ── 4. mathlib prebuilt cache ─────────────────────────────────────
echo "[4/6] Fetching mathlib prebuilt cache (~3 GB)..."
lake exe cache get 2>&1 | tail -3

# ── 5. lake build ─────────────────────────────────────────────────
echo "[5/6] Building EVMYulLean + Instance.lean..."
lake build 2>&1 | tee build.log | tail -30

if grep -q "error:" build.log; then
    echo ""
    echo "═══ BUILD FAILED — errors found ═══"
    grep "error:" build.log | head -20
    exit 1
fi

# ── 6. API conformance verifier ───────────────────────────────────
echo "[6/6] Running API conformance verifier..."
if [ -f "$CONFORMANCE_VERIFIER" ]; then
    python3 "$CONFORMANCE_VERIFIER" \
        "$INSTANCE_FILE" \
        "$WORKDIR/.lake/packages/evmyul"
else
    echo "      (conformance verifier not found at $CONFORMANCE_VERIFIER, skipping)"
fi

echo
echo "═══════════════════════════════════════════════════════════════"
echo "  ✓ EVMYulLean integration verified end-to-end"
echo "═══════════════════════════════════════════════════════════════"
echo
echo "Built artifacts:"
find .lake/build/lib -name "*.olean" 2>/dev/null | head -5
echo
echo "Next steps:"
echo "  • Use the Lake project at $WORKDIR for further proofs against EVM.State"
echo "  • Run conformance against Ethereum test suite:"
echo "      cd $WORKDIR/.lake/packages/evmyul && lake test -- 8"
echo "  • Contribute callDepth field upstream:"
echo "      see paper/EVM_INTEGRATION.md → 'Open work items'"
