"""
PARALLAX-5 on-chain registry client.

Bridges the coordinator's certificate output to the ParallaxRegistry contract
deployed on Sepolia or mainnet (or a local anvil for testing).

The client is intentionally minimal: it constructs the calldata for issue() /
publish() / supersede() / revoke() / expire() / withdraw() against a given
fingerprint, and (when a private key is supplied) signs and broadcasts the
transaction via the configured JSON-RPC endpoint.

For the canonical deployment addresses, see deployments.json.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Optional

try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    from eth_account import Account
    HAS_WEB3 = True
except ImportError:
    HAS_WEB3 = False


# ─── Lifecycle enum (matches the contract) ──────────────────────────────────

class Lifecycle(IntEnum):
    NONE = 0
    DRAFT = 1
    ISSUED = 2
    PUBLISHED = 3
    SUPERSEDED = 4
    REVOKED = 5
    EXPIRED = 6
    WITHDRAWN = 7


# ─── ABI (minimal subset, generated from the Foundry build) ─────────────────

REGISTRY_ABI = [
    {
        "type": "function", "name": "issue", "stateMutability": "nonpayable",
        "inputs": [{"name": "fingerprint", "type": "bytes32"}], "outputs": []
    },
    {
        "type": "function", "name": "publish", "stateMutability": "nonpayable",
        "inputs": [{"name": "fingerprint", "type": "bytes32"}], "outputs": []
    },
    {
        "type": "function", "name": "supersede", "stateMutability": "nonpayable",
        "inputs": [
            {"name": "fingerprint", "type": "bytes32"},
            {"name": "successor", "type": "bytes32"},
        ], "outputs": []
    },
    {
        "type": "function", "name": "revoke", "stateMutability": "nonpayable",
        "inputs": [
            {"name": "fingerprint", "type": "bytes32"},
            {"name": "reason", "type": "string"},
        ], "outputs": []
    },
    {
        "type": "function", "name": "expire", "stateMutability": "nonpayable",
        "inputs": [{"name": "fingerprint", "type": "bytes32"}], "outputs": []
    },
    {
        "type": "function", "name": "withdraw", "stateMutability": "nonpayable",
        "inputs": [{"name": "fingerprint", "type": "bytes32"}], "outputs": []
    },
    {
        "type": "function", "name": "getState", "stateMutability": "view",
        "inputs": [{"name": "fingerprint", "type": "bytes32"}],
        "outputs": [{"name": "", "type": "uint8"}]
    },
    {
        "type": "function", "name": "totalIssued", "stateMutability": "view",
        "inputs": [], "outputs": [{"name": "", "type": "uint256"}]
    },
]


@dataclass
class RegistryClient:
    rpc_url: str
    contract_address: str
    private_key: Optional[str] = None   # If None, view-only / dry-run mode
    chain_id: Optional[int] = None      # Inferred from RPC if None

    def __post_init__(self) -> None:
        if not HAS_WEB3:
            raise ImportError(
                "web3.py is required for on-chain registry submission. "
                "Install with: pip install web3 eth-account"
            )
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        # Sepolia / Goerli PoA chains need middleware
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        if self.chain_id is None:
            self.chain_id = self.w3.eth.chain_id
        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.contract_address),
            abi=REGISTRY_ABI,
        )

    # ─── Read-only ──────────────────────────────────────────────────────────

    def get_state(self, fingerprint_hex: str) -> Lifecycle:
        """Return the lifecycle state of a fingerprint."""
        fp = self._normalize_fp(fingerprint_hex)
        raw = self.contract.functions.getState(fp).call()
        return Lifecycle(raw)

    def total_issued(self) -> int:
        return self.contract.functions.totalIssued().call()

    # ─── Write (requires private key) ───────────────────────────────────────

    def issue(self, fingerprint_hex: str) -> dict:
        return self._send("issue", [self._normalize_fp(fingerprint_hex)])

    def publish(self, fingerprint_hex: str) -> dict:
        return self._send("publish", [self._normalize_fp(fingerprint_hex)])

    def supersede(self, fingerprint_hex: str, successor_hex: str) -> dict:
        return self._send("supersede", [
            self._normalize_fp(fingerprint_hex),
            self._normalize_fp(successor_hex),
        ])

    def revoke(self, fingerprint_hex: str, reason: str) -> dict:
        return self._send("revoke", [self._normalize_fp(fingerprint_hex), reason])

    def expire(self, fingerprint_hex: str) -> dict:
        return self._send("expire", [self._normalize_fp(fingerprint_hex)])

    def withdraw(self, fingerprint_hex: str) -> dict:
        return self._send("withdraw", [self._normalize_fp(fingerprint_hex)])

    # ─── Internal helpers ───────────────────────────────────────────────────

    @staticmethod
    def _normalize_fp(fp_hex: str) -> bytes:
        s = fp_hex[2:] if fp_hex.startswith("0x") else fp_hex
        if len(s) != 64:
            raise ValueError(f"Fingerprint must be 64 hex chars (32 bytes); got {len(s)}")
        return bytes.fromhex(s)

    def _send(self, method: str, args: list) -> dict:
        if not self.private_key:
            raise RuntimeError(
                "RegistryClient instantiated without private_key; cannot send transactions. "
                "Set the PARALLAX5_REGISTRY_KEY env var or pass private_key explicitly."
            )
        account = Account.from_key(self.private_key)
        fn = getattr(self.contract.functions, method)(*args)
        nonce = self.w3.eth.get_transaction_count(account.address)
        gas_estimate = fn.estimate_gas({"from": account.address})

        tx = fn.build_transaction({
            "chainId": self.chain_id,
            "from": account.address,
            "nonce": nonce,
            "gas": int(gas_estimate * 1.2),
            "maxFeePerGas": self.w3.to_wei(20, "gwei"),
            "maxPriorityFeePerGas": self.w3.to_wei(1, "gwei"),
        })
        signed = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        return {
            "method": method,
            "tx_hash": "0x" + tx_hash.hex(),
            "block_number": receipt["blockNumber"],
            "gas_used": receipt["gasUsed"],
            "status": "success" if receipt["status"] == 1 else "reverted",
            "from": account.address,
            "to": self.contract.address,
            "chain_id": self.chain_id,
        }


# ─── Helper: load deployment metadata ───────────────────────────────────────

def load_deployment(network: str = "sepolia",
                    deployments_path: Optional[Path] = None) -> dict:
    """Read the canonical deployments.json from the repo root."""
    if deployments_path is None:
        # Try to find deployments.json relative to this file
        here = Path(__file__).resolve().parent
        for candidate in [here / ".." / ".." / "registry" / "deployments.json",
                          here / ".." / ".." / ".." / "registry" / "deployments.json",
                          Path.cwd() / "registry" / "deployments.json"]:
            if candidate.exists():
                deployments_path = candidate
                break
        else:
            raise FileNotFoundError(
                "deployments.json not found; pass deployments_path explicitly."
            )
    data = json.loads(deployments_path.read_text())
    if network not in data:
        raise KeyError(f"Network '{network}' not in deployments.json; known: {list(data)}")
    return data[network]


# ─── CLI convenience entry point ────────────────────────────────────────────

def submit_certificate(cert_path: Path,
                       network: str = "sepolia",
                       dry_run: bool = False) -> dict:
    """Top-level: read a certificate JSON, extract its fingerprint, submit issue() on chain."""
    cert = json.loads(Path(cert_path).read_text())
    fp = cert["fingerprint"]
    if not fp.startswith("0x"):
        fp = "0x" + fp

    if dry_run:
        return {
            "dry_run": True,
            "would_submit": {
                "method": "issue",
                "fingerprint": fp,
                "network": network,
            },
        }

    deployment = load_deployment(network)
    private_key = os.environ.get("PARALLAX5_REGISTRY_KEY")
    if not private_key:
        raise RuntimeError(
            "PARALLAX5_REGISTRY_KEY env var not set. "
            "Set it to the issuer's signing key (held off-line; this client never persists it)."
        )

    client = RegistryClient(
        rpc_url=deployment["rpc_url"],
        contract_address=deployment["address"],
        private_key=private_key,
        chain_id=deployment.get("chain_id"),
    )
    return client.issue(fp)
