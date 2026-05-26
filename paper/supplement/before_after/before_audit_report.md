# Audit Report: ExampleVault.sol (Traditional Format)

**Auditor**: Trail of Bits  
**Engagement**: Q2 2026  
**Pages**: 47  
**Scope**: ExampleVault.sol, deposit/withdraw flows

## Executive Summary

ExampleVault.sol is an ERC-4626 vault with custom inflation protection. We audited the v2.0.0 release at commit `abc123...`. We found 1 high-severity, 2 medium-severity, and 4 low-severity issues. Critical fix recommendations have been implemented and verified.

## Findings

### TOB-VAULT-001 [High]: Share inflation via direct token transfer
Lines 142-156 of ExampleVault.sol allow an attacker who is the first depositor to deposit 1 wei, donate a large amount of underlying asset directly to the vault, and then redirect subsequent deposits' share allocations to zero. The classic Cream Finance pattern.

**Recommendation**: Add a MIN_LIQUIDITY constant and burn-to-DEAD-address pattern.

**Status**: Fixed in commit `def456...`

### TOB-VAULT-002 [Medium]: Reentrancy on withdrawal
The `withdraw` function on line 203 transfers underlying asset BEFORE updating the share balance. A malicious ERC-777 token could re-enter and withdraw twice.

**Recommendation**: Apply checks-effects-interactions pattern. Move state update before external call.

**Status**: Fixed in commit `ghi789...`

[...4 more findings, 30 more pages of narrative ...]

## Conclusion

We recommend the v2.0.0 release for production deployment subject to the above fixes being applied. Total audit cost: $87,500 over 4 weeks.
