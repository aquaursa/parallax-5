"""parallax.obligationsol.parser — extract @axioms annotations from Solidity.

Annotation grammar:
    /// @axioms <obligation> [<obligation> ...]
    /// [optional rationale lines]
    function fn_name(...) {{ ... }}

Each obligation has form A<n><mode> where:
    n ∈ {1..5}        axiom number
    mode ∈ {+, -, ?}  obligation strength
        + = must satisfy (proof obligation; checker verifies)
        - = explicitly does not touch (negative claim; checker verifies absence)
        ? = unconstrained (no checker pass; explicit lack of claim)

Examples:
    /// @axioms A1+ A4+ A5-
    /// @axioms A2+ A3+
    /// @axioms A1? A2-
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


VALID_AXIOMS = {"A1", "A2", "A3", "A4", "A5"}
VALID_MODES = {"+", "-", "?"}


@dataclass
class AxiomObligation:
    """A single axiom obligation declared by a function."""
    axiom: str              # "A1" .. "A5"
    mode: str               # "+", "-", or "?"

    def __str__(self):
        return f"{self.axiom}{self.mode}"


@dataclass
class AxiomAnnotation:
    """All obligations declared on a single function."""
    function_name: str
    function_signature: str  # full declaration line (for diagnostics)
    obligations: List[AxiomObligation] = field(default_factory=list)
    rationale_lines: List[str] = field(default_factory=list)
    source_line_number: int = 0

    @property
    def positive_axioms(self) -> List[str]:
        """Axioms with mode '+': proof obligations."""
        return [o.axiom for o in self.obligations if o.mode == "+"]

    @property
    def negative_axioms(self) -> List[str]:
        """Axioms with mode '-': explicit non-interaction claims."""
        return [o.axiom for o in self.obligations if o.mode == "-"]


# Match a function declaration line. Solidity functions can be on
# multiple lines, but for ObligationSol we require the @axioms tag be
# directly above the `function` keyword.
_FN_PATTERN = re.compile(
    r"^\s*function\s+(\w+)\s*\(",
    re.MULTILINE,
)
_AXIOMS_LINE = re.compile(r"^\s*///\s*@axioms\s+(.+)$")
_NATSPEC_CONT = re.compile(r"^\s*///\s*(.+)$")


def _parse_obligation_token(token: str) -> Optional[AxiomObligation]:
    """Parse a single obligation token like ``A1+`` or ``A2?``."""
    token = token.strip()
    if len(token) != 3:
        return None
    axiom = token[:2]
    mode = token[2]
    if axiom not in VALID_AXIOMS or mode not in VALID_MODES:
        return None
    return AxiomObligation(axiom=axiom, mode=mode)


def parse_annotations(source: str) -> List[AxiomAnnotation]:
    """Extract all @axioms annotations from Solidity source.

    For each function preceded (in the surrounding NatSpec block) by
    an ``/// @axioms`` line, produce an :class:`AxiomAnnotation`.

    Functions WITHOUT an @axioms annotation are skipped (they're
    untyped from the substrate's perspective; checker treats them as
    unsafe legacy code).
    """
    annotations: List[AxiomAnnotation] = []
    lines = source.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        # Look for a function declaration
        m = re.search(r"^\s*function\s+(\w+)\s*\(", line)
        if not m:
            i += 1
            continue
        fn_name = m.group(1)
        fn_line_num = i + 1  # 1-indexed for human display
        # Walk backwards through NatSpec lines looking for @axioms
        nat_start = i - 1
        axiom_tokens: List[str] = []
        rationale: List[str] = []
        seen_axioms = False
        while nat_start >= 0:
            nat_line = lines[nat_start].strip()
            if not nat_line.startswith("///"):
                # End of NatSpec block
                break
            axm = _AXIOMS_LINE.match(lines[nat_start])
            if axm:
                axiom_tokens = axm.group(1).split()
                seen_axioms = True
                nat_start -= 1
                continue
            # Otherwise it's a rationale line; accumulate
            cont = _NATSPEC_CONT.match(lines[nat_start])
            if cont:
                rationale.insert(0, cont.group(1).strip())
            nat_start -= 1
        if not seen_axioms:
            i += 1
            continue
        # Parse obligations
        parsed = [_parse_obligation_token(t) for t in axiom_tokens]
        parsed = [p for p in parsed if p is not None]
        if not parsed:
            i += 1
            continue
        annotations.append(AxiomAnnotation(
            function_name=fn_name,
            function_signature=line.strip(),
            obligations=parsed,
            rationale_lines=rationale,
            source_line_number=fn_line_num,
        ))
        i += 1
    return annotations


__all__ = [
    "VALID_AXIOMS", "VALID_MODES",
    "AxiomObligation", "AxiomAnnotation", "parse_annotations",
]
