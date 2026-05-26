// SPDX-License-Identifier: Apache-2.0
// PARALLAX-5 Demo 3: Runtime gate for AI-agent transaction safety
//
// The gate sits between the AI agent and the target vault. Every
// transaction the agent attempts is funneled through the gate, which
// checks the transaction against a registered StepSecure policy before
// permitting execution.
//
// This is the operational instance of "D5: runtime enforced" on the
// PARALLAX-5 proof depth scale. The gate's value is in what it
// CANNOT do: even if the agent's reasoning is wrong, even if the
// agent's key is compromised, even if the agent is jailbroken, the
// gate refuses transitions that violate the obligations.
//
// The StepSecure policy enforced here:
//   - Outflows above MAX_OUTFLOW_PERCENT of vault balance are rejected (A1)
//   - Approvals to unknown contracts are rejected (A2: only whitelisted spenders)
//   - Approvals for max uint (unlimited spend) are rejected (A1+A2)
//   - The policy itself is immutable post-deployment (the gate cannot be unlocked)

pragma solidity ^0.8.20;

import {IERC20} from "../../vault/contracts/IERC20.sol";

interface ITargetVault {
    function asset() external view returns (IERC20);
    function vaultBalance() external view returns (uint256);
    function agentApprove(address spender, uint256 amount) external;
    function agentTransfer(address to, uint256 amount) external;
}

contract RuntimeGate {
    ITargetVault public immutable vault;
    address public immutable agentKey;
    uint256 public immutable maxOutflowPercent;

    /// @notice Whitelist of contracts the agent may approve.
    /// Set at construction and immutable thereafter — the gate enforces
    /// "only whitelisted strategies" without an upgrade path.
    mapping(address => bool) public whitelistedSpenders;
    uint256 public whitelistedCount;

    /// @notice Maximum approval amount (in raw units). Setting this below
    /// type(uint256).max prevents "max approval" patterns that are a common
    /// attack vector.
    uint256 public constant MAX_APPROVAL = 10**26;  // 100 million tokens at 18 decimals

    /// @notice Rolling outflow accounting for rate-limiting (per-day budget).
    uint256 public dailyOutflow;
    uint256 public dailyOutflowResetTime;
    uint256 public constant DAILY_OUTFLOW_CAP_PERCENT = 20;  // 20% of vault per day
    uint256 public constant ONE_DAY = 86400;

    /// @notice Events for every gate decision (D5 evidence).
    event Permitted(string action, address target, uint256 amount, address agent);
    event Rejected(string action, address target, uint256 amount, string reason);

    modifier onlyAgent() {
        require(msg.sender == agentKey, "RuntimeGate: not the agent");
        _;
    }

    constructor(
        address _vault,
        address _agentKey,
        uint256 _maxOutflowPercent,
        address[] memory _initialWhitelist
    ) {
        require(_maxOutflowPercent > 0 && _maxOutflowPercent <= 50, "invalid outflow cap");
        vault = ITargetVault(_vault);
        agentKey = _agentKey;
        maxOutflowPercent = _maxOutflowPercent;
        for (uint256 i = 0; i < _initialWhitelist.length; i++) {
            whitelistedSpenders[_initialWhitelist[i]] = true;
        }
        whitelistedCount = _initialWhitelist.length;
        dailyOutflowResetTime = block.timestamp + ONE_DAY;
    }

    // ── StepSecure predicates ──────────────────────────────────────

    /// @notice The "single-transaction outflow" predicate.
    /// A transfer transition is StepSecure for amount A iff:
    ///   A <= vaultBalance * MAX_OUTFLOW_PERCENT / 100
    function _isStepSecureTransfer(uint256 amount) internal view returns (bool, string memory) {
        uint256 balance = vault.vaultBalance();
        uint256 cap = (balance * maxOutflowPercent) / 100;
        if (amount > cap) {
            return (false, "outflow exceeds single-transaction cap");
        }
        return (true, "");
    }

    /// @notice The "approve" predicate.
    /// An approval transition is StepSecure for (spender, amount) iff:
    ///   whitelistedSpenders[spender] AND amount <= MAX_APPROVAL
    function _isStepSecureApprove(address spender, uint256 amount) internal view returns (bool, string memory) {
        if (!whitelistedSpenders[spender]) {
            return (false, "spender not whitelisted");
        }
        if (amount > MAX_APPROVAL) {
            return (false, "approval exceeds MAX_APPROVAL");
        }
        return (true, "");
    }

    /// @notice The "daily outflow" predicate.
    function _isStepSecureDailyBudget(uint256 amount) internal view returns (bool, string memory) {
        uint256 balance = vault.vaultBalance();
        uint256 dailyCap = (balance * DAILY_OUTFLOW_CAP_PERCENT) / 100;
        uint256 projected = block.timestamp >= dailyOutflowResetTime
            ? amount
            : dailyOutflow + amount;
        if (projected > dailyCap) {
            return (false, "daily outflow budget exceeded");
        }
        return (true, "");
    }

    // ── Gate-permitted agent actions ───────────────────────────────

    /// @notice Gated transfer. The agent submits a candidate transfer;
    /// the gate checks predicates and either forwards or rejects.
    function transfer(address to, uint256 amount) external onlyAgent {
        (bool ok1, string memory r1) = _isStepSecureTransfer(amount);
        if (!ok1) {
            emit Rejected("transfer", to, amount, r1);
            revert(r1);
        }
        (bool ok2, string memory r2) = _isStepSecureDailyBudget(amount);
        if (!ok2) {
            emit Rejected("transfer", to, amount, r2);
            revert(r2);
        }
        // Update daily outflow tracking
        if (block.timestamp >= dailyOutflowResetTime) {
            dailyOutflow = amount;
            dailyOutflowResetTime = block.timestamp + ONE_DAY;
        } else {
            dailyOutflow += amount;
        }
        emit Permitted("transfer", to, amount, msg.sender);
        vault.agentTransfer(to, amount);
    }

    /// @notice Gated approve. Same pattern.
    function approve(address spender, uint256 amount) external onlyAgent {
        (bool ok, string memory r) = _isStepSecureApprove(spender, amount);
        if (!ok) {
            emit Rejected("approve", spender, amount, r);
            revert(r);
        }
        emit Permitted("approve", spender, amount, msg.sender);
        vault.agentApprove(spender, amount);
    }
}
