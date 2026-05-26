// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../src/Oracle.sol";

contract A5VulnerableTest {
    /// SHOULD FAIL: halmos finds a stale-oracle witness that causes liquidation.
    function check_A5_stale_oracle_drives_liquidation(
        uint256 stalePrice, uint256 staleTime, uint256 collateralAmt,
        uint256 threshold
    ) public {
        OracleVuln o = new OracleVuln();
        address user = address(0xC);
        o.setOracle(stalePrice, staleTime);
        o.setCollateral(user, collateralAmt);
        // halmos searches for input combos
        o.liquidate(user, threshold);
        // A5 assertion: liquidation should NOT happen if oracle is stale.
        // We assert it doesn't happen unconditionally → halmos finds it does.
        assert(!o.liquidated());
    }
}

contract A5HardenedTest {
    /// SHOULD PASS: with a freshness gate, no stale oracle causes liquidation.
    function check_A5_freshness_gate_blocks_stale(
        uint256 oraclePrice, uint256 oracleTime, uint256 nowTime,
        uint256 collateralAmt, uint256 threshold
    ) public {
        OracleHardened o = new OracleHardened();
        address user = address(0xC);
        o.setOracle(oraclePrice, oracleTime);
        o.setCollateral(user, collateralAmt);

        try o.liquidate(user, threshold, nowTime) {
            // If liquidate didn't revert, freshness gate passed:
            //   nowTime <= oracleTime + 1800
            assert(nowTime <= oracleTime + 1800);
        } catch {
            // Revert is fine — stale oracle correctly rejected.
        }
    }
}
