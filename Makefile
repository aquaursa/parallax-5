# PARALLAX-5 — Makefile for Worked examples (Three Flagship Demos)
#
# Targets:
#   make demo-vault   — Demo 1: ERC-4626 inflation attack (A1)
#   make demo-bridge  — Demo 2: bridge attestation (A3 + A5)
#   make demo-agent   — Demo 3: AI-agent runtime gate (A1 + A2 + D5)
#   make demo-all     — runs all three end-to-end
#   make test         — runs the package test suites (theorems + crops)
#   make clean        — removes generated certificate artifacts
#
# Requirements: python3 with jsonschema, pyyaml, ecdsa; solc 0.8.20; slither 0.11.x
# License: Apache-2.0

ROOT := $(shell pwd)
PY := PYTHONPATH=$(ROOT)/src python3
PARALLAX5 := $(PY) -m parallax5_coordinator.cli

.PHONY: demo-vault demo-bridge demo-agent demo-all test clean help

help:
	@echo "PARALLAX-5 Demo Orchestration"
	@echo ""
	@echo "  make demo-vault   ERC-4626 inflation attack (A1 conservation)"
	@echo "  make demo-bridge  Bridge attestation (A3 signature + A5 freshness)"
	@echo "  make demo-agent   AI-agent runtime gate (A1 + A2 + D5 enforcement)"
	@echo "  make demo-all     run all three demos in sequence"
	@echo "  make test         run the package test suites"
	@echo "  make clean        remove generated certificate artifacts"

demo-vault:
	@echo "================================================================="
	@echo "  Demo 1: ERC-4626 inflation attack (A1 conservation)"
	@echo "================================================================="
	@echo ""
	@echo "── Step 1/5: Exploit simulator ──────────────────────────────────"
	cd demos/vault && python3 exploit.py
	@echo ""
	@echo "── Step 2/5: Slither on vulnerable + patched ────────────────────"
	-cd demos/vault/contracts && slither VulnerableVault.sol --json /tmp/vault_vuln.json 2>&1 | tail -2
	-cd demos/vault/contracts && slither PatchedVault.sol --json /tmp/vault_patched.json 2>&1 | tail -2
	@echo ""
	@echo "── Step 3/5: Generate certificate ───────────────────────────────"
	cd demos/vault && $(PARALLAX5) certify parallax.yaml --output output/certificate.json
	@echo ""
	@echo "── Step 4/5: Validate certificate ───────────────────────────────"
	cd demos/vault && $(PARALLAX5) validate output/certificate.json
	@echo ""
	@echo "── Step 5/5: Registry submission payload ────────────────────────"
	cd demos/vault && $(PARALLAX5) registry submit output/certificate.json --dry-run
	@echo ""
	@echo "✓ Demo 1 complete. Report: demos/vault/REPORT.md"

demo-bridge:
	@echo "================================================================="
	@echo "  Demo 2: Bridge attestation (A3 + A5)"
	@echo "================================================================="
	@echo ""
	@echo "── Step 1/5: Exploit simulator (4 scenarios) ────────────────────"
	cd demos/bridge && python3 exploit.py
	@echo ""
	@echo "── Step 2/5: Slither on vulnerable + patched ────────────────────"
	-cd demos/bridge/contracts && slither VulnerableBridge.sol --json /tmp/bridge_vuln.json 2>&1 | tail -2
	-cd demos/bridge/contracts && slither PatchedBridge.sol --json /tmp/bridge_patched.json 2>&1 | tail -2
	@echo ""
	@echo "── Step 3/5: Generate certificate ───────────────────────────────"
	cd demos/bridge && $(PARALLAX5) certify parallax.yaml --output output/certificate.json
	@echo ""
	@echo "── Step 4/5: Validate certificate ───────────────────────────────"
	cd demos/bridge && $(PARALLAX5) validate output/certificate.json
	@echo ""
	@echo "── Step 5/5: Registry submission payload ────────────────────────"
	cd demos/bridge && $(PARALLAX5) registry submit output/certificate.json --dry-run
	@echo ""
	@echo "✓ Demo 2 complete. Report: demos/bridge/REPORT.md"

demo-agent:
	@echo "================================================================="
	@echo "  Demo 3: AI-agent runtime gate (A1 + A2 + D5 enforcement)"
	@echo "================================================================="
	@echo ""
	@echo "── Step 1/5: Agent-gate simulator (5 scenarios) ─────────────────"
	cd demos/agent_gate && python3 simulate.py
	@echo ""
	@echo "── Step 2/5: Slither on RuntimeGate ─────────────────────────────"
	-cd demos/agent_gate/contracts && slither RuntimeGate.sol --json /tmp/agent_gate.json 2>&1 | tail -2
	@echo ""
	@echo "── Step 3/5: Generate certificate ───────────────────────────────"
	cd demos/agent_gate && $(PARALLAX5) certify parallax.yaml --output output/certificate.json
	@echo ""
	@echo "── Step 4/5: Validate certificate ───────────────────────────────"
	cd demos/agent_gate && $(PARALLAX5) validate output/certificate.json
	@echo ""
	@echo "── Step 5/5: Registry submission payload ────────────────────────"
	cd demos/agent_gate && $(PARALLAX5) registry submit output/certificate.json --dry-run
	@echo ""
	@echo "✓ Demo 3 complete. Report: demos/agent_gate/REPORT.md"

demo-all: demo-vault demo-bridge demo-agent
	@echo ""
	@echo "================================================================="
	@echo "  All three flagship demos complete."
	@echo "================================================================="
	@echo ""
	@echo "  Reports:"
	@echo "    demos/vault/REPORT.md       (A1 — ERC-4626 inflation attack)"
	@echo "    demos/bridge/REPORT.md      (A3 + A5 — bridge attestation)"
	@echo "    demos/agent_gate/REPORT.md  (A1 + A2 + D5 — AI-agent runtime gate)"
	@echo ""
	@echo "  Certificates:"
	@echo "    demos/vault/output/certificate.json"
	@echo "    demos/bridge/output/certificate.json"
	@echo "    demos/agent_gate/output/certificate.json"
	@echo ""

test:
	@echo "── Compositional theorem suite ──────────────────────────────────"
	$(PY) -m parallax5_coordinator.theorems
	@echo ""
	@echo "── CROPS test suite ─────────────────────────────────────────────"
	$(PY) tests/test_crops.py
	@echo ""
	@echo "── Worked-example certificate validation ────────────────────────"
	$(PARALLAX5) validate examples/certificate_uniswap_v3_core.json

clean:
	rm -f demos/vault/output/certificate.json
	rm -f demos/bridge/output/certificate.json
	rm -f demos/agent_gate/output/certificate.json
	rm -f /tmp/vault_*.json /tmp/bridge_*.json /tmp/agent_gate.json
	@echo "✓ Generated artifacts cleaned"
