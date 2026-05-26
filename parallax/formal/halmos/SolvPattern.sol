// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IReceiver {
    function onCallback(address from, uint256 amount) external returns (bool);
}

/// Solv-class double-mint pattern. The mint() function uses a
/// ReentrancyGuard. BUT the sibling callback function onERC721Received
/// also mints, and it lacks the guard. This is cross-function
/// reentrancy that PER-FUNCTION static analysis (ObligationSol v0) misses.
contract SolvVuln {
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    bool private _locked;

    modifier nonReentrant() {
        require(!_locked, "REENTRANT");
        _locked = true;
        _;
        _locked = false;
    }

    /// The "deposit" function: takes a token, mints shares, AND
    /// fires a callback. The callback runs OUTSIDE the guard
    /// because it's invoked on the receiver, not the deposit fn.
    function deposit(uint256 amount, address receiver) external nonReentrant {
        // Mint A
        totalSupply += amount;
        balanceOf[msg.sender] += amount;
        // Now fire callback on receiver (typical safe-transfer pattern)
        IReceiver(receiver).onCallback(msg.sender, amount);
    }

    /// The vulnerable callback: lacks `nonReentrant`. It mints again
    /// for the same caller. This is the bug.
    function onCallback(address from, uint256 amount) external returns (bool) {
        // Mint B  ← extra mint, no guard
        totalSupply += amount;
        balanceOf[from] += amount;
        return true;
    }
}

/// A malicious receiver that re-enters `deposit` via the callback.
contract MaliciousReceiver is IReceiver {
    SolvVuln public vault;
    bool public attacked;
    constructor(address v) { vault = SolvVuln(v); }

    function attack(uint256 amount) external {
        vault.deposit(amount, address(this));
    }

    function onCallback(address, uint256 amount) external returns (bool) {
        if (!attacked) {
            attacked = true;
            // Re-enter via the unguarded sibling — mint to OURSELVES
            // even though deposit's lock is held.
            vault.onCallback(address(this), amount);
        }
        return true;
    }
}

/// Hardened: callback has the same guard, so cross-function
/// re-entry is blocked.
contract SolvHardened {
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    bool private _locked;

    modifier nonReentrant() {
        require(!_locked, "REENTRANT");
        _locked = true;
        _;
        _locked = false;
    }

    function deposit(uint256 amount, address receiver) external nonReentrant {
        totalSupply += amount;
        balanceOf[msg.sender] += amount;
        IReceiver(receiver).onCallback(msg.sender, amount);
    }

    /// CRUCIAL: the sibling callback ALSO carries the guard. This
    /// is the contract-level (not function-level) reentrancy fix.
    function onCallback(address from, uint256 amount) external nonReentrant returns (bool) {
        totalSupply += amount;
        balanceOf[from] += amount;
        return true;
    }
}
