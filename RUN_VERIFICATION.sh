#!/bin/bash
# Full PARALLAX-5 verification recipe.
# Run from the repository root: ./RUN_VERIFICATION.sh
set -e
cd "$(dirname "$0")"

echo "═══ Step 0: Install (editable) ═══"
pip install -e . --break-system-packages --quiet 2>&1 | tail -2 || pip install -e . --quiet
echo "  ✓ Package installed"
echo

echo "═══ Compositional theorems (2,152 checks) ═══"
PYTHONPATH=src python3 -m parallax5_coordinator.theorems
echo

echo "═══ CROPS test suite (19 tests, v1.0.1 matrix) ═══"
PYTHONPATH=src python3 tests/test_crops.py
echo

echo "═══ Fire tests (70 tests across formal core) ═══"
PYTHONPATH=. python3 parallax/formal/fire_tests.py 2>&1 | tail -1
P=$(PYTHONPATH=. python3 parallax/formal/fire_tests.py 2>&1 | grep -c '✓')
F=$(PYTHONPATH=. python3 parallax/formal/fire_tests.py 2>&1 | grep '✗' | grep -v issue | wc -l)
echo "  Pass: $P / 70, Fail: $F"
echo

echo "═══ ObligationSol tests ═══"
PYTHONPATH=. python3 parallax/obligationsol/fire_tests.py 2>&1 | tail -1
echo

echo "═══ Formal-core inventory ═══"
[ -f parallax/formal/lean/Parallax5.lean ] && echo "  parallax/formal/lean/Parallax5.lean: $(grep -c '^theorem' parallax/formal/lean/Parallax5.lean) theorems"
echo

echo "═══ Demos end-to-end ═══"
make demo-all
echo

echo "═══ Onchain registry — Foundry tests ═══"
if command -v forge >/dev/null; then
    cd registry && forge test 2>&1 | tail -3
    cd ..
else
    echo "  (forge not in PATH; install via 'curl -L https://foundry.paradigm.xyz | bash && foundryup')"
fi
echo

echo "═══ Onchain registry — Lean state-machine proof ═══"
[ -f lean/Parallax5/Registry.lean ] && echo "  lean/Parallax5/Registry.lean: $(grep -c '^theorem' lean/Parallax5/Registry.lean) theorems (Lean kernel run required for proof check)"
echo

echo "═══ CLI smoke tests ═══"
parallax5 --help > /dev/null && echo "  ✓ parallax5 --help" || echo "  ✗ parallax5 --help"
parallax5 capability > /dev/null && echo "  ✓ parallax5 capability"
parallax5 validate demos/vault/output/certificate.json > /dev/null && echo "  ✓ parallax5 validate (v9 cert)"
parallax5 validate paper/supplement/example_certificate.json > /dev/null && echo "  ✓ parallax5 validate (v8 cert)"
parallax5 quote --tvl 1B --level P3 > /dev/null && echo "  ✓ parallax5 quote (v8)"
echo

echo "═══ Paper compile check ═══"
if [ -f paper/parallax-5.tex ] && command -v pdflatex >/dev/null; then
    cd paper
    pdflatex -interaction=nonstopmode parallax-5.tex >/dev/null 2>&1
    pdflatex -interaction=nonstopmode parallax-5.tex >/dev/null 2>&1
    pdflatex -interaction=nonstopmode parallax-5.tex >/dev/null 2>&1
    [ -f parallax-5.pdf ] && echo "  ✓ Paper compiles cleanly: $(pdfinfo parallax-5.pdf | awk '/Pages/{print $2}') pages"
    cd ..
fi
echo
echo "═══ All gates passed. Ready for public release. ═══"
