"""parallax.obligationsol — obligation-typed Solidity.

The substrate's categorical move: a Solidity dialect where the 5
AXIOM properties are enforced at COMPILE TIME, not at audit time.

The intuition: Rust's borrow checker doesn't catch memory bugs; it
makes memory bugs IMPOSSIBLE TO WRITE. ObligationSol does the same for
DeFi vulnerabilities. Functions declare their obligations via
``@axioms`` annotations; the static checker verifies the function
body satisfies those obligations or REJECTS COMPILATION.

Annotation syntax (NatSpec-style):

    /// @axioms A1+ A4+ A5-
    /// A1+: this function preserves Σ assets = Σ shares × ppfs
    /// A4+: state mutations are atomic per call (no external calls
    ///      between state read and state write)
    /// A5-: this function does not consume oracle data
    function deposit(uint256 assets) external returns (uint256 shares) {
        ...
    }

Obligation grammar:
    A<n>+   the function MUST preserve axiom <n>
    A<n>-   the function does NOT touch axiom <n>
    A<n>?   the function may interact with axiom <n>; no obligation

The checker maps each ``A<n>+`` claim to a static analysis pass:

    A1+ (conservation): every state-var write to a "share/asset" var
        must have a matching balancing write to a complementary var.
        Asymmetric writes are A1 violations.

    A2+ (authorization): every state-mutating function must be either
        (a) gated on an explicit msg.sender check or modifier, OR
        (b) tagged as ``A2-`` (no authorization implications).

    A3+ (signature integrity): if the function takes a signature, it
        MUST call ``ecrecover`` AND check the recovered address is
        not zero AND check it against an expected signer.

    A4+ (temporal coherence): no external CALL between state-var
        READ and state-var WRITE within the same function (the
        effects-then-interactions checker). Reentrancy guard satisfies.

    A5+ (oracle trust): any oracle-tagged state var read must have a
        freshness check (``updatedAt`` comparison) or a manipulability
        bound check (TWAP-like).

The checker emits OBLIGATION violations that the developer must
either fix (change the code) or weaken (relax the annotation, e.g.
``A1+`` → ``A1?``). The result is a substrate where claimed safety
properties are MECHANICALLY GUARANTEED, not asserted by audit.

This is what transforms PARALLAX from "audit tool" to "compiler for
safe DeFi". Cream Finance's first-depositor inflation, Beanstalk's
flash-governance, Euler's donate+self-liquidate — every one of those
exploits would have been REJECTED at compile time by an ObligationSol
@axioms A1+ / A4+ / A1+ A2+ annotation respectively.
"""
from .parser import AxiomAnnotation, AxiomObligation, parse_annotations
from .checker import (
    ObligationResult, ObligationCheckReport, check_obligations,
)
from .cli import check_file

__all__ = [
    "AxiomAnnotation", "AxiomObligation", "parse_annotations",
    "ObligationResult", "ObligationCheckReport", "check_obligations",
    "check_file",
]
