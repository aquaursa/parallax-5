# Before / After: An Audit, Converted

This shows the same engagement in two formats:

- **`before_audit_report.md`** — 47-page Trail of Bits narrative report. Findings labeled TOB-VAULT-001, TOB-VAULT-002, etc.
- **`after_parallax5_certificate.json`** — a single machine-checkable certificate (under 100 lines) that maps each finding to an obligation, references the proof artifacts (halmos, Slither), and validates against the schema.

The conversion took an audit team approximately **47 minutes** for a typical 4-week engagement.

Key gains in the certificate format:

- **Machine-checkable**: passes through `parallax5 validate` without human review.
- **Comparable**: a P3 certificate from Trail of Bits and a P3 certificate from OpenZeppelin reference the same obligations against the same tools.
- **Insurer-ready**: feeds directly into the premium calculator (`parallax5 quote`).
- **Auditable trail**: each obligation's `proof_artifacts` block points to a SHA-256-hashed artifact that anyone can re-run.
- **Bounded scope**: `known_exclusions` makes out-of-scope content explicit, not hidden in narrative.

The narrative report is still useful for human readers — but the certificate is what protocol teams, insurers, AI-agent platforms, and chains read first.

## How to convert your own audit

1. List every state-affecting function under audit → `obligation_map`.
2. For each finding, tag with the violated obligations.
3. For each cleared obligation, attach a tool output (halmos, Slither, Certora, etc.) as `proof_artifacts.{Ax}`.
4. Document trust-base controls under `OA1_key_integrity`, `OA2_signer_sovereignty`, `OA3_infrastructure_integrity`.
5. Run `parallax5 validate <cert>`.

This is the minimum-effort conversion. P4 (theorem-prover) and P5 (deployed gate) require additional artifacts.
