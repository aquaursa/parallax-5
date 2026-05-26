# PARALLAX-5 Certificate Registry

The on-chain registry that anchors PARALLAX-5 certificate lifecycle events. This document covers the contract design, deployment process, gas profile, the Python client, the CLI integration, and the Lean state-machine soundness proof.

## What it is

A permissionless EVM contract that records the lifecycle of PARALLAX-5 certificates. Anyone can call `issue()` against a certificate's fingerprint; only the original registrant can transition that record's state. Events emitted on each transition allow off-chain consumers (block explorers, scanning indexers, reputation services) to reconstruct the substrate's "trust ledger" without any privileged operator.

The contract is the on-chain projection of the [Certificate Schema v1.0 §3 lifecycle state machine](./PARALLAX5_CERTIFICATE_SCHEMA_v1.0.md). The schema's draft state is intentionally omitted from the contract: drafts are off-chain (the canonical certificate JSON has not yet been signed by the issuer); the on-chain record begins at `Issued` and proceeds through `Published` to one of four terminal states.

```
        ┌─────────┐  issue()  ┌────────┐  publish()  ┌───────────┐
        │ (None)  │ ────────► │ Issued │ ──────────► │ Published │
        └─────────┘           └────────┘             └───────────┘
                                                          │
                              ┌───────────────────────────┼───────────────────┐
                              │              │            │                   │
                       supersede()       revoke()     expire()          withdraw()
                              ▼              ▼            ▼                   ▼
                       ┌────────────┐ ┌─────────┐ ┌─────────┐         ┌─────────────┐
                       │ Superseded │ │ Revoked │ │ Expired │         │ Withdrawn   │
                       └────────────┘ └─────────┘ └─────────┘         └─────────────┘
                              ▲              ▲            ▲                   ▲
                              └──── terminal states (absorbing) ──────────────┘
```

## Contract surface

- **Source**: [`registry/src/ParallaxRegistry.sol`](./registry/src/ParallaxRegistry.sol)
- **Solidity**: 0.8.24 (optimizer enabled, 200 runs)
- **License**: Apache-2.0
- **Tests**: [`registry/test/ParallaxRegistry.t.sol`](./registry/test/ParallaxRegistry.t.sol) — 24 tests passing, including 2 fuzz tests at 256 runs each
- **Lean proof**: [`lean/Parallax5/Registry.lean`](./lean/Parallax5/Registry.lean) — 6 theorems, 0 `sorry`

Functions, all parameters typed `bytes32` fingerprint (SHA-256 of canonical certificate JSON):

| Function | Permission | Transition |
|---|---|---|
| `issue(bytes32 fingerprint)` | Permissionless | `None → Issued` |
| `publish(bytes32 fingerprint)` | Registrant only | `Issued → Published` |
| `supersede(bytes32 fingerprint, bytes32 successor)` | Registrant only | `Published → Superseded` |
| `revoke(bytes32 fingerprint, string reason)` | Registrant only | `Published → Revoked` |
| `expire(bytes32 fingerprint)` | Permissionless | `Published → Expired` |
| `withdraw(bytes32 fingerprint)` | Registrant only | `Published → Withdrawn` |

Views: `getRecord`, `getState`, `isEffective`, `issuerCertCount`, `totalIssued`.

Errors are typed: `AlreadyRegistered`, `NotRegistered`, `NotRegistrant`, `InvalidTransition`, `ZeroFingerprint`, `SelfSupersession`.

## Gas profile (anvil-verified)

| Method | Gas |
|---|---|
| `issue()` | ~115k (1 SSTORE + event + counter increment) |
| `publish()` | ~32k (1 SSTORE update + event) |
| `supersede()` | ~38k (1 SSTORE update + indexed successor + event) |
| `revoke()` | ~38k (1 SSTORE update + string arg + event) |
| `expire()` | ~32k (permissionless) |
| `withdraw()` | ~32k |

Mainnet operating cost at 30 gwei × $2,500/ETH: roughly $8.60 per `issue()`, $2.40 per state transition. Sepolia testnet: free.

## Deployment

### Local (anvil)

```bash
cd registry
./scripts/deploy.sh anvil
```

Anvil's deterministic CREATE2 address from the default account is `0x5FbDB2315678afecb367f032d93F642f64180aa3`.

### Sepolia testnet

```bash
export SEPOLIA_RPC_URL="https://sepolia.infura.io/v3/<your-key>"
export DEPLOYER_KEY="0x<your-key-here>"
export ETHERSCAN_API_KEY="<your-etherscan-key>"   # optional, enables source verification

cd registry
./scripts/deploy.sh sepolia
```

After deployment, edit [`registry/deployments.json`](./registry/deployments.json) to record the address, deployment block, transaction hash, and deployer.

### Mainnet

```bash
export MAINNET_RPC_URL="https://mainnet.infura.io/v3/<your-key>"
export DEPLOYER_KEY="0x<your-key-here>"
export ETHERSCAN_API_KEY="<your-etherscan-key>"   # required for mainnet

cd registry
./scripts/deploy.sh mainnet
# Confirms with "yes" prompt
```

The mainnet path requires explicit confirmation; the script will not proceed without it.

## Python client

[`src/parallax5_coordinator/registry_client.py`](./src/parallax5_coordinator/registry_client.py) wraps the contract's ABI and exposes a typed Python interface. The client reads the signing key from the `PARALLAX5_REGISTRY_KEY` environment variable (never persisted) and constructs EIP-1559 transactions.

```python
from parallax5_coordinator.registry_client import RegistryClient, load_deployment

deployment = load_deployment("sepolia")
client = RegistryClient(
    rpc_url=deployment["rpc_url"],
    contract_address=deployment["address"],
    private_key=os.environ["PARALLAX5_REGISTRY_KEY"],
    chain_id=deployment["chain_id"],
)

# Submit a certificate
receipt = client.issue("0xa880650b924463c61c78c014f4966e554fa59913941e872e036255259a8da86d")
print(receipt)  # {tx_hash, block_number, gas_used, status, ...}

# Verify on-chain state
state = client.get_state("0xa880650b924463c61c78c014f4966e554fa59913941e872e036255259a8da86d")
print(state)  # Lifecycle.ISSUED
```

## CLI integration

The coordinator's `parallax5 registry submit` command consumes a certificate JSON, extracts its fingerprint, and submits an on-chain `issue()` call to the deployment on the target network.

```bash
# Dry-run (default, no transaction sent)
parallax5 registry submit demos/vault/output/certificate.json

# Live submission to Sepolia (requires PARALLAX5_REGISTRY_KEY env var)
export PARALLAX5_REGISTRY_KEY="0x<issuer-signing-key>"
parallax5 registry submit demos/vault/output/certificate.json --network sepolia --broadcast

# Verify on-chain state of a previously-submitted certificate
parallax5 registry state demos/vault/output/certificate.json --network sepolia
```

The CLI never persists the signing key, and refuses to broadcast unless both `--broadcast` and `PARALLAX5_REGISTRY_KEY` are present. Dry-run is the default.

## Lean state-machine soundness proof

The contract's state machine is formally verified in [`lean/Parallax5/Registry.lean`](./lean/Parallax5/Registry.lean), with 6 theorems and zero `sorry`:

| Theorem | Property |
|---|---|
| `terminal_absorbs` | No transition originates from a terminal state |
| `effective_iff_operational` | `isEffective()` returns true exactly for `{Issued, Published}` |
| `terminal_predecessor_is_published` | Every transition into a terminal state originates from `Published` |
| `published_targets` | The four targets reachable from `Published` are exactly the terminals |
| `no_self_loop` | The contract's `SelfSupersession` revert proves a record cannot supersede itself |
| `transition_preserves_valid` | All six transitions preserve the `ValidState` invariant |

These theorems prove the on-chain state machine implements the schema RFC v1.0 §3 specification. The proofs are by structural case analysis on the `Transition` inductive type; the Lean kernel accepts them with no remaining proof obligations.

## Self-application

The registry contract is itself a PARALLAX-5 artifact. It can therefore carry its own PARALLAX-5 certificate, recording:

```yaml
obligation_coverage:
  A1: D4   # state integrity, formally proved (Registry.lean)
  A2: D4   # authorization closure, formally proved (Registry.lean)
walkaway: full
  rationale: |
    The contract has no admin role, no pausing mechanism, no upgrade path.
    Once deployed, the substrate's certificate ledger continues to operate
    in the deployer's absence.
crops: { C: 4, R: 5, O: 5, P: 0, S: 4 }
proof_artifacts:
  - lean/Parallax5/Registry.lean      # 6 theorems, 0 sorry
  - registry/test/ParallaxRegistry.t.sol  # 24 Foundry tests, 24 pass
```

This self-application is the strongest demonstration of substrate maturity: the infrastructure that records certificates carries a certificate that satisfies the same obligations it records.

## Audit notes

- The contract holds **no value**. There is no transfer of ether or tokens, no funds at risk; the contract is purely a state machine over fingerprints.
- All write functions emit events whose indexed topics are the fingerprint and the issuer / successor. Indexers can reconstruct the full ledger from logs alone.
- The `expire()` function is permissionless by design: any party can attest that a certificate's validity window has lapsed. This prevents registrants from indefinitely keeping a stale certificate in `Published`. If a registrant disputes an expiration, they re-issue a fresh certificate.
- The `supersede()` function strictly requires the successor to be already registered (state ≠ `None`), preventing supersession by phantom certificates.
- The `SelfSupersession` guard makes the supersession edge a strict partial order; the Lean `no_self_loop` theorem mechanizes this.
- The `bytes32(0)` fingerprint is rejected at `issue()` time via the `ZeroFingerprint` error.

## Files

| Path | Purpose |
|---|---|
| `registry/src/ParallaxRegistry.sol` | The contract |
| `registry/test/ParallaxRegistry.t.sol` | 24-test Foundry suite (24 pass, including 2 fuzz at 256 runs) |
| `registry/script/Deploy.s.sol` | Foundry deploy script |
| `registry/scripts/deploy.sh` | Convenience shell wrapper for anvil / sepolia / mainnet |
| `registry/deployments.json` | Canonical deployment manifest (per-network address records) |
| `registry/foundry.toml` | Foundry configuration |
| `src/parallax5_coordinator/registry_client.py` | Python web3 client |
| `lean/Parallax5/Registry.lean` | State-machine soundness proof |
| `docs/REGISTRY.md` | This document |
