"""
PARALLAX-5 Demo 3 — AI-Agent Runtime Gate Simulator

Demonstrates the runtime-gate pattern: a StepSecure-checked relay
sitting between an AI agent and a target vault. Even if the agent's
reasoning produces a harmful transaction (jailbreak, prompt injection,
key compromise, hallucinated tool use), the gate refuses transitions
that violate the obligations.

Scenarios:
  A. Agent attempts a legitimate rebalance — gate permits.
  B. Agent attempts max-uint approval to attacker contract — gate rejects.
  C. Agent attempts to drain vault via single transfer — gate rejects.
  D. Agent attempts to drain vault via many small transfers — daily budget rejects.
  E. Agent attempts approval to non-whitelisted contract — gate rejects.

Each scenario is a faithful Python translation of the Solidity contract
state machine (TargetVault + RuntimeGate). The simulator is the
authoritative description of the gate's behavior for this demo.

Usage:
    python3 simulate.py
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class MockToken:
    balances: Dict[str, int] = field(default_factory=dict)
    allowances: Dict[Tuple[str, str], int] = field(default_factory=dict)

    def mint(self, to: str, amount: int):
        self.balances[to] = self.balances.get(to, 0) + amount

    def balance_of(self, who: str) -> int:
        return self.balances.get(who, 0)

    def transfer(self, sender: str, to: str, amount: int) -> bool:
        if self.balances.get(sender, 0) < amount:
            return False
        self.balances[sender] -= amount
        self.balances[to] = self.balances.get(to, 0) + amount
        return True

    def approve(self, owner: str, spender: str, amount: int) -> bool:
        self.allowances[(owner, spender)] = amount
        return True

    def allowance(self, owner: str, spender: str) -> int:
        return self.allowances.get((owner, spender), 0)


@dataclass
class TargetVault:
    """Python translation of TargetVault.sol."""
    asset: MockToken
    address: str
    owner: str
    agent_manager: str  # the gate contract's address, NOT the agent's key
    deposits: Dict[str, int] = field(default_factory=dict)
    total_deposits: int = 0

    def deposit(self, sender: str, amount: int):
        if sender != self.owner:
            raise RuntimeError("not owner")
        if not self.asset.transfer(sender, self.address, amount):
            raise RuntimeError("transfer failed")
        self.deposits[sender] = self.deposits.get(sender, 0) + amount
        self.total_deposits += amount

    def vault_balance(self) -> int:
        return self.asset.balance_of(self.address)

    def agent_approve(self, sender: str, spender: str, amount: int):
        if sender != self.agent_manager:
            raise RuntimeError("not agent")
        self.asset.approve(self.address, spender, amount)

    def agent_transfer(self, sender: str, to: str, amount: int):
        if sender != self.agent_manager:
            raise RuntimeError("not agent")
        if not self.asset.transfer(self.address, to, amount):
            raise RuntimeError("transfer failed")


@dataclass
class RuntimeGate:
    """Python translation of RuntimeGate.sol with the same predicates."""
    vault: TargetVault
    address: str   # the gate's own address in the ledger
    agent_key: str
    max_outflow_percent: int
    whitelisted_spenders: Dict[str, bool] = field(default_factory=dict)
    MAX_APPROVAL: int = 10**26
    DAILY_OUTFLOW_CAP_PERCENT: int = 20
    ONE_DAY: int = 86400
    daily_outflow: int = 0
    daily_outflow_reset_time: int = 86400  # one day from t=0
    current_time: int = 0  # simulator-controlled clock

    # ─── StepSecure predicates ────────────────────────────────────

    def is_stepsecure_transfer(self, amount: int) -> Tuple[bool, str]:
        balance = self.vault.vault_balance()
        cap = (balance * self.max_outflow_percent) // 100
        if amount > cap:
            return False, f"outflow {amount:,} exceeds cap {cap:,} ({self.max_outflow_percent}%)"
        return True, ""

    def is_stepsecure_approve(self, spender: str, amount: int) -> Tuple[bool, str]:
        if not self.whitelisted_spenders.get(spender, False):
            return False, f"spender {spender} not whitelisted"
        if amount > self.MAX_APPROVAL:
            return False, f"approval {amount:,} exceeds MAX_APPROVAL {self.MAX_APPROVAL:,}"
        return True, ""

    def is_stepsecure_daily_budget(self, amount: int) -> Tuple[bool, str]:
        balance = self.vault.vault_balance()
        daily_cap = (balance * self.DAILY_OUTFLOW_CAP_PERCENT) // 100
        projected = amount if self.current_time >= self.daily_outflow_reset_time else self.daily_outflow + amount
        if projected > daily_cap:
            return False, f"projected daily outflow {projected:,} exceeds cap {daily_cap:,}"
        return True, ""

    # ─── Gate-permitted agent actions ─────────────────────────────

    def transfer(self, sender: str, to: str, amount: int):
        if sender != self.agent_key:
            raise RuntimeError("not the agent")
        ok, reason = self.is_stepsecure_transfer(amount)
        if not ok:
            raise RuntimeError(f"REJECTED (transfer): {reason}")
        ok2, reason2 = self.is_stepsecure_daily_budget(amount)
        if not ok2:
            raise RuntimeError(f"REJECTED (transfer): {reason2}")
        # Update daily outflow
        if self.current_time >= self.daily_outflow_reset_time:
            self.daily_outflow = amount
            self.daily_outflow_reset_time = self.current_time + self.ONE_DAY
        else:
            self.daily_outflow += amount
        # Forward to vault (gate's address is the vault's agent_manager)
        self.vault.agent_transfer(self.address, to, amount)
        return True

    def approve(self, sender: str, spender: str, amount: int):
        if sender != self.agent_key:
            raise RuntimeError("not the agent")
        ok, reason = self.is_stepsecure_approve(spender, amount)
        if not ok:
            raise RuntimeError(f"REJECTED (approve): {reason}")
        self.vault.agent_approve(self.address, spender, amount)
        return True


# ─── Setup ────────────────────────────────────────────────────────────

USER = "0xUser"
AGENT_KEY = "0xAgentKey"
GATE_ADDR = "0xGate"
VAULT_ADDR = "0xVault"
STRATEGY_A = "0xStrategyA"          # whitelisted, legitimate yield strategy
STRATEGY_B = "0xStrategyB"          # whitelisted, alternative
EVIL_CONTRACT = "0xEvilDrainer"     # NOT whitelisted


def setup() -> Tuple[MockToken, TargetVault, RuntimeGate]:
    token = MockToken()
    token.mint(USER, 1_000_000)

    vault = TargetVault(asset=token, address=VAULT_ADDR, owner=USER, agent_manager=GATE_ADDR)
    gate = RuntimeGate(
        vault=vault,
        address=GATE_ADDR,
        agent_key=AGENT_KEY,
        max_outflow_percent=5,  # 5% per transaction
        whitelisted_spenders={STRATEGY_A: True, STRATEGY_B: True},
    )

    # User deposits 1M tokens
    vault.deposit(USER, 1_000_000)
    return token, vault, gate


# ─── Scenarios ────────────────────────────────────────────────────────

def scenario_A_legitimate_rebalance() -> bool:
    """Agent does a small, legitimate rebalance — should pass."""
    print("\n  Scenario A: Legitimate rebalance (agent transfers 4% to whitelisted strategy)")
    token, vault, gate = setup()
    print(f"    Vault balance: {vault.vault_balance():,}")
    try:
        gate.transfer(sender=AGENT_KEY, to=STRATEGY_A, amount=40_000)
        print(f"    ✓ PERMITTED: 40,000 tokens transferred to {STRATEGY_A}")
        print(f"    Vault balance after: {vault.vault_balance():,}")
        return True
    except RuntimeError as e:
        print(f"    ✗ UNEXPECTED REJECTION: {e}")
        return False


def scenario_B_max_approval_attack() -> bool:
    """Agent compromised; tries max-uint approval to drainer — gate rejects."""
    print("\n  Scenario B: Compromised agent tries max-uint approval to attacker contract")
    token, vault, gate = setup()
    MAX_UINT = 2**256 - 1
    try:
        gate.approve(sender=AGENT_KEY, spender=EVIL_CONTRACT, amount=MAX_UINT)
        print(f"    ✗ FAIL: gate permitted max-uint approval to evil contract!")
        return False
    except RuntimeError as e:
        print(f"    ✓ {e}")
        # Verify vault is intact
        if vault.vault_balance() == 1_000_000:
            print(f"    ✓ Vault balance unchanged: {vault.vault_balance():,}")
            return True
        return False


def scenario_C_drain_single_transfer() -> bool:
    """Agent tries to drain everything in one transaction — single-tx cap rejects."""
    print("\n  Scenario C: Agent tries to drain 100% in one transfer")
    token, vault, gate = setup()
    try:
        gate.transfer(sender=AGENT_KEY, to=EVIL_CONTRACT, amount=1_000_000)
        print(f"    ✗ FAIL: gate permitted full drain!")
        return False
    except RuntimeError as e:
        print(f"    ✓ {e}")
        if vault.vault_balance() == 1_000_000:
            print(f"    ✓ Vault balance unchanged: {vault.vault_balance():,}")
            return True
        return False


def scenario_D_drain_via_repeated_transfers() -> bool:
    """Agent tries to drain via many small transfers within a day — daily cap rejects."""
    print("\n  Scenario D: Agent tries to drain via repeated 5%-cap transfers (daily budget)")
    token, vault, gate = setup()
    transfers_completed = 0
    last_error = ""
    for i in range(10):  # try 10 transfers
        try:
            # Each is at the single-tx cap (5% of current balance, but cap evaluates against current vault balance)
            # First call: 5% of 1M = 50,000. After: 950,000 vault balance, 5% = 47,500. Etc.
            balance = vault.vault_balance()
            amount = (balance * 5) // 100
            if amount == 0:
                break
            gate.transfer(sender=AGENT_KEY, to=STRATEGY_A, amount=amount)  # to whitelisted but adversary-controlled
            transfers_completed += 1
        except RuntimeError as e:
            last_error = str(e)
            break
    print(f"    Transfers completed before rejection: {transfers_completed}")
    if last_error:
        print(f"    ✓ {last_error}")
    # The total outflow should be bounded by daily cap (20%)
    drained = 1_000_000 - vault.vault_balance()
    print(f"    Total drained in one day: {drained:,} ({drained/10000:.1f}% of initial)")
    if drained <= 1_000_000 * 0.25:  # allow small slack for rounding/budget timing
        print(f"    ✓ Daily budget bounded the drain to <= 25%")
        return True
    print(f"    ✗ FAIL: drain exceeded daily budget!")
    return False


def scenario_E_unwhitelisted_approval() -> bool:
    """Agent tries to approve a contract that wasn't pre-approved — gate rejects."""
    print("\n  Scenario E: Agent tries to approve non-whitelisted strategy contract")
    token, vault, gate = setup()
    NEW_STRATEGY = "0xNewYieldFarm"
    try:
        gate.approve(sender=AGENT_KEY, spender=NEW_STRATEGY, amount=10_000)
        print(f"    ✗ FAIL: gate permitted approval to non-whitelisted contract!")
        return False
    except RuntimeError as e:
        print(f"    ✓ {e}")
        return True


def main() -> int:
    print("=" * 72)
    print("  PARALLAX-5 Demo 3: AI-Agent Runtime Gate (A1 + A2 + D5 enforcement)")
    print("=" * 72)

    results = [
        ("A. Legitimate rebalance permitted",   scenario_A_legitimate_rebalance()),
        ("B. Max-uint approval rejected",       scenario_B_max_approval_attack()),
        ("C. Single-tx drain rejected",         scenario_C_drain_single_transfer()),
        ("D. Daily-budget drain rejected",      scenario_D_drain_via_repeated_transfers()),
        ("E. Unwhitelisted approval rejected",  scenario_E_unwhitelisted_approval()),
    ]

    print()
    print("=" * 72)
    print("  Summary:")
    print("=" * 72)
    all_passed = True
    for name, ok in results:
        marker = "✓" if ok else "✗"
        print(f"    {marker}  {name}")
        if not ok:
            all_passed = False
    print()
    if all_passed:
        print("  Result: All five scenarios produced the predicted gate behavior.")
        print("          The runtime gate provides D5 enforcement for A1 (value")
        print("          conservation) and A2 (authorization closure) over the")
        print("          AI-agent's transaction surface.")
        return 0
    else:
        print("  UNEXPECTED: at least one scenario failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
