// SPDX-License-Identifier: Apache-2.0
// PARALLAX-5 Demo 2: Vulnerable bridge attestation
//
// This contract is DELIBERATELY VULNERABLE to two related attack
// families on cross-chain bridge attestation:
//
//   1. Signature malleability via high-s ECDSA signatures (A3 violation)
//      Pre-EIP-2 ECDSA allows two valid signatures for each message
//      (r, s) and (r, n-s). An attacker can re-broadcast the malleable
//      copy under a different message hash, replay-attacking a one-time
//      withdrawal.
//
//   2. No freshness window (A5 violation)
//      Bridge attestations are valid forever. An attacker can hold a
//      stolen attestation and execute it any time, even after the
//      validator set has rotated.
//
// Pedagogical only. DO NOT DEPLOY.

pragma solidity ^0.8.20;

contract VulnerableBridge {
    /// @notice The set of validators authorized to attest withdrawals.
    /// Each validator's address is registered once at construction.
    mapping(address => bool) public isValidator;
    uint256 public validatorCount;
    uint256 public requiredQuorum;  // minimum number of valid signatures

    /// @notice Tracks which messages have been processed.
    mapping(bytes32 => bool) public processedMessages;

    /// @notice Total amount escrowed in the bridge.
    uint256 public totalEscrow;

    event Withdrawn(bytes32 indexed messageHash, address indexed recipient, uint256 amount);

    constructor(address[] memory _validators, uint256 _quorum) {
        require(_validators.length >= _quorum && _quorum > 0, "invalid quorum");
        for (uint256 i = 0; i < _validators.length; i++) {
            isValidator[_validators[i]] = true;
        }
        validatorCount = _validators.length;
        requiredQuorum = _quorum;
    }

    /// @notice Deposit native value into the bridge for later withdrawal on the destination chain.
    function deposit() external payable {
        totalEscrow += msg.value;
    }

    /// @notice Withdraw bridged funds. Caller submits the message hash and the validator signatures.
    /// VULNERABILITIES:
    ///   (A3)  Signature malleability: no enforcement of low-s. An attacker can replay with (r, n-s).
    ///   (A5)  No freshness window: stale attestations remain valid indefinitely.
    ///   (A5)  No quorum-binding: messageHash does not include the validator set version.
    function withdraw(
        bytes32 messageHash,
        address recipient,
        uint256 amount,
        uint8[] memory v,
        bytes32[] memory r,
        bytes32[] memory s
    ) external {
        require(!processedMessages[messageHash], "already processed");
        require(v.length == r.length && r.length == s.length, "length mismatch");
        require(v.length >= requiredQuorum, "insufficient signatures");

        uint256 validCount = 0;
        // Track seen signers to prevent the same validator signing twice
        // (This is correctly implemented; the bug is NOT here)
        address[] memory seen = new address[](v.length);

        for (uint256 i = 0; i < v.length; i++) {
            // VULNERABILITY: no check that s ≤ secp256k1n/2 (high-s allowed)
            address signer = ecrecover(messageHash, v[i], r[i], s[i]);
            require(signer != address(0), "invalid signature");
            require(isValidator[signer], "not a validator");

            // Check for duplicates
            for (uint256 j = 0; j < i; j++) {
                require(seen[j] != signer, "duplicate signer");
            }
            seen[i] = signer;
            validCount++;
        }

        require(validCount >= requiredQuorum, "quorum not met");

        // Mark processed and pay out
        processedMessages[messageHash] = true;
        totalEscrow -= amount;
        (bool ok, ) = recipient.call{value: amount}("");
        require(ok, "transfer failed");

        emit Withdrawn(messageHash, recipient, amount);
    }
}
