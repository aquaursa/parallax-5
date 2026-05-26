// SPDX-License-Identifier: Apache-2.0
// PARALLAX-5 Demo 3: target vault for the AI-agent runtime-gate demo.
//
// This is the contract the AI agent is given authority over. The vault
// holds user funds; the agent's job is to manage them (e.g., yield-
// farming, rebalancing). The agent has a key that can submit
// transactions to this contract.
//
// Without a runtime gate, the agent's key is a unilateral admin: it
// can do anything its function selectors permit. With a PARALLAX-5
// runtime gate sitting in front of every agent action, only StepSecure
// transitions reach the vault.

pragma solidity ^0.8.20;

import {IERC20} from "../../vault/contracts/IERC20.sol";

contract TargetVault {
    IERC20 public immutable asset;
    address public immutable owner;          // the human user
    address public immutable agentManager;   // the address authorized to manage

    mapping(address => uint256) public deposits;
    uint256 public totalDeposits;

    /// @notice Maximum single-transaction outflow as a percentage of total.
    /// Hardcoded for the demo; in production this would be a parameter.
    uint256 public constant MAX_OUTFLOW_PERCENT = 5;  // 5%

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event Approved(address indexed spender, uint256 amount);
    event Transferred(address indexed to, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "TargetVault: not owner");
        _;
    }

    modifier onlyAgent() {
        require(msg.sender == agentManager, "TargetVault: not agent");
        _;
    }

    constructor(address _asset, address _owner, address _agentManager) {
        asset = IERC20(_asset);
        owner = _owner;
        agentManager = _agentManager;
    }

    /// @notice User deposit. Only the owner (user) calls this.
    function deposit(uint256 amount) external onlyOwner {
        require(asset.transferFrom(msg.sender, address(this), amount), "transfer failed");
        deposits[msg.sender] += amount;
        totalDeposits += amount;
        emit Deposited(msg.sender, amount);
    }

    /// @notice User withdrawal. Only the owner (user) calls this.
    function withdraw(uint256 amount) external onlyOwner {
        require(deposits[msg.sender] >= amount, "insufficient balance");
        deposits[msg.sender] -= amount;
        totalDeposits -= amount;
        require(asset.transfer(msg.sender, amount), "transfer failed");
        emit Withdrawn(msg.sender, amount);
    }

    /// @notice Agent function: approve a spender (e.g., a yield strategy).
    /// Without a runtime gate, the agent could approve any spender for any
    /// amount — including a malicious contract for max uint.
    function agentApprove(address spender, uint256 amount) external onlyAgent {
        require(asset.approve(spender, amount), "approve failed");
        emit Approved(spender, amount);
    }

    /// @notice Agent function: transfer to a strategy contract.
    /// Without a runtime gate, the agent could transfer any amount to any
    /// destination — including draining the vault to its own address.
    function agentTransfer(address to, uint256 amount) external onlyAgent {
        require(asset.transfer(to, amount), "transfer failed");
        emit Transferred(to, amount);
    }

    function vaultBalance() external view returns (uint256) {
        return asset.balanceOf(address(this));
    }
}
