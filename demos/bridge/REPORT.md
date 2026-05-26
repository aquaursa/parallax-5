# Demo 2 — Bridge Attestation (A3 Signature Integrity + A5 Attestation Trust)

**Demo:** PARALLAX-5 Flagship Demo 2
**Obligations:** A3 (signature integrity), A5 (external-attestation trust) — primary
**License of this document:** CC0
**Reproducibility:** single command — `make demo-bridge`

---

## Summary

Cross-chain bridges have historically been the largest single source of DeFi losses: Wormhole ($320M, Feb 2022), Ronin ($625M, Mar 2022), Nomad ($190M, Aug 2022), Multichain ($126M, Jul 2023). The common pattern across these incidents is **attestation-validation failure**: the bridge accepts attestations it should not have accepted. This demo formalizes two attestation-validation failure classes and demonstrates their mitigation.

The two vulnerability classes:

1. **ECDSA signature malleability** (A3 violation). The bridge accepts both `(r, s)` and `(r, n − s)` as valid signatures for the same message; an attacker replays a malleated copy under a different message identifier.
2. **Stale attestation acceptance** (A5 violation). The bridge has no freshness window; old attestations can be withdrawn long after the validator set has rotated.

Both are mitigated in `PatchedBridge.sol` via standard mechanisms: low-s ECDSA enforcement (EIP-2) and a one-hour freshness window with epoch-binding hash. The mitigations are mechanized in Lean 4.

---

## Vulnerability 1: Signature malleability (A3)

### The cryptographic property

For any valid ECDSA signature `(r, s)` over message `M` and public key `P`, the pair `(r, n − s)` is *also* a valid signature for the same `M` and `P`, where `n` is the curve order. This is the **signature malleability property**: every signature has a "twin" that verifies identically.

Pre-EIP-2 (2015), Ethereum had no canonical-form requirement. Post-EIP-2, the convention is that `s ≤ n/2` is canonical (low-s) and `s > n/2` is non-canonical (high-s). EIP-2 transactions reject high-s. But **smart contracts that call `ecrecover` directly inherit no such enforcement.** A bridge contract that uses `ecrecover` without explicitly rejecting high-s remains vulnerable.

### Attack on `VulnerableBridge.sol`

```
Step 1: validators sign withdrawal message M with low-s signatures (r, s)
Step 2: bridge processes M correctly; pays out to legitimate recipient
Step 3: attacker constructs (r, n - s) — valid for the same M and signers
Step 4: attacker re-broadcasts withdrawal under message hash M' = keccak(M ‖ "replayed")
        with malleated signatures
Step 5: vulnerable bridge accepts; pays out to attacker
```

### Simulator output

```
First withdrawal (low-s signatures): SUCCEEDED
Replay with malleated (high-s) signatures on different msg hash: SUCCEEDED
⚠ The vulnerable bridge accepted high-s signatures (A3 violation)
```

### Mitigation

```solidity
require(uint256(s[i]) <= uint256(SECP256K1N_DIV_2), "high-s rejected");
```

This single check eliminates the malleability vector. Lean theorem `patched_rejects_high_s` formalizes the property.

### Patched simulator output

```
Legitimate withdrawal (low-s): SUCCEEDED
✓ High-s signatures rejected: high-s rejected
```

---

## Vulnerability 2: Stale attestation acceptance (A5)

### The protocol-level property

A cross-chain bridge's safety depends on the **freshness** of validator attestations. An attestation issued at time `t` reflects the validator set's state at that time. If the validator set rotates at time `t'` (because a validator was compromised, replaced, or its key rotated), attestations issued before `t'` should no longer be accepted — they reflect a stale view of the validator set.

The vulnerable bridge has no freshness window. An attacker who holds an old withdrawal attestation can execute it at any future time. Worse: even if the validator set has rotated due to a discovered compromise, the old attestation remains valid.

### Attack on `VulnerableBridge.sol`

```
Step 1: validators issue an attestation A at time t_0 for amount 100 → 0xOldAttacker
Step 2: attacker holds A indefinitely
Step 3: at any later time t_1 >> t_0, attacker submits A
Step 4: vulnerable bridge accepts; pays out
```

The simulator confirms this: replay with no time check succeeds.

### Mitigation

Two complementary patches:

1. **Freshness window**: reject attestations issued more than `FRESHNESS_WINDOW` (1 hour) ago.

   ```solidity
   require(block.timestamp <= issuedAt + FRESHNESS_WINDOW, "attestation stale");
   ```

2. **Epoch-binding hash**: the message hash incorporates `validatorEpoch`. When the validator set rotates, the epoch increments; old attestations bound to the previous epoch produce a different hash on replay and fail verification.

   ```solidity
   bytes32 messageHash = keccak256(abi.encode(recipient, amount, nonce, issuedAt, validatorEpoch));
   ```

Lean theorems `stale_attestation_rejected`, `future_attestation_rejected`, and `epoch_rotation_breaks_replay` formalize the properties.

### Patched simulator output

```
✓ Stale attestation rejected: attestation stale
```

---

## Obligation coverage on the patched bridge

| Obligation | Tool / source | Evidence | Depth |
|---|---|---|---|
| **A1** value conservation | (not the focus of this demo) | (not addressed at depth > 0) | D0 |
| **A2** authorization closure | `lean/Parallax5/Walkaway.lean` (bounded variant) | Walkaway-bounded theorem; no admin role exists but bridge depends on off-chain validator infrastructure | **D4** |
| **A3** signature integrity | `proof/Attestation.lean` | Theorem `patched_rejects_high_s` rejects malleable signatures | **D4** |
| **A4** temporal distinctness | Slither (reentrancy checks) | Static detection on safe ordering of state changes vs external calls | D2 |
| **A5** external-attestation trust | `proof/Attestation.lean` | Theorems `stale_attestation_rejected`, `future_attestation_rejected`, `epoch_rotation_breaks_replay` | **D4** |

CROPS vector: **`C=4 R=4 O=5 P=0 S=4`**

- **C=4** (max over A1, A4, A5; bounded by A5=4 from freshness proof)
- **R=4** (A2=4 dominates; walkaway_BOUNDED=4 matches — bridge depends on off-chain validator infrastructure)
- **O=5** (source openness explicitly declared)
- **P=0** (no privacy primitives — the bridge makes no privacy claim, and per CROPS v1.0.1 the matrix does not inflate P from A3 alone)
- **S=4** (max over A1..A5)

The R=4 (rather than R=5) honestly reflects the bridge's dependence on off-chain validator infrastructure. A bridge cannot achieve full walkaway by structure: the bridge's purpose is to relay attestations from external validators. If all validators disappear, no new withdrawals can be processed (liveness loss). This is a *bounded* walkaway, not full. The certificate is explicit about this in `walkaway.dependencies_disclosed`.

---

## What this demo proves about the substrate

1. **The same five obligations apply across protocol categories.** Demo 1 was an AMM/vault (A1 conservation primary). Demo 2 is a bridge (A3 + A5 primary). The substrate's vocabulary covers both with no extension required.

2. **Walkaway classification captures real protocol structure.** Not every protocol can be full walkaway; bridges by design depend on validator infrastructure. The bounded classification, with `dependencies_disclosed` enumerating the off-chain dependencies, gives consumers an honest picture without false binary "decentralized vs centralized" framing.

3. **A3 contributes to S in CROPS (and to P only when explicit privacy primitives are declared).** Signature integrity is a foundational security property. The CROPS contribution matrix was refined in v1.0.1 to require explicit privacy-primitive declarations as the sole source of P contributions: signature canonicalization on a non-private bridge does not inflate the bridge's privacy rating. This is the honest reporting the substrate prefers. A protocol using A3 evidence as part of a privacy-primitive design (ring signatures, blinded signatures, selective disclosure) declares `privacy_primitives_depth` accordingly.

4. **Formal proofs are the mechanism for D4 evidence.** Slither found 8 surface findings (mostly reentrancy/event ordering); none of them establishes A3 or A5 at the strength needed for a bridge. The Lean theorems in `proof/Attestation.lean` are what produce the D4 evidence that bridge users need.

---

## Files in this demo

```
demos/bridge/
├── REPORT.md                         (this file)
├── parallax.yaml                     PARALLAX-5 spec for the patched bridge
├── exploit.py                        Mechanical exploit simulator (4 scenarios)
├── contracts/
│   ├── VulnerableBridge.sol          Deliberately broken bridge attestation
│   └── PatchedBridge.sol             EIP-2 low-s + freshness + epoch-binding
├── proof/
│   └── Attestation.lean              Lean 4 A3 + A5 proofs (zero sorry)
└── output/
    └── certificate.json              Generated PARALLAX-5 certificate
```

---

## Running this demo

```bash
make demo-bridge
```

Executes:
1. `python3 demos/bridge/exploit.py` — confirms both attacks succeed on vulnerable, both rejected on patched
2. `slither demos/bridge/contracts/VulnerableBridge.sol` and `PatchedBridge.sol` — static-analysis findings
3. `parallax5 certify demos/bridge/parallax.yaml --output demos/bridge/output/certificate.json`
4. `parallax5 validate demos/bridge/output/certificate.json`
5. `parallax5 registry submit demos/bridge/output/certificate.json --dry-run`

---

## Citation

```bibtex
@misc{parallax5_demo_bridge,
  author    = {{AquaUrsa Research}},
  title  = {{PARALLAX-5 Demo 2: Bridge Attestation Integrity (A3 + A5)}},
  year   = {2026},
  publisher = {AquaUrsa Research},
  license = {CC0}
}
```

---

**End of report.** CC0. Fork it; improve it.
