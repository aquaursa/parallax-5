// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract OracleVuln {
    uint256 public price;
    uint256 public updatedAt;
    mapping(address => uint256) public collateral;
    bool public liquidated;

    function setOracle(uint256 p, uint256 t) external {
        price = p;
        updatedAt = t;
    }
    function setCollateral(address u, uint256 c) external { collateral[u] = c; }

    function liquidate(address user, uint256 threshold) external returns (bool) {
        // VULN: no freshness check on updatedAt
        if (collateral[user] * price < threshold) {
            liquidated = true;
            collateral[user] = 0;
            return true;
        }
        return false;
    }
}

contract OracleHardened {
    uint256 public price;
    uint256 public updatedAt;
    uint256 public constant MAX_AGE = 1800;
    mapping(address => uint256) public collateral;
    bool public liquidated;

    function setOracle(uint256 p, uint256 t) external {
        price = p;
        updatedAt = t;
    }
    function setCollateral(address u, uint256 c) external { collateral[u] = c; }

    function liquidate(address user, uint256 threshold, uint256 nowTime) external returns (bool) {
        require(nowTime <= updatedAt + MAX_AGE, "stale oracle");
        if (collateral[user] * price < threshold) {
            liquidated = true;
            collateral[user] = 0;
            return true;
        }
        return false;
    }
}
