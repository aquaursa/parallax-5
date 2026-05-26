// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// CRUCIBLE-hardened vault with MIN_LIQUIDITY burn (CRUCIBLE A1+ pattern).
contract CreamHardened {
    uint256 public totalShares;
    uint256 public totalAssets;
    uint256 public constant MIN_LIQUIDITY = 1000;
    mapping(address => uint256) public balanceOf;
    
    function deposit(uint256 assets) external returns (uint256 shares) {
        if (totalShares == 0) {
            require(assets > MIN_LIQUIDITY * MIN_LIQUIDITY, "insufficient initial");
            shares = assets - MIN_LIQUIDITY;
            balanceOf[address(0)] = MIN_LIQUIDITY;
            totalShares = shares + MIN_LIQUIDITY;
        } else {
            shares = assets * totalShares / totalAssets;
            require(shares > 0, "deposit too small");
            totalShares += shares;
        }
        balanceOf[msg.sender] += shares;
        totalAssets += assets;
    }
}
