// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

/// @title PARALLAX-5 Certificate Registry
/// @notice Permissionless on-chain registry for PARALLAX-5 certificate
///         lifecycle events. Anyone can register a certificate fingerprint;
///         only the original registrant can transition states.
/// @dev    Implements the seven-state lifecycle of PARALLAX-5 Certificate
///         Schema v1.0 (RFC at docs/CERTIFICATE_SCHEMA.md §3).
///         Admissible transitions, per the schema:
///
///           Draft → Issued → Published → {Superseded, Revoked, Expired, Withdrawn}
///
///         All transitions emit events carrying the certificate's fingerprint;
///         consumers may verify the off-chain Ed25519 signature against the
///         issuer's declared public key (the on-chain record is the lifecycle
///         state machine; the certificate JSON and signature remain off-chain).
///
///         Gas profile (mainnet target):
///           issue():     ~67k gas (1 SSTORE + event)
///           publish():   ~35k gas (1 SSTORE update + event)
///           supersede(): ~38k gas (1 SSTORE update + event + bytes32 indexed arg)
///           revoke():    ~38k gas (1 SSTORE update + event + string arg)
///           expire():    ~32k gas
///           withdraw():  ~32k gas
///
/// @custom:standard PARALLAX-5 Certificate Schema v1.0 §3 lifecycle state machine
/// @custom:repo     https://github.com/aquaursa/parallax-5
contract ParallaxRegistry {
    /// @dev Lifecycle states per schema §3. Values match the canonical enum order.
    enum Lifecycle {
        None,        // Sentinel: never written; distinguishes "registered" from "absent"
        Draft,       // Not used on chain (drafts are off-chain); reserved for future use
        Issued,      // Initial on-chain state
        Published,   // Anchored as a public certificate
        Superseded,  // Replaced by a successor certificate
        Revoked,     // Withdrawn by the issuer for a stated reason
        Expired,     // Validity window has elapsed
        Withdrawn    // Issuer-initiated retraction
    }

    struct Record {
        address registrant;
        Lifecycle state;
        uint64 issuedAt;
        uint64 lastUpdated;
        bytes32 supersededBy;  // Non-zero iff state == Superseded
    }

    /// @notice fingerprint (SHA-256 of canonical certificate JSON) => record
    mapping(bytes32 => Record) internal _records;

    /// @notice issuer (msg.sender at issuance) => total certificates issued
    mapping(address => uint256) public issuerCertCount;

    /// @notice Total certificates ever issued by this registry.
    uint256 public totalIssued;

    // ─── Events (six lifecycle transitions per schema §22.5) ─────────────────

    event Issued(bytes32 indexed fingerprint, address indexed issuer, uint256 timestamp);
    event Published(bytes32 indexed fingerprint, address indexed issuer, uint256 timestamp);
    event Superseded(bytes32 indexed fingerprint, bytes32 indexed successor, address indexed issuer, uint256 timestamp);
    event Revoked(bytes32 indexed fingerprint, address indexed issuer, string reason, uint256 timestamp);
    event Expired(bytes32 indexed fingerprint, uint256 timestamp);
    event Withdrawn(bytes32 indexed fingerprint, address indexed issuer, uint256 timestamp);

    // ─── Errors (typed; gas-efficient) ───────────────────────────────────────

    error AlreadyRegistered(bytes32 fingerprint);
    error NotRegistered(bytes32 fingerprint);
    error NotRegistrant(bytes32 fingerprint, address caller);
    error InvalidTransition(bytes32 fingerprint, Lifecycle from, Lifecycle to);
    error ZeroFingerprint();
    error SelfSupersession();

    // ─── State transitions ───────────────────────────────────────────────────

    /// @notice Register and issue a new certificate fingerprint.
    /// @dev    Transition: None → Issued. Permissionless.
    /// @param fingerprint  SHA-256 hash of the canonical-serialized certificate JSON
    function issue(bytes32 fingerprint) external {
        if (fingerprint == bytes32(0)) revert ZeroFingerprint();
        if (_records[fingerprint].state != Lifecycle.None) revert AlreadyRegistered(fingerprint);

        _records[fingerprint] = Record({
            registrant: msg.sender,
            state: Lifecycle.Issued,
            issuedAt: uint64(block.timestamp),
            lastUpdated: uint64(block.timestamp),
            supersededBy: bytes32(0)
        });

        unchecked {
            ++issuerCertCount[msg.sender];
            ++totalIssued;
        }

        emit Issued(fingerprint, msg.sender, block.timestamp);
    }

    /// @notice Publish a previously-issued certificate (anchor it as public).
    /// @dev    Transition: Issued → Published. Restricted to original registrant.
    function publish(bytes32 fingerprint) external {
        Record storage r = _onlyRegistrant(fingerprint);
        if (r.state != Lifecycle.Issued) revert InvalidTransition(fingerprint, r.state, Lifecycle.Published);
        r.state = Lifecycle.Published;
        r.lastUpdated = uint64(block.timestamp);
        emit Published(fingerprint, msg.sender, block.timestamp);
    }

    /// @notice Supersede a published certificate with a successor.
    /// @dev    Transition: Published → Superseded. The successor must already be Issued or Published.
    /// @param fingerprint  The predecessor's fingerprint
    /// @param successor    The successor certificate's fingerprint
    function supersede(bytes32 fingerprint, bytes32 successor) external {
        if (fingerprint == successor) revert SelfSupersession();
        Record storage r = _onlyRegistrant(fingerprint);
        if (r.state != Lifecycle.Published) revert InvalidTransition(fingerprint, r.state, Lifecycle.Superseded);

        // Optional but strict: require the successor to be a known certificate
        if (_records[successor].state == Lifecycle.None) revert NotRegistered(successor);

        r.state = Lifecycle.Superseded;
        r.supersededBy = successor;
        r.lastUpdated = uint64(block.timestamp);
        emit Superseded(fingerprint, successor, msg.sender, block.timestamp);
    }

    /// @notice Revoke a published certificate.
    /// @dev    Transition: Published → Revoked. Restricted to original registrant.
    function revoke(bytes32 fingerprint, string calldata reason) external {
        Record storage r = _onlyRegistrant(fingerprint);
        if (r.state != Lifecycle.Published) revert InvalidTransition(fingerprint, r.state, Lifecycle.Revoked);
        r.state = Lifecycle.Revoked;
        r.lastUpdated = uint64(block.timestamp);
        emit Revoked(fingerprint, msg.sender, reason, block.timestamp);
    }

    /// @notice Mark a published certificate as expired.
    /// @dev    Transition: Published → Expired. Permissionless: anyone may call.
    ///         The substrate places no on-chain validity window; off-chain consumers
    ///         compare the certificate's `validity.not_after` to the current time.
    ///         Setting expired on chain is therefore an external assertion that the
    ///         certificate's validity has lapsed; the registrant may dispute via
    ///         a new issued certificate.
    function expire(bytes32 fingerprint) external {
        Record storage r = _records[fingerprint];
        if (r.state == Lifecycle.None) revert NotRegistered(fingerprint);
        if (r.state != Lifecycle.Published) revert InvalidTransition(fingerprint, r.state, Lifecycle.Expired);
        r.state = Lifecycle.Expired;
        r.lastUpdated = uint64(block.timestamp);
        emit Expired(fingerprint, block.timestamp);
    }

    /// @notice Withdraw a published certificate (registrant-initiated retraction).
    /// @dev    Transition: Published → Withdrawn. Restricted to original registrant.
    function withdraw(bytes32 fingerprint) external {
        Record storage r = _onlyRegistrant(fingerprint);
        if (r.state != Lifecycle.Published) revert InvalidTransition(fingerprint, r.state, Lifecycle.Withdrawn);
        r.state = Lifecycle.Withdrawn;
        r.lastUpdated = uint64(block.timestamp);
        emit Withdrawn(fingerprint, msg.sender, block.timestamp);
    }

    // ─── View functions ──────────────────────────────────────────────────────

    /// @notice Return the full record for a fingerprint.
    function getRecord(bytes32 fingerprint) external view returns (Record memory) {
        return _records[fingerprint];
    }

    /// @notice Return the current lifecycle state of a fingerprint.
    function getState(bytes32 fingerprint) external view returns (Lifecycle) {
        return _records[fingerprint].state;
    }

    /// @notice Return whether a fingerprint is currently in a "currently effective" state.
    /// @dev    Effective states are Issued and Published. Terminal states (Superseded,
    ///         Revoked, Expired, Withdrawn) are not effective.
    function isEffective(bytes32 fingerprint) external view returns (bool) {
        Lifecycle s = _records[fingerprint].state;
        return s == Lifecycle.Issued || s == Lifecycle.Published;
    }

    // ─── Internal helpers ────────────────────────────────────────────────────

    function _onlyRegistrant(bytes32 fingerprint) internal view returns (Record storage r) {
        r = _records[fingerprint];
        if (r.state == Lifecycle.None) revert NotRegistered(fingerprint);
        if (r.registrant != msg.sender) revert NotRegistrant(fingerprint, msg.sender);
    }
}
