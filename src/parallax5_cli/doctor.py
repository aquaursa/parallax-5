"""Diagnose what PARALLAX-5 level a repo qualifies for."""
from __future__ import annotations
import shutil
from pathlib import Path


def diagnose(root: Path) -> dict:
    """Inspect the repo and recommend a level + next steps."""
    sol_files = list(root.rglob("*.sol"))
    # Exclude common dependency dirs
    excluded = {"node_modules", "lib", ".git", "out", "cache", "artifacts"}
    sol_files = [p for p in sol_files
                 if set(p.relative_to(root).parts).isdisjoint(excluded)]

    tools = {
        "Slither (static detectors → P2)": bool(shutil.which("slither")),
        "halmos (symbolic execution → P3)": bool(shutil.which("halmos")),
        "Certora (rule verification → P4)": bool(shutil.which("certoraRun")),
        "Lean 4 (theorem proving → P4)": bool(shutil.which("lean")),
        "Foundry (test framework)": bool(shutil.which("forge")),
        "Z3 (SMT solver)": bool(shutil.which("z3")),
        "CVC5 (SMT solver — cross-validation)": bool(shutil.which("cvc5")),
        "Yices2 (SMT solver — cross-validation)": bool(shutil.which("yices-smt2")),
    }

    # Estimate level
    if not sol_files:
        level = "P0"
        next_level = "P1"
        steps = [
            "Add Solidity contracts under contracts/ or src/",
            "Run `parallax5 init --level P1` to author a baseline certificate",
        ]
    elif tools["Slither (static detectors → P2)"]:
        level = "P2"
        next_level = "P3"
        steps = [
            "Add halmos test contracts in test/ (Foundry-compatible)",
            "Add explicit obligation tags ($A_1$..$A_5$) in NatSpec",
            "Run `parallax5 score .` to generate a P2 certificate",
        ]
        if tools["halmos (symbolic execution → P3)"]:
            steps.append("✓ halmos installed — write symbolic property tests to reach P3")
    else:
        level = "P1"
        next_level = "P2"
        steps = [
            "Install Slither: `pip install slither-analyzer`",
            "Run `parallax5 score .` after installing",
        ]

    return {
        "estimated_level": level,
        "next_level": next_level,
        "solidity_files": len(sol_files),
        "tools": tools,
        "next_steps": steps,
    }
