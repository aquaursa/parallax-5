// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/ParallaxRegistry.sol";

/// @notice Deploy script for ParallaxRegistry.
///
/// Usage:
///   forge script script/Deploy.s.sol --rpc-url $SEPOLIA_RPC_URL \
///     --private-key $DEPLOYER_KEY --broadcast --verify
///
/// For local anvil:
///   anvil &
///   forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 \
///     --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
///     --broadcast
contract DeployScript is Script {
    function run() external returns (ParallaxRegistry registry) {
        uint256 deployerKey = vm.envOr("DEPLOYER_KEY", uint256(0));

        if (deployerKey != 0) {
            vm.startBroadcast(deployerKey);
        } else {
            // Local anvil: use default account
            vm.startBroadcast();
        }

        registry = new ParallaxRegistry();

        vm.stopBroadcast();

        console.log("ParallaxRegistry deployed at:", address(registry));
        console.log("Block number:", block.number);
        console.log("Deployer:", msg.sender);
        console.log("");
        console.log("Next: record the address in deployments.json and update the paper's");
        console.log("registry section to cite this deployment.");
    }
}
