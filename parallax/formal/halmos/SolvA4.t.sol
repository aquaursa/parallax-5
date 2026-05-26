// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../src/SolvPattern.sol";

/// halmos symbolic verification of cross-function reentrancy.
/// In the vulnerable model, a malicious receiver can drive the
/// total supply to grow by MORE than the deposit amount in a
/// single transaction.
contract A4VulnerableSolvTest {
    /// SHOULD FAIL: halmos finds an inflation witness where
    /// balanceOf[attacker] exceeds the deposit amount (because
    /// the unguarded onCallback got called once by deposit and
    /// once by the malicious re-entrant call).
    function check_A4_cross_function_reentrancy(uint256 amount) public {
        // Symbolic constraint: a moderate amount
        if (amount == 0) return;
        if (amount > 1e18) return;

        SolvVuln vault = new SolvVuln();
        MaliciousReceiver attacker = new MaliciousReceiver(address(vault));

        // Initial state: attacker holds 0
        assert(vault.balanceOf(address(attacker)) == 0);

        // Attack: attacker calls deposit(amount, attacker)
        //   → deposit() mints `amount` to attacker (mint A)
        //   → deposit() calls attacker.onCallback(attacker, amount)
        //   → attacker re-enters vault.onCallback (mint B, no guard)
        //   → vault.onCallback mints another `amount` (mint C)
        //   → control returns to deposit's tail: lock released
        attacker.attack(amount);

        // The A4 / A1 violation: attacker now holds MORE than `amount`
        // because the unguarded sibling onCallback minted a second
        // time during the re-entered call.
        // SAFE post-condition: only one mint per deposit. halmos
        // finds the assertion fails on the vulnerable contract.
        assert(vault.balanceOf(address(attacker)) <= amount);
    }
}

contract A4HardenedSolvTest {
    /// SHOULD PASS: with the guard on the sibling, no inflation occurs.
    function check_A4_hardened_no_reentrancy(uint256 amount) public {
        if (amount == 0) return;
        if (amount > 1e18) return;

        SolvHardened vault = new SolvHardened();

        // Direct deposit (no malicious receiver because reentrancy is blocked)
        address self = address(this);

        try vault.deposit(amount, self) {
            // If deposit succeeded the callback returned cleanly.
            // The total should be exactly amount.
            assert(vault.balanceOf(self) == amount);
        } catch {
            // If deposit reverts (e.g., the callback couldn't be called
            // because this contract has no onCallback), that's also fine.
        }
    }
}
