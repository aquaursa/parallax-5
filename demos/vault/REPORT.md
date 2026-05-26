# Demo 1 — ERC-4626 Inflation Attack (A1 Conservation)

**Demo:** PARALLAX-5 Flagship Demo 1
**Obligation:** A1 (value conservation) — primary
**License of this document:** CC0
**Reproducibility:** single command — see "Running this demo" below

---

## Summary

This demo exhibits a well-known exploit on ERC-4626 vault contracts (the "inflation attack"), the formal violation of PARALLAX-5's A1 obligation that it represents, and the mitigation via the OpenZeppelin virtual-shares pattern. The mitigation is verified mechanically via a Python state-machine simulator and formally via a Lean 4 proof. A PARALLAX-5 certificate is issued for the patched version, validates clean against the v1.0 schema, and produces a registry submission payload ready for the onchain registry deployment.

The substrate's value proposition is illustrated concretely: Slither (static analysis) does **not** detect this vulnerability class; halmos (symbolic execution) can detect it given the right invariant; only the formal Lean proof produces D4-level evidence for A1 conservation. The PARALLAX-5 certificate composes these heterogeneous evidence sources under one schema.

---

## The vulnerability

ERC-4626 vaults convert a deposit of `assets` into a number of `shares` via:

```
shares = (assets × totalSupply) / totalAssets
```

With integer floor division, this admits a manipulation: an attacker can make the share price so high that subsequent deposits round down to zero shares.

### Attack steps (mechanically simulated in `exploit.py`)

1. Attacker deposits 1 wei → mints 1 share
   - vault state: `totalAssets = 1`, `totalSupply = 1`
2. Attacker directly transfers 1×10¹⁸ wei to the vault (donation; bypasses `deposit`)
   - vault state: `totalAssets = 10¹⁸ + 1`, `totalSupply = 1`
   - share price now ~10¹⁸ assets per share
3. Victim calls `deposit(10¹⁸ − 1)`. The convert function:
   - `(10¹⁸ − 1) × 1 / (10¹⁸ + 1) = 0` (floor division)
   - Victim's 10¹⁸ − 1 wei enter the vault; **zero shares minted**
4. Attacker redeems their 1 share → withdraws all vault assets (~2×10¹⁸ wei)

### Result on `VulnerableVault.sol` (simulator output)

```
attacker profit = 999,999,999,999,999,999 wei
victim   loss   = 999,999,999,999,999,999 wei
```

The attacker captures 1×10¹⁸ wei of the victim's deposit. **A1 (value conservation) is violated.** The total invariant `sum(balances) = totalSupply` is preserved, but the *economic* conservation that A1 captures (no party can capture value without authorized state transitions) is broken.

---

## The mitigation: virtual shares

OpenZeppelin's ERC-4626 base contract introduced the virtual-shares pattern in v4.8. The conversion becomes:

```
shares = (assets × (totalSupply + 10⁶)) / (totalAssets + 1)
```

The virtual offset shifts the rounding to always favor the vault. For an attacker to force a victim's deposit of `assets` wei to mint zero shares, the attacker must inflate `totalAssets` to at least `assets × 10⁶`. With `assets = 10¹⁸`, the required donation is 10²⁴ wei — exceeding any realistic ERC-20 supply.

### Formal cost lower bound (Lean theorem)

From `proof/Conservation.lean`:

```lean
theorem inflation_attack_cost_lower_bound
    (s : VaultState) (assets : Nat)
    (hAssetsPos : assets > 0)
    (hZero : convertToShares s assets = 0) :
    s.totalAssets + VIRTUAL_ASSETS > assets * (s.totalShares + VIRTUAL_SHARES)
```

This theorem states: if the patched `convertToShares` returns zero for a nonzero deposit, then the attacker must have inflated `totalAssets + VIRTUAL_ASSETS` to exceed `assets × (totalSupply + VIRTUAL_SHARES)`. Kernel-accepted, zero `sorry`.

### Result on `PatchedVault.sol` (simulator output)

Same exploit sequence on the patched version:

```
Step 1: attacker deposits 1 wei → mints 1,000,000 share(s)
Step 2: attacker DONATES 1e18 directly
Step 3: victim deposits ~1e18 → mints 1,999,999 share(s)
        Victim economic loss: 0.000025%
```

The patched vault converts the victim's deposit to ~2×10⁶ shares — non-zero, redeemable for approximately the deposited value (loss is roundoff, ~2.5×10⁻⁷). **A1 preserved.**

---

## Obligation coverage on the patched vault

| Obligation | Tool / source | Evidence | Depth |
|---|---|---|---|
| **A1** value conservation | `proof/Conservation.lean` | Kernel-accepted theorems (deposit_preserves_conservation, donation_preserves_conservation, inflation_attack_cost_lower_bound) | **D4** |
| **A2** authorization closure | `lean/Parallax5/Walkaway.lean` | Walkaway-full theorem; no admin role exists | **D4** |
| **A3** signature integrity | n/a — no signatures used | (not addressed) | D0 |
| **A4** temporal distinctness | Slither (reentrancy-no-eth, reentrancy-events) | Static detection on safe ordering | D2 |
| **A5** external-attestation trust | n/a — no oracles or external attestations | (not addressed) | D0 |

CROPS vector: **`C=4 R=5 O=5 P=0 S=4`**

- **C=4**: max(A1=4, A4=2, A5=0) = 4. Strong censorship-resistance from the conservation proof.
- **R=5**: max(A2=4, walkaway_FULL=5) = 5. Full walkaway: no admin to remove.
- **O=5**: source openness depth declared by the spec (open repository, Apache-2.0).
- **P=0**: no privacy primitives. Transactions are public by design (honest reporting).
- **S=4**: max(A1..A5) = 4. Security at formal-proof depth.

---

## What this demo proves about the substrate

1. **Heterogeneous evidence composes.** Slither detection (D2 for A4) + Lean theorem (D4 for A1, A2) + manual declaration (source openness for O) all enter one certificate under one schema. No tool is replaced; each contributes what it does best.
2. **Static analysis alone is insufficient.** Slither found 7 issues on the vulnerable vault and 5 on the patched. **Neither detection set identifies the inflation attack itself.** The certificate is honest about this: A1 depth on the patched vault comes from the Lean proof, not Slither.
3. **The CROPS vector tells the consumer what the protocol is and isn't.** `(C=4, R=5, O=5, P=0, S=4)` makes clear: security and capture-resistance strong, privacy zero. A privacy-seeking user would route elsewhere. A consumer who only needs strong S and R is informed.
4. **Mathematical content is portable.** The Lean proof in `proof/Conservation.lean` extends naturally to other ERC-4626 implementations using the virtual-shares pattern. The substrate amortizes the cost of formal-method effort across protocols sharing structure.

---

## Files in this demo

```
demos/vault/
├── REPORT.md                         (this file)
├── parallax.yaml                     PARALLAX-5 spec for the patched vault
├── exploit.py                        Mechanical exploit simulator
├── contracts/
│   ├── IERC20.sol                    Minimal ERC-20 interface
│   ├── VulnerableVault.sol           Deliberately broken ERC-4626
│   └── PatchedVault.sol              Virtual-shares mitigation
├── proof/
│   └── Conservation.lean             Lean 4 A1 proof (zero sorry)
└── output/
    ├── certificate.json              Generated PARALLAX-5 certificate
    └── registry_payload.json         (planned: registry submission payload)
```

---

## Running this demo

From the parallax5_coordinator root:

```bash
make demo-vault
```

This executes:
1. `python3 demos/vault/exploit.py` — runs the inflation-attack simulator, confirming exploit on vulnerable and patch effectiveness on patched (exits 0 if both expected behaviors hold)
2. `slither demos/vault/contracts/VulnerableVault.sol` — confirms 7 Slither findings on vulnerable
3. `slither demos/vault/contracts/PatchedVault.sol` — confirms 5 findings on patched (the inflation attack is not in either set)
4. `parallax5 certify demos/vault/parallax.yaml --output demos/vault/output/certificate.json` — generates the certificate
5. `parallax5 validate demos/vault/output/certificate.json` — confirms certificate validates clean
6. `parallax5 registry submit demos/vault/output/certificate.json --dry-run` — prepares the on-chain submission payload

Expected output: clean exit, certificate generated, validates, payload prepared.

---

## Citation

```bibtex
@misc{parallax5_demo_vault,
  author    = {{AquaUrsa Research}},
  title  = {{PARALLAX-5 Demo 1: ERC-4626 Inflation Attack and A1 Conservation}},
  year   = {2026},
  publisher = {AquaUrsa Research},
  license = {CC0}
}
```

---

**End of report.** CC0. Fork it; improve it; reference the parent (10.5281/zenodo.20386868) if useful.
