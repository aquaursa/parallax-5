// SPDX-License-Identifier: Apache-2.0
// PARALLAX-5 Demo 2: Patched bridge attestation
//
// Mitigations applied:
//   (A3)  Enforce low-s ECDSA (s ≤ secp256k1n/2). Rejects malleable signatures.
//   (A5)  Freshness window: messages expire after FRESHNESS_WINDOW seconds.
//   (A5)  Quorum-binding hash: the message hash binds the validator set epoch,
//         preventing replay against a rotated validator set.
//
// References:
//   - EIP-2 (low-s enforcement): https://eips.ethereum.org/EIPS/eip-2
//   - OpenZeppelin ECDSA library (defends against malleability)
//   - The 2022 Wormhole bridge exploit and the 2023 Nomad bridge exploit
//     both involved attestation-validation failures of this family.

pragma solidity ^0.8.20;

contract PatchedBridge {
    /// @notice Validator set with epoch tagging. When rotated, epoch increments;
    /// old attestations bound to the old epoch are no longer valid.
    mapping(address => bool) public isValidator;
    uint256 public validatorEpoch;
    uint256 public validatorCount;
    uint256 public requiredQuorum;

    mapping(bytes32 => bool) public processedMessages;
    uint256 public totalEscrow;

    /// @notice secp256k1 curve order divided by 2; the largest valid s value
    /// for canonical (low-s) signatures.
    /// secp256k1n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    /// secp256k1n/2 (in hex):
    bytes32 public constant SECP256K1N_DIV_2 =
        0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0;

    /// @notice Freshness window: attestations are only valid for this many seconds
    /// after issuance. The on-chain block.timestamp is the reference clock.
    uint256 public constant FRESHNESS_WINDOW = 1 hours;

    event Withdrawn(bytes32 indexed messageHash, address indexed recipient, uint256 amount);

    constructor(address[] memory _validators, uint256 _quorum) {
        require(_validators.length >= _quorum && _quorum > 0, "invalid quorum");
        for (uint256 i = 0; i < _validators.length; i++) {
            isValidator[_validators[i]] = true;
        }
        validatorCount = _validators.length;
        requiredQuorum = _quorum;
        validatorEpoch = 1;
    }

    function deposit() external payable {
        totalEscrow += msg.value;
    }

    /// @notice Compute the canonical message hash including the validator epoch
    /// and the issuance timestamp.
    /// @dev The hash binds: recipient, amount, nonce, issuedAt, validatorEpoch.
    /// Replaying with a different epoch produces a different hash, so a
    /// rotated validator set's signatures are not valid for old messages.
    function computeMessageHash(
        address recipient,
        uint256 amount,
        uint256 nonce,
        uint256 issuedAt,
        uint256 epoch
    ) public pure returns (bytes32) {
        return keccak256(abi.encode(recipient, amount, nonce, issuedAt, epoch));
    }

    /// @notice Withdraw with full validation.
    function withdraw(
        address recipient,
        uint256 amount,
        uint256 nonce,
        uint256 issuedAt,
        uint8[] memory v,
        bytes32[] memory r,
        bytes32[] memory s
    ) external {
        // PATCH (A5 freshness): require issuance recent
        require(block.timestamp <= issuedAt + FRESHNESS_WINDOW, "attestation stale");
        require(issuedAt <= block.timestamp, "attestation from the future");

        // Compute hash binding the current validator epoch
        bytes32 messageHash = computeMessageHash(recipient, amount, nonce, issuedAt, validatorEpoch);

        require(!processedMessages[messageHash], "already processed");
        require(v.length == r.length && r.length == s.length, "length mismatch");
        require(v.length >= requiredQuorum, "insufficient signatures");

        uint256 validCount = 0;
        address[] memory seen = new address[](v.length);

        for (uint256 i = 0; i < v.length; i++) {
            // PATCH (A3 malleability): enforce low-s
            require(uint256(s[i]) <= uint256(SECP256K1N_DIV_2), "high-s rejected");
            require(v[i] == 27 || v[i] == 28, "invalid v");

            address signer = ecrecover(messageHash, v[i], r[i], s[i]);
            require(signer != address(0), "invalid signature");
            require(isValidator[signer], "not a validator");

            for (uint256 j = 0; j < i; j++) {
                require(seen[j] != signer, "duplicate signer");
            }
            seen[i] = signer;
            validCount++;
        }

        require(validCount >= requiredQuorum, "quorum not met");

        processedMessages[messageHash] = true;
        totalEscrow -= amount;
        (bool ok, ) = recipient.call{value: amount}("");
        require(ok, "transfer failed");

        emit Withdrawn(messageHash, recipient, amount);
    }
}
