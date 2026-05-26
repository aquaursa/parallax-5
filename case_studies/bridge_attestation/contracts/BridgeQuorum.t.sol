// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";

/// @title HARDENED: q-of-n verifier bridge with diversity
/// @notice Generalized A5: quorum + diversity + replay protection +
/// domain binding + freshness.
contract BridgeQuorum {
    address[] public verifiers;
    uint256 public immutable threshold;     // q in q-of-n
    uint256 public immutable maxAge;        // freshness window (sec)
    bytes32 public immutable domain;        // domain binding
    mapping(bytes32 => bool) public consumed;
    uint256 public reserves;

    constructor(address[] memory _verifiers, uint256 _threshold, uint256 _maxAge, bytes32 _domain) {
        require(_threshold > 1 && _threshold <= _verifiers.length, "PARALLAX-A5: quorum=1");
        require(_verifiers.length >= 3, "PARALLAX-A5: insufficient diversity");
        verifiers = _verifiers;
        threshold = _threshold;
        maxAge = _maxAge;
        domain = _domain;
    }

    function deposit() external payable { reserves += msg.value; }

    function release(
        address payable to,
        uint256 amount,
        bytes32 msgHash,
        uint256 issuedAt,
        bytes[] calldata sigs
    ) external {
        require(!consumed[msgHash], "PARALLAX-A5: replay");
        require(block.timestamp - issuedAt <= maxAge, "PARALLAX-A5: stale");
        // Quorum + diversity check
        uint256 valid = 0;
        bool[] memory seen = new bool[](verifiers.length);
        bytes32 boundHash = keccak256(abi.encodePacked(domain, msgHash, issuedAt, to, amount));
        for (uint256 i = 0; i < sigs.length; i++) {
            address signer = _recover(boundHash, sigs[i]);
            for (uint256 j = 0; j < verifiers.length; j++) {
                if (verifiers[j] == signer && !seen[j]) {
                    seen[j] = true;
                    valid++;
                    break;
                }
            }
        }
        require(valid >= threshold, "PARALLAX-A5: insufficient signatures");
        consumed[msgHash] = true;
        reserves -= amount;
        (bool ok,) = to.call{value: amount}("");
        require(ok, "xfer");
    }

    function _recover(bytes32 h, bytes memory sig) internal pure returns (address) {
        if (sig.length != 65) return address(0);
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

contract BridgeQuorumTest is Test {
    BridgeQuorum b;
    address[] verifiers;
    uint256[] keys;
    address attacker = address(0x99);

    function setUp() public {
        keys = [uint256(1), uint256(2), uint256(3), uint256(4), uint256(5)];
        for (uint256 i = 0; i < 5; i++) {
            verifiers.push(vm.addr(keys[i]));
        }
        b = new BridgeQuorum(verifiers, 3, 3600, keccak256("PARALLAX-BRIDGE-V1"));
        vm.deal(address(this), 100 ether);
        b.deposit{value: 10 ether}();
    }

    /// @notice PASS: a single compromised verifier cannot release funds.
    /// Bytecode-level proof that A5 quorum is correctly enforced.
    function check_NoUnilateralRelease(uint256 amount, bytes32 msgHash) public {
        vm.assume(amount > 0 && amount <= 5 ether);
        vm.assume(!b.consumed(msgHash));
        // Attacker controls verifier[0] only
        bytes32 bound = keccak256(abi.encodePacked(
            keccak256("PARALLAX-BRIDGE-V1"), msgHash, block.timestamp, payable(attacker), amount
        ));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(keys[0], bound);
        bytes[] memory sigs = new bytes[](1);
        sigs[0] = abi.encodePacked(r, s, v);
        vm.expectRevert(bytes("PARALLAX-A5: insufficient signatures"));
        b.release(payable(attacker), amount, msgHash, block.timestamp, sigs);
    }
}
