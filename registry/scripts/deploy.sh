#!/usr/bin/env bash
# Deploy ParallaxRegistry to a target network.
#
# Usage:
#   ./scripts/deploy.sh anvil       — local testing (uses default anvil key)
#   ./scripts/deploy.sh sepolia     — Sepolia testnet (requires DEPLOYER_KEY + SEPOLIA_RPC_URL)
#   ./scripts/deploy.sh mainnet     — Mainnet (requires DEPLOYER_KEY + MAINNET_RPC_URL + ETHERSCAN_API_KEY)
#
# After Sepolia / mainnet deploy, edit registry/deployments.json to record the address.

set -euo pipefail

NETWORK="${1:-anvil}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

case "$NETWORK" in
    anvil)
        if ! pgrep -f "anvil" > /dev/null; then
            echo "Starting anvil..."
            anvil --silent > /tmp/anvil.log 2>&1 &
            sleep 3
            trap "pkill -f anvil 2>/dev/null" EXIT
        fi
        RPC_URL="http://127.0.0.1:8545"
        # Default anvil account 0
        DEPLOYER_KEY="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        VERIFY_FLAG=""
        ;;
    sepolia)
        : "${SEPOLIA_RPC_URL:?must be set}"
        : "${DEPLOYER_KEY:?must be set}"
        RPC_URL="$SEPOLIA_RPC_URL"
        VERIFY_FLAG="${ETHERSCAN_API_KEY:+--verify --etherscan-api-key $ETHERSCAN_API_KEY}"
        ;;
    mainnet)
        : "${MAINNET_RPC_URL:?must be set}"
        : "${DEPLOYER_KEY:?must be set}"
        : "${ETHERSCAN_API_KEY:?must be set for mainnet verification}"
        RPC_URL="$MAINNET_RPC_URL"
        VERIFY_FLAG="--verify --etherscan-api-key $ETHERSCAN_API_KEY"
        # Safety prompt
        read -p "Confirm mainnet deploy (yes/no)? " confirm
        [[ "$confirm" == "yes" ]] || { echo "Aborted."; exit 1; }
        ;;
    *)
        echo "Unknown network: $NETWORK (use anvil | sepolia | mainnet)"
        exit 1
        ;;
esac

echo "═══ Deploying ParallaxRegistry to $NETWORK ═══"
forge create src/ParallaxRegistry.sol:ParallaxRegistry \
    --rpc-url "$RPC_URL" \
    --private-key "$DEPLOYER_KEY" \
    --broadcast \
    $VERIFY_FLAG

echo
echo "═══ Next steps ═══"
echo "  1. Edit registry/deployments.json to record the deployed address, block, and tx hash."
echo "  2. Run a verification issue() call as the deployer to confirm event emission."
echo "  3. Update the paper's §22.5 (registry events) to cite the deployment."
