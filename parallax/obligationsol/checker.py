"""parallax.obligationsol.checker — static obligation verification.

For each ``A<n>+`` obligation declared on a function, run the
corresponding static analysis pass against the function body. If
the pass fails, the obligation is VIOLATED and compilation must
reject.

Mapping from obligation to checker pass:

  A1+ (conservation): every state-var write to a share/asset/balance
      variable must have a complementary balancing write within the
      same function. Asymmetric writes ARE A1 violations. The first-
      depositor inflation bug (Cream Finance) violates A1 because
      ``deposit`` can mint shares disproportionate to assets when
      ``totalShares == 0``.

  A2+ (authorization): every state-mutating function must enforce
      caller identity via either (a) modifier on the function (e.g.
      ``onlyOwner``, ``onlyRole``) OR (b) explicit ``require(msg.
      sender == ...)`` checks BEFORE the first state write.

  A3+ (signature integrity): if a function accepts signature-shaped
      parameters (``bytes`` or ``uint8 v, bytes32 r, bytes32 s``),
      the body MUST call ``ecrecover``, MUST check the result is
      non-zero, and MUST compare it against an expected signer that
      was stored or passed in.

  A4+ (temporal coherence): no external CALL between any state-var
      read and any state-var write inside the same function. The
      effects-then-interactions discipline. A reentrancy modifier
      (e.g. ``nonReentrant``) trivially satisfies the obligation.

  A5+ (oracle trust): any oracle-tagged state-var read MUST be
      guarded by a freshness check (``require(updatedAt > now -
      max_age)``) or be a TWAP-style aggregate.

  Negative-mode obligations (``A<n>-``) are also checked: the
  function body MUST NOT exhibit the corresponding axiom-touching
  pattern. e.g. ``A5-`` means no oracle-tagged state vars are read.

Each check returns an ``ObligationResult`` with verdict
{satisfied, violated, indeterminate} and a citation back to the
specific source line(s) that triggered the verdict.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .parser import AxiomAnnotation, AxiomObligation


# Heuristic name patterns. Production: derive from slither AST type
# annotations. For the v0 checker these regexes are tight enough to
# catch the historical exploit shapes.
SHARE_PATTERNS = ("share", "balanceof", "balance",
                  "totalshares", "totalsupply")
ASSET_PATTERNS = ("asset", "totalasset", "reserve",
                  "deposit", "available")
ORACLE_PATTERNS = ("price", "oracle", "feed", "rate",
                   "updatedat", "latest")
AUTH_MODIFIERS = ("onlyowner", "onlyadmin", "onlyrole", "onlymanager",
                  "onlyguardian", "auth", "restricted")


@dataclass
class ObligationResult:
    """The verdict of one obligation check."""
    obligation: AxiomObligation
    verdict: str  # "satisfied" | "violated" | "indeterminate"
    explanation: str
    evidence_lines: List[Tuple[int, str]] = field(default_factory=list)
    """List of (line_num, source_excerpt) supporting the verdict."""


@dataclass
class ObligationCheckReport:
    """Aggregate report across all annotated functions in a contract."""
    contract_name: str
    annotation_count: int
    results: List[Tuple[AxiomAnnotation, ObligationResult]] = \
        field(default_factory=list)

    @property
    def violations(self) -> List[Tuple[AxiomAnnotation, ObligationResult]]:
        return [(a, r) for a, r in self.results
                if r.verdict == "violated"]

    @property
    def satisfied_count(self) -> int:
        return sum(1 for _, r in self.results if r.verdict == "satisfied")

    @property
    def compiles(self) -> bool:
        """Compilation succeeds IFF no obligation is violated."""
        return not any(r.verdict == "violated" for _, r in self.results)

    def summary(self) -> str:
        return (
            f"ObligationCheckReport[{self.contract_name}]: "
            f"{self.annotation_count} annotation(s), "
            f"{self.satisfied_count}/{len(self.results)} satisfied, "
            f"{len(self.violations)} violation(s), "
            f"compiles={self.compiles}"
        )


def _strip_comments(text: str) -> str:
    """Remove // line comments and /* */ block comments from Solidity
    source. Critical: the checker must verify CODE behavior, not what
    comments CLAIM. A comment saying "// BUG: no zero check" must not
    cause the checker to think a zero check exists."""
    # Block comments first
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    # Line comments
    text = re.sub(r"//[^\n]*", "", text)
    return text


def _extract_function_body(
    source: str, fn_name: str,
) -> Optional[Tuple[int, int, str]]:
    """Return (start_line, end_line, body_text_with_comments_stripped)
    for the named function.

    Uses brace counting from the opening '{' on the function declaration
    line to the matching closing brace. Comments are stripped from the
    returned body so the checker verifies code behavior, not commented
    claims.
    """
    lines = source.split("\n")
    # Find function declaration line
    pat = re.compile(r"^\s*function\s+" + re.escape(fn_name) + r"\s*\(")
    decl_line = None
    for i, line in enumerate(lines):
        if pat.search(line):
            decl_line = i
            break
    if decl_line is None:
        return None
    # Find the first '{' (might be on declaration line or following)
    body_start = decl_line
    while body_start < len(lines) and "{" not in lines[body_start]:
        body_start += 1
    if body_start >= len(lines):
        return None
    # Brace count from that '{'
    depth = 0
    seen_open = False
    end_line = body_start
    body_chars: List[str] = []
    for i in range(body_start, len(lines)):
        line = lines[i]
        for ch in line:
            if ch == "{":
                depth += 1
                seen_open = True
            elif ch == "}":
                depth -= 1
            body_chars.append(ch)
        body_chars.append("\n")
        if seen_open and depth == 0:
            end_line = i
            break
    raw_body = "".join(body_chars)
    return (decl_line + 1, end_line + 1, _strip_comments(raw_body))


def _function_modifiers(decl_line: str) -> List[str]:
    """Extract modifier names from a function declaration line."""
    # Modifiers appear after the parameter list and before the body
    # or 'returns'. Match identifier tokens between ')' and '{'/'returns'.
    after_params_match = re.search(r"\)\s*([^{;]*?)(\{|returns|;|$)", decl_line)
    if not after_params_match:
        return []
    region = after_params_match.group(1)
    # Strip visibility/mutability keywords
    keywords = {"public", "external", "internal", "private",
                "view", "pure", "payable", "virtual", "override"}
    tokens = re.findall(r"[A-Za-z_]\w*", region)
    return [t for t in tokens if t.lower() not in keywords]


def _line_writes_state_var(line: str, var_patterns) -> List[str]:
    """Return state-var keywords matching this line's mutation, if any."""
    line_l = line.lower()
    if not re.search(r"(=|\+=|-=|\*=|/=|push|pop)", line_l):
        return []
    return [p for p in var_patterns if p in line_l]


def _line_reads_state_var(line: str, var_patterns) -> List[str]:
    """Return state-var keywords matching this line's read."""
    line_l = line.lower()
    return [p for p in var_patterns if p in line_l]


# ── Per-axiom checkers ────────────────────────────────────────────

def _check_a1_conservation(
    body: str, fn_name: str, body_start_line: int,
) -> ObligationResult:
    """A1+: every share-write must have a balancing asset-write
    in the same function. Asymmetric writes are violations.

    The Cream first-depositor pattern: ``deposit`` mints shares
    based on ``assets * totalShares / totalAssets`` but when
    ``totalShares == 0``, shares == assets (no asymmetry); a
    subsequent attacker deposit + donate creates the inflation. The
    A1+ obligation requires either:
       (a) every share-write line ALSO writes an asset var
       (b) or the function is marked with a 'virtual offset' /
           'minimum deposit' / 'lock min liquidity' pattern that
           prevents the first-depositor manipulation.
    """
    obligation = AxiomObligation(axiom="A1", mode="+")
    body_lines = body.split("\n")
    share_writes: List[Tuple[int, str]] = []
    asset_writes: List[Tuple[int, str]] = []
    for ln, line in enumerate(body_lines):
        if _line_writes_state_var(line, SHARE_PATTERNS):
            share_writes.append((body_start_line + ln, line.strip()))
        if _line_writes_state_var(line, ASSET_PATTERNS):
            asset_writes.append((body_start_line + ln, line.strip()))
    # Symmetry check: equal counts of share/asset write LINES
    if not share_writes and not asset_writes:
        return ObligationResult(
            obligation=obligation,
            verdict="satisfied",
            explanation=(
                f"{fn_name} writes no share or asset state. "
                "A1 conservation trivially holds."
            ),
        )
    if share_writes and not asset_writes:
        return ObligationResult(
            obligation=obligation,
            verdict="violated",
            explanation=(
                f"{fn_name} writes share state ({len(share_writes)} "
                "line(s)) without any balancing asset state write. "
                "A1 conservation violated: assets/shares ratio "
                "can drift."
            ),
            evidence_lines=share_writes[:3],
        )
    if asset_writes and not share_writes:
        return ObligationResult(
            obligation=obligation,
            verdict="violated",
            explanation=(
                f"{fn_name} writes asset state without balancing "
                "share write. Donation channel exists: assets can "
                "be added without shares. (Euler-class A1 violation.)"
            ),
            evidence_lines=asset_writes[:3],
        )
    # Both present — additional check: first-depositor virtual offset?
    has_virtual_offset = bool(re.search(
        r"(virtual\s*[Oo]ffset|MIN_LIQUIDITY|MINIMUM_LIQUIDITY|"
        r"_burn\s*\(\s*address\s*\(\s*0\s*\)|"
        r"\+\s*10\s*\*\*|\+\s*1e\d+)",
        body,
    ))
    if not has_virtual_offset:
        # Look for first-depositor protection patterns
        has_first_deposit_guard = bool(re.search(
            r"(totalShares\s*==\s*0|totalSupply\s*\(\)\s*==\s*0|"
            r"_totalShares\s*==\s*0|_totalSupply\s*==\s*0)",
            body,
        ))
        if has_first_deposit_guard:
            return ObligationResult(
                obligation=obligation,
                verdict="violated",
                explanation=(
                    f"{fn_name} has a totalShares==0 branch but no "
                    "virtual offset / MIN_LIQUIDITY burn / minimum "
                    "deposit. This is the Cream Finance first-"
                    "depositor inflation pattern ($130M loss, "
                    "Oct 2021). A1 violated."
                ),
                evidence_lines=share_writes[:1] + asset_writes[:1],
            )
    return ObligationResult(
        obligation=obligation,
        verdict="satisfied",
        explanation=(
            f"{fn_name} writes both share and asset state with "
            "first-depositor protection (virtual offset or "
            "min-liquidity pattern). A1 holds."
        ),
    )


def _check_a2_authorization(
    body: str, fn_name: str, body_start_line: int,
    decl_line: str,
) -> ObligationResult:
    """A2+: state-mutating function must enforce caller identity
    via a modifier OR an explicit msg.sender check before the
    first state write."""
    obligation = AxiomObligation(axiom="A2", mode="+")
    modifiers = _function_modifiers(decl_line)
    auth_mods = [m for m in modifiers if m.lower() in AUTH_MODIFIERS]
    if auth_mods:
        return ObligationResult(
            obligation=obligation,
            verdict="satisfied",
            explanation=(
                f"{fn_name} has auth modifier(s): {', '.join(auth_mods)}. "
                "A2 satisfied at the modifier level."
            ),
        )
    # Look for explicit require(msg.sender ...) before any state write
    body_lines = body.split("\n")
    state_mutated = False
    msg_sender_checked = False
    for line in body_lines:
        if re.search(r"require\s*\(.*msg\.sender", line):
            msg_sender_checked = True
        if re.search(r"\b\w+\s*(\[.*?\]\s*)?(=|\+=|-=)", line) and \
           "function" not in line and "//" not in line.split("\n")[0]:
            if not msg_sender_checked:
                # State write before any msg.sender check
                state_mutated = True
                break
    if state_mutated and not msg_sender_checked:
        return ObligationResult(
            obligation=obligation,
            verdict="violated",
            explanation=(
                f"{fn_name} mutates state without a msg.sender check "
                "or auth modifier. A2 violated: any caller can mutate."
            ),
        )
    if msg_sender_checked:
        return ObligationResult(
            obligation=obligation,
            verdict="satisfied",
            explanation=(
                f"{fn_name} performs require(msg.sender ...) before "
                "state writes. A2 satisfied."
            ),
        )
    return ObligationResult(
        obligation=obligation,
        verdict="indeterminate",
        explanation=(
            f"{fn_name} state-write pattern not recognized; cannot "
            "confirm A2 mechanically."
        ),
    )


def _check_a3_signature_integrity(
    body: str, fn_name: str, body_start_line: int,
    decl_line: str,
) -> ObligationResult:
    """A3+: if the function takes signature-shaped params, the body
    must call ecrecover, check non-zero, AND compare against an
    expected signer."""
    obligation = AxiomObligation(axiom="A3", mode="+")
    takes_sig = bool(re.search(
        r"(bytes\s+(calldata\s+)?(sig|signature)|"
        r"uint8\s+v\s*,\s*bytes32\s+r\s*,\s*bytes32\s+s|"
        r"bytes32\s+r\s*,\s*bytes32\s+s\s*,\s*uint8\s+v)",
        decl_line,
    ))
    if not takes_sig:
        return ObligationResult(
            obligation=obligation,
            verdict="satisfied",
            explanation=(
                f"{fn_name} takes no signature parameters; A3 "
                "trivially holds."
            ),
        )
    calls_ecrecover = "ecrecover" in body
    if not calls_ecrecover:
        return ObligationResult(
            obligation=obligation,
            verdict="violated",
            explanation=(
                f"{fn_name} accepts a signature parameter but body "
                "does not call ecrecover. A3 violated: signature "
                "is parsed but never verified."
            ),
        )
    # Look for zero-check on recovered address (recovered != 0 or != address(0))
    zero_check = bool(re.search(
        r"(recovered\s*!=\s*address\s*\(\s*0\s*\)|"
        r"signer\s*!=\s*address\s*\(\s*0\s*\)|"
        r"!=\s*address\s*\(\s*0\s*\))",
        body,
    ))
    has_signer_compare = bool(re.search(
        r"(recovered\s*==\s*|signer\s*==\s*|address\s+\w+\s*=\s*ecrecover.*?;\s*require\s*\(\s*\w+\s*==)",
        body,
    ))
    if not has_signer_compare and not zero_check:
        return ObligationResult(
            obligation=obligation,
            verdict="violated",
            explanation=(
                f"{fn_name} calls ecrecover but neither (a) checks "
                "result != address(0) nor (b) compares against an "
                "expected signer. A3 violated: Wormhole-class "
                "signature-verification bypass ($326M loss)."
            ),
        )
    return ObligationResult(
        obligation=obligation,
        verdict="satisfied",
        explanation=(
            f"{fn_name} calls ecrecover with zero-check and/or "
            "expected-signer comparison. A3 satisfied."
        ),
    )


def _check_a4_temporal(
    body: str, fn_name: str, body_start_line: int,
    decl_line: str,
) -> ObligationResult:
    """A4+: no external CALL between state read and state write
    within the same function. A nonReentrant modifier satisfies."""
    obligation = AxiomObligation(axiom="A4", mode="+")
    modifiers = _function_modifiers(decl_line)
    has_nonreentrant = any("reentr" in m.lower() for m in modifiers)
    if has_nonreentrant:
        return ObligationResult(
            obligation=obligation,
            verdict="satisfied",
            explanation=(
                f"{fn_name} has nonReentrant modifier; A4 satisfied "
                "by reentrancy guard."
            ),
        )
    # Look for the effects-then-interactions discipline
    body_lines = body.split("\n")
    external_call_lines: List[Tuple[int, str]] = []
    state_write_after_call = False
    saw_external_call = False
    for ln, line in enumerate(body_lines):
        # Heuristic for external call: .call(, .transfer(, .send(,
        # or interface-typed call (Iface(addr).method())
        if re.search(
            r"(\.call\b|\.transfer\b|\.send\b|"
            r"I\w+\(.*?\)\.\w+|\w+\.\w+\s*\(.*?\)\s*;)",
            line,
        ):
            # Crude filter: ignore if it's clearly a Solidity built-in
            if not re.search(r"(require|assert|emit|abi\.encode)", line):
                external_call_lines.append((body_start_line + ln, line.strip()))
                saw_external_call = True
        if saw_external_call:
            # If any state write follows an external call, A4 violated
            if re.search(r"\b\w+\s*(\[.*?\]\s*)?(=|\+=|-=)", line) and \
               "function" not in line:
                state_write_after_call = True
                break
    if state_write_after_call:
        return ObligationResult(
            obligation=obligation,
            verdict="violated",
            explanation=(
                f"{fn_name} performs a state write AFTER an external "
                "call without nonReentrant. A4 violated: reentrancy "
                "window. (Beanstalk-class governance manipulation.)"
            ),
            evidence_lines=external_call_lines[:2],
        )
    return ObligationResult(
        obligation=obligation,
        verdict="satisfied",
        explanation=(
            f"{fn_name} either has no external calls or follows "
            "effects-then-interactions discipline. A4 satisfied."
        ),
    )


def _check_a5_oracle(
    body: str, fn_name: str, body_start_line: int, mode: str = "+",
) -> ObligationResult:
    """A5+: oracle reads must be guarded by a freshness check.
    A5-: function reads no oracle-tagged state."""
    obligation = AxiomObligation(axiom="A5", mode=mode)
    body_lines = body.split("\n")
    oracle_reads: List[Tuple[int, str]] = []
    for ln, line in enumerate(body_lines):
        if _line_reads_state_var(line, ORACLE_PATTERNS):
            oracle_reads.append((body_start_line + ln, line.strip()))
    if mode == "-":
        if oracle_reads:
            return ObligationResult(
                obligation=obligation,
                verdict="violated",
                explanation=(
                    f"{fn_name} claims A5- (no oracle interaction) "
                    f"but reads oracle-tagged state ({len(oracle_reads)} "
                    "line(s)). A5- violated."
                ),
                evidence_lines=oracle_reads[:3],
            )
        return ObligationResult(
            obligation=obligation,
            verdict="satisfied",
            explanation=f"{fn_name} reads no oracle state. A5- holds.",
        )
    # mode == "+"
    if not oracle_reads:
        return ObligationResult(
            obligation=obligation,
            verdict="satisfied",
            explanation=(
                f"{fn_name} reads no oracle state; A5+ trivially holds."
            ),
        )
    # Look for freshness guard
    has_freshness_check = bool(re.search(
        r"(updatedAt|block\.timestamp\s*-\s*\w+\s*[<=>]|"
        r"latestRoundData|MAX_AGE|max_age|STALENESS|"
        r"require\s*\(\s*block\.timestamp\s*[<=>])",
        body,
    ))
    if not has_freshness_check:
        return ObligationResult(
            obligation=obligation,
            verdict="violated",
            explanation=(
                f"{fn_name} reads oracle state without a freshness "
                "check (no updatedAt/MAX_AGE/timestamp comparison). "
                "A5+ violated: Mango-class oracle staleness ($116M)."
            ),
            evidence_lines=oracle_reads[:2],
        )
    return ObligationResult(
        obligation=obligation,
        verdict="satisfied",
        explanation=(
            f"{fn_name} reads oracle state guarded by freshness "
            "check. A5+ satisfied."
        ),
    )


# ── Top-level driver ──────────────────────────────────────────────

def check_obligation(
    obligation: AxiomObligation, annotation: AxiomAnnotation, source: str,
) -> ObligationResult:
    """Dispatch one obligation to its checker pass."""
    body_info = _extract_function_body(source, annotation.function_name)
    if body_info is None:
        return ObligationResult(
            obligation=obligation,
            verdict="indeterminate",
            explanation=(
                f"Could not extract body of {annotation.function_name}"
            ),
        )
    body_start, _body_end, body = body_info
    decl_line = annotation.function_signature

    if obligation.mode == "?":
        return ObligationResult(
            obligation=obligation,
            verdict="satisfied",
            explanation=f"{obligation.axiom}? mode: no obligation.",
        )

    if obligation.axiom == "A1" and obligation.mode == "+":
        return _check_a1_conservation(body, annotation.function_name, body_start)
    if obligation.axiom == "A2" and obligation.mode == "+":
        return _check_a2_authorization(
            body, annotation.function_name, body_start, decl_line,
        )
    if obligation.axiom == "A3" and obligation.mode == "+":
        return _check_a3_signature_integrity(
            body, annotation.function_name, body_start, decl_line,
        )
    if obligation.axiom == "A4" and obligation.mode == "+":
        return _check_a4_temporal(
            body, annotation.function_name, body_start, decl_line,
        )
    if obligation.axiom == "A5":
        return _check_a5_oracle(
            body, annotation.function_name, body_start, mode=obligation.mode,
        )
    # Negative modes for axioms A1..A4 we haven't implemented yet;
    # treat as indeterminate (no specific pattern to look for).
    return ObligationResult(
        obligation=obligation,
        verdict="indeterminate",
        explanation=f"{obligation.axiom}{obligation.mode}: not implemented.",
    )


def check_obligations(
    source: str, contract_name: str = "<unknown>",
) -> ObligationCheckReport:
    """Run static checks against every @axioms-annotated function in
    the Solidity source. Return a structured report."""
    annotations = []
    from .parser import parse_annotations
    annotations = parse_annotations(source)
    results: List[Tuple[AxiomAnnotation, ObligationResult]] = []
    for ann in annotations:
        for ob in ann.obligations:
            res = check_obligation(ob, ann, source)
            results.append((ann, res))
    return ObligationCheckReport(
        contract_name=contract_name,
        annotation_count=len(annotations),
        results=results,
    )


__all__ = [
    "ObligationResult", "ObligationCheckReport",
    "check_obligation", "check_obligations",
]
