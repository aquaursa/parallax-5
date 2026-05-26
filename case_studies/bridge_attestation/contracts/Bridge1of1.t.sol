// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";

/// @title VULNERABLE: 1-of-1 verifier bridge (Kelp DAO archetype)
/// @notice A5 violation: insufficient quorum/diversity for external attestation.
contract Bridge1of1 {
    address public verifier;       // SINGLE verifier — quorum size 1
    mapping(bytes32 => bool) public consumed;
    uint256 public reserves;

    constructor(address v) {
        verifier = v;
    }

    function deposit() external payable {
        reserves += msg.value;
    }

    /// @notice Release reserves if "verifier" attests to the message.
    /// @dev VIOLATES A5: quorum=1, no diversity, no manipulation-resistance check.
    function release(
        address payable to,
        uint256 amount,
        bytes32 msgHash,
        bytes calldata sig
    ) external {
        require(!consumed[msgHash], "replay");
        // Single-verifier check
        require(_recover(msgHash, sig) == verifier, "bad sig");
        consumed[msgHash] = true;
        reserves -= amount;
        (bool ok,) = to.call{value: amount}("");
        require(ok, "xfer");
    }

    function _recover(bytes32 h, bytes memory sig) internal pure returns (address) {
        require(sig.length == 65, "sig len");
        bytes32 r; bytes32 s; uint8 v;
        assembly {
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }
        return ecrecover(h, v, r, s);
    }

    receive() external payable { reserves += msg.value; }
}

contract Bridge1of1Test is Test {
    Bridge1of1 b;
    address verifier = address(0x1);
    address victim = address(0x2);
    address attacker = address(0x3);

    function setUp() public {
        b = new Bridge1of1(verifier);
        vm.deal(address(this), 100 ether);
        b.deposit{value: 10 ether}();
    }

    /// @notice REFUTED: an attacker who controls the single verifier
    /// (e.g., via DDoS, RPC poisoning, or social engineering) can
    /// release arbitrary funds. The check passes per A3 but A5 fails
    /// because quorum=1 has no manipulation-resistance.
    function check_NoUnilateralRelease(
        bytes32 attackerMsg,
        uint256 amount
    ) public {
        vm.assume(amount > 0 && amount <= 5 ether);
        vm.assume(!b.consumed(attackerMsg));
        // Sign with the verifier's (potentially compromised) key
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(uint256(1), attackerMsg);
        bytes memory sig = abi.encodePacked(r, s, v);
        vm.prank(attacker);
        b.release(payable(attacker), amount, attackerMsg, sig);
        // Property: if the verifier was the only attestor and was
        // compromised, the bridge released funds with NO independent
        // attestation. This violates the generalized A5 requirement
        // (quorum, diversity).
        // We assert a witness exists: amount > 0 AND consumed
        assert(b.consumed(attackerMsg) && amount > 0);  // REFUTED-style: shows exploit is reachable
    }
}
