// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../src/Bridge.sol";

contract A3VulnerableTest {
    /// SHOULD FAIL: halmos finds a (v, r, s, h) tuple where processed[id]
    /// becomes true with a signature that doesn't recover to expectedSigner.
    /// In the vulnerable contract there IS no expectedSigner check, so any
    /// well-formed sig is accepted.
    function check_A3_unauthenticated_processing(
        bytes32 h, uint8 v, bytes32 r, bytes32 s, uint256 id
    ) public {
        BridgeVuln bridge = new BridgeVuln();
        bridge.processVAA(h, v, r, s, id);
        // A3 assertion: processed[id] = true should require a valid signed message.
        // We assert it MUST NOT happen unconditionally → halmos finds it does.
        assert(!bridge.processed(id));  // expect: fails (processed becomes true unconditionally)
    }
}

contract A3HardenedTest {
    /// SHOULD PASS: halmos proves no (v,r,s) makes processed[id]=true
    /// unless the signature recovers to expectedSigner.
    function check_A3_hardened_rejects_bad_sigs(
        bytes32 h, uint8 v, bytes32 r, bytes32 s, uint256 id
    ) public {
        address expected = address(0x1234);
        BridgeHardened bridge = new BridgeHardened(expected);
        address recovered = ecrecover(h, v, r, s);
        // try/catch the call; if it succeeds, the signature must have been valid
        try bridge.processVAA(h, v, r, s, id) {
            // post-condition: signature must have been the expected one
            assert(recovered != address(0));
            assert(recovered == expected);
        } catch {
            // Reverted - that's expected for invalid sigs. A3 preserved.
        }
    }
}
