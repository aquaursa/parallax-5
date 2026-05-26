// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// The Cream first-depositor vulnerability, in minimal isolated form.
/// axioms-check's  A1+ obligation: shares must track assets monotonically.
contract CreamVuln {
    uint256 public totalShares;
    uint256 public totalAssets;
    mapping(address => uint256) public balanceOf;
    
    function deposit(uint256 assets) external returns (uint256 shares) {
        if (totalShares == 0) {
            shares = assets;
        } else {
            shares = assets * totalShares / totalAssets;
        }
        balanceOf[msg.sender] += shares;
        totalShares += shares;
        totalAssets += assets;
    }
    
    // Simulate the "donation" channel that breaks A1
    function donate(uint256 amount) external {
        totalAssets += amount;
    }
}
