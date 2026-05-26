#!/usr/bin/env bash
# Verify the halmos symbolic-execution proofs over the substrate's
# Solidity contracts. Each contract has a vulnerable variant
# (expected: counterexample FAIL) and a hardened variant
# (expected: PASS over all symbolic paths).
set -e
cd "$(dirname "$0")"

if ! command -v halmos &>/dev/null; then
    echo "✗ halmos not in PATH"
    exit 1
fi

# Set up a temp foundry workspace mirroring the substrate layout
WORKDIR=$(mktemp -d)
mkdir -p "$WORKDIR/src" "$WORKDIR/test"
cp CreamVuln.sol CreamHardened.sol Bridge.sol Oracle.sol SolvPattern.sol "$WORKDIR/src/"
cp CreamA1.t.sol BridgeA3.t.sol OracleA5.t.sol SolvA4.t.sol "$WORKDIR/test/"
cat > "$WORKDIR/foundry.toml" << EOF
[profile.default]
src = "src"
test = "test"
out = "out"
ast = true
build_info = true
extra_output = ["storageLayout"]
EOF

cd "$WORKDIR"
forge build 2>&1 | tail -3
echo
echo "── A1 vulnerable: expect FAIL with counterexample ──"
halmos --contract A1VulnerableTest --function check_ 2>&1 | grep -E "FAIL|PASS|Counterexample"
echo "── A1 hardened: expect PASS ──"
halmos --contract A1HardenedTest --function check_ 2>&1 | grep -E "FAIL|PASS"
echo "── A3 vulnerable: expect FAIL ──"
halmos --contract A3VulnerableTest --function check_ 2>&1 | grep -E "FAIL|PASS|Counterexample"
echo "── A3 hardened: expect PASS ──"
halmos --contract A3HardenedTest --function check_ 2>&1 | grep -E "FAIL|PASS"
echo "── A5 vulnerable: expect FAIL ──"
halmos --contract A5VulnerableTest --function check_ 2>&1 | grep -E "FAIL|PASS|Counterexample"
echo "── A5 hardened: expect PASS ──"
halmos --contract A5HardenedTest --function check_ 2>&1 | grep -E "FAIL|PASS"
echo "── Solv cross-function reentrancy: expect FAIL ──"
halmos --contract A4VulnerableSolvTest --function check_ 2>&1 | grep -E "FAIL|PASS|Counterexample"
echo "── Solv hardened: expect PASS ──"
halmos --contract A4HardenedSolvTest --function check_ 2>&1 | grep -E "FAIL|PASS"

rm -rf "$WORKDIR"
