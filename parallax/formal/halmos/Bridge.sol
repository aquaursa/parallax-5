// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract BridgeVuln {
    mapping(uint256 => bool) public processed;
    
    /// Wormhole-class: ecrecover used but no zero-check, no signer comparison.
    function processVAA(bytes32 h, uint8 v, bytes32 r, bytes32 s, uint256 id) external {
        ecrecover(h, v, r, s);  // result discarded
        processed[id] = true;
    }
}

contract BridgeHardened {
    address public expectedSigner;
    mapping(uint256 => bool) public processed;
    
    constructor(address _signer) { expectedSigner = _signer; }
    
    function processVAA(bytes32 h, uint8 v, bytes32 r, bytes32 s, uint256 id) external {
        address recovered = ecrecover(h, v, r, s);
        require(recovered != address(0), "zero recovery");
        require(recovered == expectedSigner, "wrong signer");
        processed[id] = true;
    }
}
