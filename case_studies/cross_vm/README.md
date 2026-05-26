# Cross-VM PARALLAX-5

PARALLAX-5's obligations are stated over an abstract value-bearing state machine, so they apply to any VM with value transitions. This case study works the obligations on **Move** (Sui/Aptos) and **Solana SBPF**.

## A1 (Value Conservation) — Move

```move
module pkg::vault {
    use sui::balance::{Self, Balance};
    use sui::coin::{Self, Coin};
    use sui::transfer;
    use sui::tx_context::TxContext;

    struct Vault<phantom T> has key {
        id: UID,
        total_assets: Balance<T>,
        total_shares: u64,
    }

    /// A1 (Value Conservation): minted shares must be proportional
    /// to the assets backing them. The Move type system + Balance
    /// resource make A1 partially structural (Balance cannot be
    /// duplicated or destroyed except via burn). Still need to
    /// enforce the proportionality.
    public fun deposit<T>(vault: &mut Vault<T>, c: Coin<T>): u64 {
        let amount = coin::value(&c);
        assert!(amount > 0, 0);  // PARALLAX-A1: zero deposit
        let new_shares = if (vault.total_shares == 0) {
            assert!(amount >= 1000, 1);  // PARALLAX-A1: MIN_LIQUIDITY
            amount
        } else {
            let assets_pre = balance::value(&vault.total_assets);
            let shares = (amount * vault.total_shares) / assets_pre;
            assert!(shares > 0, 2);  // PARALLAX-A1: zero shares
            shares
        };
        balance::join(&mut vault.total_assets, coin::into_balance(c));
        vault.total_shares = vault.total_shares + new_shares;
        new_shares
    }
}
```

**Verification**: Sui's `prover` (formerly Move Prover) discharges A1 with the same kind of inductive invariant used in Solidity. Output certificate is P3 (symbolically checked) with `proof_artifacts.A1.tool = "MoveProver"`.

## A2 (Authorization Closure) — Solana SBPF (Anchor)

```rust
use anchor_lang::prelude::*;

#[program]
pub mod treasury {
    use super::*;

    /// A2 (Authorization Closure): only the recorded admin can call.
    /// Anchor's `has_one` constraint enforces structurally. In raw SBPF,
    /// the equivalent is a manual signer check on the first AccountInfo.
    pub fn set_oracle(ctx: Context<SetOracle>, new_oracle: Pubkey) -> Result<()> {
        // Anchor verifies that ctx.accounts.admin.key() == ctx.accounts.treasury.admin
        // via the `has_one` attribute below
        ctx.accounts.treasury.oracle = new_oracle;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct SetOracle<'info> {
    #[account(mut, has_one = admin)]   // A2: enforced by Anchor at deserialization
    pub treasury: Account<'info, Treasury>,
    pub admin: Signer<'info>,           // A2: must be a signer
}
```

**Verification**: A combination of Anchor's compile-time constraints (`has_one`, `Signer<'info>`) and `solana-program-test` integration tests. For P3, use `solana-fuzz` symbolic-execution harness; P4 requires Coq formalization of the SBPF subset (no production tool yet, marked as a known limitation in this case study).

## A5 (External-Attestation Trust) — Wormhole / LayerZero

The cross-chain bridge case is independent of VM. A5 obligations on:

- Quorum: $q$-of-$n$ verifier set, $q \geq 2$, $n \geq 3$
- Diversity: verifiers run on distinct cloud providers, jurisdictions
- Freshness: message must be acted on within $\tau$ seconds of attestation
- Domain binding: signed hash includes chain ID, contract address, message nonce
- Replay protection: per-message nullifier

Wormhole and LayerZero each have these as configurable parameters. A PARALLAX-5 P3 certificate for a bridge contract attaches the configuration as `proof_artifacts.A5.configuration` and references the deployed verifier addresses.

## What this case study demonstrates

PARALLAX-5 is **VM-agnostic** in design. The Lean formalization quantifies over abstract states, transitions, and predicates; the concrete instantiation differs by VM but the obligation structure does not. A protocol team deploying on Move + Solana + EVM can issue:

- One PARALLAX-5 certificate per chain (covering chain-specific deployment).
- A meta-certificate covering the protocol's value-bearing logic at the model level.

This is the same pattern as Common Criteria's evaluation across implementations of the same Security Target.
