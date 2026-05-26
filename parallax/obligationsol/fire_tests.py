"""parallax.obligationsol.fire_tests — ObligationSol fire tests.

Validates that the type system rejects historical exploits at
compile-time and accepts hardened equivalents.
"""
from __future__ import annotations

import sys
import time

from parallax.obligationsol import check_obligations, parse_annotations


# Source fixtures — pre-built so each test is self-contained.

CREAM_VULN = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CreamVault {
    uint256 public totalShares;
    uint256 public totalAssets;
    mapping(address => uint256) public balanceOf;
    /// @axioms A1+ A4+
    function deposit(uint256 assets) external returns (uint256 shares) {
        if (totalShares == 0) { shares = assets; }
        else { shares = assets * totalShares / totalAssets; }
        balanceOf[msg.sender] += shares;
        totalShares += shares;
        totalAssets += assets;
    }
}"""

WORMHOLE_VULN = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract WormholeBridge {
    mapping(uint256 => bool) public processedVAAs;
    /// @axioms A3+
    function processVAA(bytes32 h, uint8 v, bytes32 r, bytes32 s, uint256 id) external {
        address signer = ecrecover(h, v, r, s);
        processedVAAs[id] = true;
    }
}"""

MANGO_VULN = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract MangoPerp {
    uint256 public price;
    mapping(address => uint256) public collateral;
    /// @axioms A5+
    function liquidate(address user) external {
        if (collateral[user] * price < 1000) { collateral[user] = 0; }
    }
}"""

SAFE_BRIDGE = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract HardenedBridge {
    address public expectedSigner;
    mapping(uint256 => bool) public processedVAAs;
    /// @axioms A3+
    function processVAA(bytes32 h, uint8 v, bytes32 r, bytes32 s, uint256 id) external {
        address recovered = ecrecover(h, v, r, s);
        require(recovered != address(0));
        require(recovered == expectedSigner);
        processedVAAs[id] = true;
    }
}"""

SAFE_LENDER = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract HardenedLender {
    uint256 public price;
    uint256 public updatedAt;
    uint256 public constant MAX_AGE = 1800;
    mapping(address => uint256) public collateral;
    /// @axioms A5+
    function liquidate(address user) external {
        require(block.timestamp <= updatedAt + MAX_AGE);
        if (collateral[user] * price < 1000) { collateral[user] = 0; }
    }
}"""


# ─── Parser tests ──────────────────────────────────────────────────

def test_parser_extracts_axioms_annotation():
    """@axioms A1+ A4+ parses to two AxiomObligations."""
    anns = parse_annotations(CREAM_VULN)
    assert len(anns) == 1
    ann = anns[0]
    assert ann.function_name == "deposit"
    obs = {(o.axiom, o.mode) for o in ann.obligations}
    assert obs == {("A1", "+"), ("A4", "+")}


def test_parser_skips_unannotated_functions():
    """Functions without @axioms are not included."""
    src = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract X {
    function noAnnotation() external {}
    /// @axioms A1+
    function withAnnotation() external {}
}"""
    anns = parse_annotations(src)
    assert len(anns) == 1
    assert anns[0].function_name == "withAnnotation"


def test_parser_handles_invalid_obligations():
    """Bogus tokens are silently dropped; valid ones still parsed."""
    src = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract X {
    /// @axioms A1+ A99+ Q3? A5-
    function f() external {}
}"""
    anns = parse_annotations(src)
    assert len(anns) == 1
    obs = {(o.axiom, o.mode) for o in anns[0].obligations}
    assert obs == {("A1", "+"), ("A5", "-")}


# ─── Compile-time rejection of historical exploits ────────────────

def test_cream_first_depositor_rejected():
    """The Cream Finance $130M inflation source rejects under A1+."""
    rep = check_obligations(CREAM_VULN, "Cream")
    assert not rep.compiles, "Cream-style source must be rejected"
    a1_results = [r for _, r in rep.results if r.obligation.axiom == "A1"]
    assert any(r.verdict == "violated" for r in a1_results), (
        "Expected an A1+ violation on the first-depositor pattern"
    )


def test_wormhole_signature_bypass_rejected():
    """The Wormhole $326M signature-bypass source rejects under A3+."""
    rep = check_obligations(WORMHOLE_VULN, "Wormhole")
    assert not rep.compiles, "Wormhole-style source must be rejected"
    a3_results = [r for _, r in rep.results if r.obligation.axiom == "A3"]
    assert any(r.verdict == "violated" for r in a3_results)


def test_mango_oracle_staleness_rejected():
    """The Mango $116M oracle-staleness source rejects under A5+."""
    rep = check_obligations(MANGO_VULN, "Mango")
    assert not rep.compiles, "Mango-style source must be rejected"
    a5_results = [r for _, r in rep.results if r.obligation.axiom == "A5"]
    assert any(r.verdict == "violated" for r in a5_results)


def test_hardened_bridge_accepted():
    """A bridge with zero-check + signer-check passes A3+."""
    rep = check_obligations(SAFE_BRIDGE, "SafeBridge")
    assert rep.compiles, "Hardened bridge must compile under A3+"


def test_hardened_lender_accepted():
    """A lender with freshness check passes A5+."""
    rep = check_obligations(SAFE_LENDER, "SafeLender")
    assert rep.compiles, "Hardened lender must compile under A5+"


def test_comments_do_not_influence_verdict():
    """A comment claiming a check doesn't make the check exist.

    Regression test: an earlier version of the checker treated text
    inside `// BUG: signer != address(0)` as a real zero-check, which
    would let the Wormhole vuln slip through.
    """
    src = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract Tricky {
    mapping(uint256 => bool) public processed;
    /// @axioms A3+
    function process(bytes32 h, uint8 v, bytes32 r, bytes32 s, uint256 id) external {
        address signer = ecrecover(h, v, r, s);
        // BUG: this comment says signer != address(0) but the code does not check
        processed[id] = true;
    }
}"""
    rep = check_obligations(src, "Tricky")
    assert not rep.compiles, "Comment text must not satisfy A3 check"


def test_negative_obligation_a5_minus():
    """A5- on a function that reads oracle state is a violation."""
    src = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract Liar {
    uint256 public price;
    /// @axioms A5-
    function fakeNonOracleFn() external view returns (uint256) {
        return price;
    }
}"""
    rep = check_obligations(src, "Liar")
    assert not rep.compiles, "A5- claim must be checked against actual oracle reads"


# ─── Test runner ──────────────────────────────────────────────────

ALL_TESTS = [
    test_parser_extracts_axioms_annotation,
    test_parser_skips_unannotated_functions,
    test_parser_handles_invalid_obligations,
    test_cream_first_depositor_rejected,
    test_wormhole_signature_bypass_rejected,
    test_mango_oracle_staleness_rejected,
    test_hardened_bridge_accepted,
    test_hardened_lender_accepted,
    test_comments_do_not_influence_verdict,
    test_negative_obligation_a5_minus,
]


def run_all() -> int:
    print(f"ObligationSol fire tests: {len(ALL_TESTS)}")
    failed = []
    t0 = time.time()
    for test in ALL_TESTS:
        t = time.time()
        try:
            test()
            print(f"  ✓ {test.__name__}  ({time.time()-t:.2f}s)")
        except Exception as e:
            print(f"  ✗ {test.__name__}: {type(e).__name__}: {e}")
            failed.append(test.__name__)
    print(f"total: {time.time()-t0:.2f}s")
    if failed:
        print(f"FAILED: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
