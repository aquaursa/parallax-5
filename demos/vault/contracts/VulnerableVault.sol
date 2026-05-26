// SPDX-License-Identifier: Apache-2.0
// PARALLAX-5 Demo 1: ERC-4626 inflation-attack target
//
// This contract is DELIBERATELY VULNERABLE to a well-known inflation
// attack on ERC-4626 vaults. It exists as a worked example for the
// PARALLAX-5 substrate's A1 (value conservation) obligation.
//
// DO NOT DEPLOY. This is for pedagogical use only.
//
// Vulnerability class:  share-price-manipulation via direct asset donation
// Violated obligation:  A1 (value conservation)
// Expected depth (per TOOL-MAPPING/aquaursa-v1):
//   Static (Slither):   D2 — reentrancy-related findings; not the inflation
//                       attack directly (Slither does not detect it)
//   Symbolic:           D3 — halmos can find share-rounding violations
//                       given the right invariant
//   Formal proof:       D4 — Lean proof shows the unpatched version
//                       admits a no-deposit→capture path
//
// The attack proceeds in 4 steps:
//   1. Attacker calls deposit(1) → mints 1 share, vault holds 1 asset
//   2. Attacker transfers 1e18 assets directly to vault (donation; bypasses deposit)
//   3. Vault state: totalAssets = 1e18 + 1, totalSupply = 1
//      Share price is now ~1e18 assets per share
//   4. Victim calls deposit(1e18 - 1) → previewDeposit rounds down to 0 shares
//      Victim's assets are absorbed into vault but no shares minted
//   5. Attacker calls redeem(1) → gets all of vault's assets
//
// The patched version (PatchedVault.sol) prevents this via virtual shares
// (OpenZeppelin's pattern), making the rounding always favor the vault.

pragma solidity ^0.8.20;

import {IERC20} from "./IERC20.sol";

/// @title VulnerableVault — deliberately broken ERC-4626 for the PARALLAX-5 vault demo.
contract VulnerableVault {
    IERC20 public immutable asset;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    string public constant name = "Vulnerable Vault Share";
    string public constant symbol = "vVS";
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

    /// @notice Convert assets to shares — DELIBERATELY VULNERABLE
    /// @dev Rounds DOWN; allows zero-share deposits when share price is inflated
    function convertToShares(uint256 assets) public view returns (uint256) {
        if (totalSupply == 0) {
            return assets;
        }
        // Vulnerability: pure ratio with no offset, allows manipulation
        return (assets * totalSupply) / totalAssets();
    }

    function convertToAssets(uint256 shares) public view returns (uint256) {
        if (totalSupply == 0) {
            return shares;
        }
        return (shares * totalAssets()) / totalSupply;
    }

    function deposit(uint256 assets, address receiver) public returns (uint256 shares) {
        shares = convertToShares(assets);
        // VULNERABILITY: no check that shares > 0
        // A1 violation: the depositor adds `assets` to the vault but
        // receives 0 shares; their value is captured by existing share holders.
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
