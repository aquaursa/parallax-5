// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title VulnerableLending - intentionally insecure contract for PARALLAX-5 coordinator testing
/// @notice This contract embeds violations of A1, A2, A4, A5 to exercise the coordinator
contract VulnerableLending {
    mapping(address => uint256) public balances;
    address public admin;
    address public priceOracle;
    uint256 public lastPrice;
    uint256 public totalSupply;

    constructor(address _oracle) {
        // A2 violation: admin set in constructor but no role-revocation mechanism
        admin = msg.sender;
        priceOracle = _oracle;
    }

    /// A4 violation: classical reentrancy via external call before state update
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        balances[msg.sender] -= amount;
        totalSupply -= amount;
    }

    /// A2 violation: unprotected initialize-like function
    function initialize(address newAdmin) external {
        admin = newAdmin;
    }

    /// A2 violation: tx.origin-based authorization
    function emergencyKill() external {
        require(tx.origin == admin, "Not admin");
        selfdestruct(payable(msg.sender));
    }

    /// A1 violation: balance increment without corresponding totalSupply increment
    /// Conservation violated; can over-credit
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        // BUG: totalSupply not updated, conservation violated
    }

    /// A5 violation: no staleness check on price oracle
    function getPrice() public view returns (uint256) {
        // BUG: no check that lastPrice was recently updated
        return lastPrice;
    }

    /// A5 violation: single-source oracle write with no validation
    function updatePrice(uint256 newPrice) external {
        require(msg.sender == priceOracle, "Not oracle");
        lastPrice = newPrice;
    }

    // Standard receive function
    receive() external payable {
        balances[msg.sender] += msg.value;
    }
}
