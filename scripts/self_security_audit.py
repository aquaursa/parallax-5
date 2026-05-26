"""scripts/self_security_audit.py — automated security audit of
PARALLAX itself.

Closes the "no security review of PARALLAX itself" gap from the
honest assessment. Scans the codebase for known anti-patterns:

  1. SQL injection (string concatenation in queries)
  2. Path traversal (user input in os.path.join)
  3. Command injection (shell=True with user input)
  4. SSRF (urllib.request without URL validation)
  5. Hardcoded secrets / API keys
  6. Pickle/yaml unsafe deserialization
  7. Bare exceptions hiding errors
  8. Use of eval / exec / compile

Outputs structured findings with severity + file:line references.
"""
from __future__ import annotations
import pathlib

import os
import re
import sys
from dataclasses import dataclass


@dataclass
class SecurityFinding:
    severity: str    # critical | high | medium | low | info
    rule_id: str
    file_path: str
    line_no: int
    code_snippet: str
    explanation: str


# Rules
RULES = [
    {
        "rule_id": "SQL_FSTRING",
        "severity": "high",
        "regex": re.compile(r'(execute|executemany)\s*\(\s*f["\']'),
        "explanation": "f-string in SQL execute() — possible SQL injection",
    },
    {
        "rule_id": "SQL_CONCAT",
        "severity": "high",
        "regex": re.compile(
            r'(execute|executemany)\s*\(\s*["\'][^"\']*["\']\s*\+'),
        "explanation": "String concatenation in SQL execute() — possible injection",
    },
    {
        "rule_id": "SHELL_TRUE",
        "severity": "high",
        "regex": re.compile(r'subprocess\.\w+\([^)]*shell\s*=\s*True'),
        "explanation": "shell=True allows command injection if input not sanitized",
    },
    {
        "rule_id": "EVAL_USE",
        "severity": "critical",
        "regex": re.compile(r'\beval\s*\('),
        "explanation": "eval() — extremely dangerous, allows arbitrary code execution",
    },
    {
        "rule_id": "EXEC_USE",
        "severity": "critical",
        "regex": re.compile(r'\bexec\s*\('),
        "explanation": "exec() — allows arbitrary code execution",
    },
    {
        "rule_id": "PICKLE_LOAD",
        "severity": "medium",
        "regex": re.compile(r'pickle\.loads?\s*\('),
        "explanation": "pickle.load() can execute arbitrary code — only use with trusted data",
    },
    {
        "rule_id": "YAML_UNSAFE",
        "severity": "high",
        "regex": re.compile(r'yaml\.load\s*\([^)]*\)'),
        "explanation": "yaml.load() without SafeLoader — arbitrary code execution",
    },
    {
        "rule_id": "BARE_EXCEPT",
        "severity": "low",
        "regex": re.compile(r'^\s*except\s*:\s*$'),
        "explanation": "Bare except hides all errors including KeyboardInterrupt",
    },
    {
        "rule_id": "EXCEPT_PASS",
        "severity": "low",
        "regex": re.compile(
            r'^\s*except\s+\w+(\s+as\s+\w+)?\s*:\s*$\n\s*pass\s*$',
            re.MULTILINE),
        "explanation": "except: pass silently swallows exceptions",
    },
    {
        "rule_id": "URLOPEN_USERINPUT",
        "severity": "medium",
        "regex": re.compile(r'urllib\.request\.urlopen\s*\(\s*\w+\s*\)'),
        "explanation": "urlopen with variable URL — possible SSRF if user-controlled",
    },
    {
        "rule_id": "HARDCODED_SECRET",
        "severity": "high",
        "regex": re.compile(
            r'["\'](sk-[a-zA-Z0-9]{20,}|api_key=[a-zA-Z0-9]{20,}|'
            r'[A-Z0-9]{32,})["\']'),
        "explanation": "Hardcoded secret/API key detected",
    },
    {
        "rule_id": "MD5_USE",
        "severity": "low",
        "regex": re.compile(r'hashlib\.md5\s*\('),
        "explanation": "MD5 is cryptographically broken — use SHA-256",
    },
    {
        "rule_id": "TODO_FIXME",
        "severity": "info",
        "regex": re.compile(r'#.*\b(TODO|FIXME|XXX|HACK)\b'),
        "explanation": "Code annotation flagged for follow-up",
    },
    {
        "rule_id": "PATH_TRAVERSAL",
        "severity": "medium",
        "regex": re.compile(r'os\.path\.join\s*\(\s*[^,)]+,\s*\w+\s*\)'),
        "explanation": "os.path.join with variable suffix — verify no user-controlled traversal",
    },
]


def audit_file(file_path: str) -> list:
    """Run all rules against one file."""
    findings = []
    try:
        with open(file_path, "r", errors="ignore") as f:
            content = f.read()
    except Exception:
        return findings
    lines = content.splitlines()

    for rule in RULES:
        for m in rule["regex"].finditer(content):
            line_no = content[:m.start()].count("\n") + 1
            if line_no <= len(lines):
                snippet = lines[line_no - 1].strip()
            else:
                snippet = m.group()
            findings.append(SecurityFinding(
                severity=rule["severity"],
                rule_id=rule["rule_id"],
                file_path=file_path,
                line_no=line_no,
                code_snippet=snippet[:120],
                explanation=rule["explanation"]))
    return findings


def audit_directory(root: str, *, ignore_dirs: tuple = (
    "__pycache__", ".git", "node_modules", "data", "tests",
    "_selftest_s56.py",
)) -> list:
    """Walk directory, audit each .py file."""
    findings = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ignore_dirs]
        for f in fn:
            if f in ignore_dirs:
                continue
            if f.endswith(".py"):
                findings.extend(audit_file(os.path.join(dp, f)))
    return findings


def main():
    root = (
        sys.argv[1] if len(sys.argv) > 1 else
        str(pathlib.Path(__file__).resolve().parent.parent / "parallax"))
    print("=" * 72)
    print("  PARALLAX self-security-audit")
    print(f"  Scanning: {root}")
    print("=" * 72)
    findings = audit_directory(root)
    
    # Group by severity
    by_severity = {}
    for f in findings:
        by_severity.setdefault(f.severity, []).append(f)

    # Skip "info" (TODO/FIXME) for the headline
    print(f"\n=== Findings summary ===")
    for sev in ("critical", "high", "medium", "low", "info"):
        if sev not in by_severity:
            continue
        items = by_severity[sev]
        print(f"  {sev.upper():10s}  {len(items)} findings")

    # Group by rule_id
    by_rule = {}
    for f in findings:
        by_rule.setdefault(f.rule_id, []).append(f)
    print(f"\n=== Findings by rule ===")
    for rule_id, items in sorted(
            by_rule.items(), key=lambda kv: -len(kv[1])):
        first = items[0]
        if first.severity == "info":
            continue
        print(f"  {first.severity.upper():8s}  {rule_id:18s}  "
                f"{len(items):>4d} occurrences")

    # Show samples for high+critical
    print(f"\n=== Critical/High severity samples ===")
    for sev in ("critical", "high"):
        if sev not in by_severity:
            continue
        for f in by_severity[sev][:3]:
            short_path = f.file_path.replace(
                str(pathlib.Path(__file__).resolve().parent.parent) + "/", "")
            print(f"\n  [{f.severity.upper()}] {f.rule_id}")
            print(f"    {short_path}:{f.line_no}")
            print(f"    {f.code_snippet}")
            print(f"    → {f.explanation}")
    
    # Final verdict
    n_crit = len(by_severity.get("critical", []))
    n_high = len(by_severity.get("high", []))
    print(f"\n{'='*72}")
    print(f"  Total findings: {len(findings)}")
    print(f"  Critical: {n_crit}, High: {n_high}, "
          f"Medium: {len(by_severity.get('medium', []))}, "
          f"Low: {len(by_severity.get('low', []))}")
    print(f"{'='*72}")
    return findings


if __name__ == "__main__":
    main()
