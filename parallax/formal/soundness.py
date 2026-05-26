"""parallax.formal.soundness — ObligationSol vs Z3 cross-verification.

ObligationSol uses regex-based pattern matching against function bodies.
Z3 uses SMT-level reasoning over abstract state machines. halmos uses
symbolic execution over real EVM bytecode.

These three should agree on the same source fixtures. Where they
agree, ObligationSol's lightweight regex checker is a sound (computable)
approximation of the deeper formal models.

Where they DISAGREE, the regex checker has either a false positive
(rejects code that SMT proves safe) or a false negative (accepts
code that SMT proves vulnerable). Both are bugs in the regex
checker that the cross-verification surfaces.

This module mechanizes the agreement check:

  For each (axiom, source-fixture) pair:
      obligationsol_verdict = check_obligations(source).compiles
      smt_verdict      = (corresponding Z3 query returns UNSAT)
      assert obligationsol_verdict == smt_verdict

If any pair disagrees, the cross-verification surfaces the gap.
This is the ObligationSol equivalent of "type system soundness with
respect to the underlying semantics."
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from parallax.obligationsol import check_obligations
from .z3_axioms import (
    deposit_vulnerable, deposit_hardened,
    can_violate_a1_first_depositor,
    can_violate_a5_no_freshness_check,
    cannot_violate_a5_with_freshness_check,
    can_violate_a3_no_zero_check,
    cannot_violate_a3_with_both_checks,
)


@dataclass
class CrossVerification:
    """Result of a cross-verification check."""
    name: str
    axiom_claim: str
    obligationsol_compiles: bool
    z3_property_holds: bool
    agree: bool
    explanation: str


# Source fixtures — same as in the ObligationSol fire tests, paired with
# the corresponding Z3 model query

CREAM_VULN_SRC = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CreamVuln {
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

CREAM_HARDENED_SRC = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract CreamHardened {
    uint256 public totalShares;
    uint256 public totalAssets;
    uint256 public constant MIN_LIQUIDITY = 1000;
    mapping(address => uint256) public balanceOf;
    /// @axioms A1+ A4+
    function deposit(uint256 assets) external returns (uint256 shares) {
        if (totalShares == 0) {
            require(assets > MIN_LIQUIDITY * MIN_LIQUIDITY);
            shares = assets - MIN_LIQUIDITY;
            balanceOf[address(0)] = MIN_LIQUIDITY;
            totalShares = shares + MIN_LIQUIDITY;
        } else {
            shares = assets * totalShares / totalAssets;
            totalShares += shares;
        }
        balanceOf[msg.sender] += shares;
        totalAssets += assets;
    }
}"""

WORMHOLE_VULN_SRC = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract WormholeVuln {
    mapping(uint256 => bool) public processed;
    /// @axioms A3+
    function processVAA(bytes32 h, uint8 v, bytes32 r, bytes32 s, uint256 id) external {
        ecrecover(h, v, r, s);
        processed[id] = true;
    }
}"""

WORMHOLE_HARDENED_SRC = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract WormholeHardened {
    address public expectedSigner;
    mapping(uint256 => bool) public processed;
    /// @axioms A3+
    function processVAA(bytes32 h, uint8 v, bytes32 r, bytes32 s, uint256 id) external {
        address recovered = ecrecover(h, v, r, s);
        require(recovered != address(0));
        require(recovered == expectedSigner);
        processed[id] = true;
    }
}"""

MANGO_VULN_SRC = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract MangoVuln {
    uint256 public price;
    mapping(address => uint256) public collateral;
    /// @axioms A5+
    function liquidate(address user) external {
        if (collateral[user] * price < 1000) { collateral[user] = 0; }
    }
}"""

MANGO_HARDENED_SRC = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract MangoHardened {
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


def cross_verify_obligationsol_vs_z3() -> List[CrossVerification]:
    """For each fixture/axiom pair, compare ObligationSol's verdict to
    the Z3 model's verdict. The two should agree."""

    fixtures: List[Tuple[str, str, str, str, str]] = [
        # (name, source, claimed_axiom, smt_query_kind, expected_agreement)
        ("Cream vuln (A1)",     CREAM_VULN_SRC,     "A1", "A1_vuln",     "both reject"),
        ("Cream hardened (A1)", CREAM_HARDENED_SRC, "A1", "A1_hardened", "both accept"),
        ("Wormhole vuln (A3)",  WORMHOLE_VULN_SRC,  "A3", "A3_vuln",     "both reject"),
        ("Wormhole hardened (A3)", WORMHOLE_HARDENED_SRC, "A3", "A3_hardened", "both accept"),
        ("Mango vuln (A5)",     MANGO_VULN_SRC,     "A5", "A5_vuln",     "both reject"),
        ("Mango hardened (A5)", MANGO_HARDENED_SRC, "A5", "A5_hardened", "both accept"),
    ]

    results = []
    for name, source, axiom, query_kind, expected in fixtures:
        report = check_obligations(source, contract_name=name)
        ax_compiles = report.compiles

        # Run the corresponding Z3 query
        if query_kind == "A1_vuln":
            # Z3 says: counter-witness exists (so A1+ does NOT hold)
            z3_property_holds = (
                can_violate_a1_first_depositor(deposit_vulnerable) is None
            )
        elif query_kind == "A1_hardened":
            # Z3 says: no counter-witness exists (so A1+ holds)
            z3_property_holds = (
                can_violate_a1_first_depositor(
                    lambda pre, amt, post: deposit_hardened(
                        pre, amt, post, min_liquidity=1000,
                    )
                ) is None
            )
        elif query_kind == "A3_vuln":
            z3_property_holds = (
                can_violate_a3_no_zero_check() is None
            )
        elif query_kind == "A3_hardened":
            z3_property_holds = cannot_violate_a3_with_both_checks()
        elif query_kind == "A5_vuln":
            z3_property_holds = (
                can_violate_a5_no_freshness_check() is None
            )
        elif query_kind == "A5_hardened":
            z3_property_holds = cannot_violate_a5_with_freshness_check()
        else:
            z3_property_holds = False

        # The two verdicts should match: both reject (ax_compiles=False,
        # z3_property_holds=False) or both accept.
        agree = (ax_compiles == z3_property_holds)
        explanation = (
            f"ObligationSol compiles={ax_compiles}; Z3 axiom holds={z3_property_holds}"
        )
        results.append(CrossVerification(
            name=name, axiom_claim=axiom,
            obligationsol_compiles=ax_compiles,
            z3_property_holds=z3_property_holds,
            agree=agree, explanation=explanation,
        ))
    return results


__all__ = ["CrossVerification", "cross_verify_obligationsol_vs_z3"]
