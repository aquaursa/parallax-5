# Case Study 1: ERC-4626 Vault — A1/A4 in Action

**Goal**: Demonstrate PARALLAX-5 at compliance level **P3** (Symbolically Checked) on a representative ERC-4626 vault, showing how the substrate composes Z3 + halmos + ObligationSol + Lean to discharge the A1 conservation and A4 temporal obligations.

## The Vulnerability: Share Inflation (Cream archetype)

The vulnerable vault rounds shares down on deposit:
```solidity
shares = (assets * totalShares) / totalAssets;  // floor division
```

When `totalAssets >> totalShares`, a victim's deposit can mint zero shares:
- Attacker deposits 1 wei → mints 1 share (first-depositor branch)
- Attacker donates 524,288 wei directly to the vault
- State: `totalAssets = 524,289, totalShares = 1`
- Victim deposits 524,288 wei → `floor(524288 * 1 / 524289) = 0` shares
- Victim's assets now back the attacker's single share

**Obligation signature**: σ(t) = {A1}. The conservation relation `backing ≥ claims` is violated.

## Mechanical Evidence

### Z3 SMT (`parallax/axiom_formal/independence.py`)
Z3 produces the SAT witness `(donation=524288, victimDeposit=524288)`. Verdict: **REFUTED**.

### halmos symbolic execution (`parallax/axiom_formal/halmos/contracts/CreamClone.t.sol`)
halmos finds the same witness at the EVM bytecode level over symbolic paths. Verdict: **FAIL** with concrete counterexample.

### Lean theorem (`parallax/axiom_formal/lean/ParallaxAxioms.lean`)
Theorem `a1_complete_for_share_inflation` proves: any transition that produces zero shares against positive assets violates A1.

## The Patch: MIN_LIQUIDITY + Minimum-Shares Check

```solidity
uint256 constant MIN_LIQUIDITY = 1000;

function deposit(uint256 assets, address receiver) external returns (uint256 shares) {
    require(assets > 0, "PARALLAX-A1: zero deposit");
    if (totalShares == 0) {
        shares = assets;
        require(shares >= MIN_LIQUIDITY, "PARALLAX-A1: below min");
        _mint(DEAD, MIN_LIQUIDITY);  // permanent liquidity
    } else {
        shares = (assets * totalShares) / totalAssets;
        require(shares > 0, "PARALLAX-A1: zero shares");
    }
}
```

- halmos verdict on `CreamClone_hardened.t.sol`: **PASS over 6 symbolic paths**
- Z3 inductive preservation: **UNSAT** (no counterexample exists)
- Lean theorem `a1_preserved_by_deposit_hardened`: **discharged without sorry**

## The PARALLAX-5 Certificate (P3)

```json
{
  "compliance_level": "P3",
  "obligation_map": {
    "deposit(uint256,address)": ["A1", "A2", "A4"],
    "redeem(uint256,address,address)": ["A1", "A2", "A4"]
  },
  "proof_artifacts": {
    "A1": { "tool": "halmos", "verdict": "PASS", "paths_explored": 6, ... },
    "A4": { "tool": "halmos", "verdict": "PASS", "paths_explored": 3, ... }
  }
}
```

A P4 certificate adds a Lean theorem hash; a P5 certificate adds a deployed step-secure gate address.

## What This Case Study Demonstrates

1. **Composition**: ObligationSol regex flags the pattern, Z3 confirms at the model level, halmos confirms at bytecode, Lean proves the meta-theorem. Each tool plays a precisely defined role — no overlap, no gap.
2. **Falsification**: The vulnerable contract is REFUTED independently by every tool — the basis is mechanically observable.
3. **Generic hardening**: The conservation-wrapper pattern (`require(shares > 0)`) is provably correct via the Lean theorem `conservation_wrapper_preserves_A1`. Not bespoke to this vault.
4. **Audit-ready output**: The certificate composes per-obligation evidence from multiple tools into a single artifact suitable for an audit report or an insurance underwriting input.
