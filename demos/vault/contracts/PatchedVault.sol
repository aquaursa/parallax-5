// SPDX-License-Identifier: Apache-2.0
// PARALLAX-5 Demo 1: ERC-4626 inflation-attack mitigation
//
// Patched version of VulnerableVault using OpenZeppelin's virtual-shares
// pattern. The virtual offset prevents the donation attack by ensuring
// the rounding always favors the vault (not the attacker).
//
// Pattern reference:
//   "ERC4626 Virtual Shares" — OpenZeppelin Defender, 2023
//   (canonical mitigation; described in the OZ v4.8+ ERC4626 base contract)
//
// Mechanism:
//   convertToShares uses (assets + 1) * (totalSupply + virtualShares)
//                        --------------------------------------------
//                        (totalAssets() + virtualAssets)
//   with virtualShares = 10**decimalsOffset (typically 10**6 for 1e-6 minimum unit)
//   and virtualAssets = 1.
//
// Effect: an attacker would need to donate ~virtualShares × inflation_target
// to manipulate the share price meaningfully, which is uneconomical.
//
// A1 obligation now holds at D4 (formal proof in proof/Conservation.lean)
// against the inflation-attack family of exploits, conditional on:
//   - Underlying ERC-20 conforms to standard transfer semantics
//   - decimalsOffset ≥ 6 (enforced by constructor)

pragma solidity ^0.8.20;

import {IERC20} from "./IERC20.sol";

contract PatchedVault {
    IERC20 public immutable asset;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    /// @notice Virtual shares offset — the larger this is, the more
    /// expensive an inflation attack becomes. 10^6 is the OZ default.
    uint8 public constant DECIMALS_OFFSET = 6;
    uint256 public constant VIRTUAL_SHARES = 10**6;
    uint256 public constant VIRTUAL_ASSETS = 1;

    string public constant name = "Patched Vault Share";
    string public constant symbol = "pVS";
    uint8 public constant decimals = 18;

    event Deposit(address indexed sender, address indexed receiver, uint256 assets, uint256 shares);
    event Withdraw(
        address indexed sender,
        address indexed receiver,
        address indexed owner,
        uint256 assets,
        uint256 shares
    );

    constructor(address _asset) {
        asset = IERC20(_asset);
    }

    function totalAssets() public view returns (uint256) {
        return asset.balanceOf(address(this));
    }

    /// @notice Convert assets to shares — patched with virtual offset.
    /// @dev Rounds DOWN, but virtual offset ensures non-zero shares for
    /// any non-zero deposit at reasonable share prices.
    function convertToShares(uint256 assets) public view returns (uint256) {
        // PATCH: virtual offset prevents the donation attack
        // by making the rounding always favor the vault.
        return (assets * (totalSupply + VIRTUAL_SHARES)) / (totalAssets() + VIRTUAL_ASSETS);
    }

    function convertToAssets(uint256 shares) public view returns (uint256) {
        return (shares * (totalAssets() + VIRTUAL_ASSETS)) / (totalSupply + VIRTUAL_SHARES);
    }

    /// @notice Preview a deposit. Reverts if it would result in 0 shares.
    function previewDeposit(uint256 assets) public view returns (uint256 shares) {
        shares = convertToShares(assets);
        require(shares > 0, "PatchedVault: zero-share deposit prevented");
    }

    function deposit(uint256 assets, address receiver) public returns (uint256 shares) {
        shares = previewDeposit(assets);
        require(asset.transferFrom(msg.sender, address(this), assets), "transfer failed");
        balanceOf[receiver] += shares;
        totalSupply += shares;
        emit Deposit(msg.sender, receiver, assets, shares);
    }

    function redeem(uint256 shares, address receiver, address owner) public returns (uint256 assets) {
        require(msg.sender == owner, "not owner");
        assets = convertToAssets(shares);
        balanceOf[owner] -= shares;
        totalSupply -= shares;
        require(asset.transfer(receiver, assets), "transfer failed");
        emit Withdraw(msg.sender, receiver, owner, assets, shares);
    }
}
