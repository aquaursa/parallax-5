# PARALLAX-5 Practitioner Guide: Issuing and Reading Certificates

This guide is for audit firms, protocol engineers, insurance underwriters, and AI-agent platform operators. It assumes familiarity with smart-contract security but no prior knowledge of formal methods.

## The Five Obligations in 60 Seconds

| | Name | What it means in plain English |
|---|---|---|
| **A1** | Value Conservation | After any operation, the protocol's books balance: total backing ≥ total claims, no rounding leak. |
| **A2** | Authorization Closure | Whoever called a state-changing function had the right to call it. |
| **A3** | Signature Integrity | Any signed authorization is a real, unforgeable, chain-bound, non-replayed signature. |
| **A4** | Temporal Distinctness | No value-affecting operation happens during a reentrant call or violates a known happens-before. |
| **A5** | External-Attestation Trust | Any oracle price, bridge message, or governance snapshot meets the protocol's quorum + freshness + diversity requirements. |

A vulnerability is **always** a violation of at least one of these (under the conditional-completeness theorem).

## Reading a PARALLAX-5 Certificate

A certificate is a JSON file with these required sections:

1. **`compliance_level`**: P0 (unclassified) through P5 (runtime-enforced). Higher = stronger.
2. **`obligation_map`**: every value-affecting function in the protocol, mapped to the obligations that apply.
3. **`proof_artifacts`** (required at P3+): per-obligation evidence, with tool name, version, verdict, and SHA-256 hash of the artifact.
4. **`trust_base_assumptions`**: explicit list of off-chain controls for OA1 (keys), OA2 (signers), OA3 (infrastructure).
5. **`known_exclusions`**: what is OUT of scope (e.g., "ECDSA modeled as assumption").
6. **`revalidation_triggers`**: when this certificate becomes invalid.

### Quick reading checklist

When you receive a certificate, in this order:

1. **Run the validator**: `python3 -m parallax.standard.validator cert.json`. If it doesn't say `VALID`, stop.
2. **Check the compliance level**. P0/P1 means almost no verification. P3+ means symbolic or formal proof. P5 means a deployed runtime gate.
3. **Check `obligation_map` coverage**: does it list EVERY function that touches value? If not, missing functions are unverified.
4. **Check `trust_base_assumptions`**: are the controls real? "Multisig 4-of-7 with hardware-secured signers across 3 jurisdictions" is real; "best practices" is not.
5. **Check `known_exclusions`**: what's NOT covered? If the cert excludes "cross-chain bridges" and the protocol has one, get a separate cert for that.
6. **Verify the proof artifact hashes**: download each referenced artifact, hash it, compare. If you cannot reproduce, the certificate is unverified.
7. **Check `revalidation_triggers`**: when does the cert expire? Has the protocol upgraded since?

## Issuing a PARALLAX-5 Certificate

To issue a P3+ certificate, you need:

1. A **list of all value-affecting functions** (the protocol's "transition set"). Use Slither or ObligationSol to enumerate.
2. For each function, **which obligations apply**. Typical patterns:
   - Vault deposit: A1, A2, A4
   - Bridge release: A2, A3, A5
   - Governance setter: A2
   - Oracle update consumer: A5
3. **Proof artifacts** for each declared obligation. Tools and what they produce:
   - **Slither**: P1/P2 only (static detectors)
   - **Mythril/halmos**: P3 (symbolic verification of bounded paths)
   - **Certora**: P4 (formally verified rules with SMT)
   - **Lean/Coq**: P4 (theorem-level proofs)
   - **Deployed step-secure gate**: P5
4. **Trust-base controls** documented for each of OA1, OA2, OA3.
5. **The Issuer's signature** over the certificate hash.

### From audit report to certificate

If your audit firm already produces narrative reports, the conversion is mechanical:

1. Tag every finding with one or more of A1..A5. (See the mapping in Section 13 of the paper.)
2. For every value-affecting function, list which findings were ruled out.
3. For every cleared obligation per function, attach the tool output as a proof artifact.
4. Wrap the document hashes in JSON per the schema.

A typical audit becomes a P2 (statically screened) or P3 (symbolically checked) certificate. Adding Certora/Lean verification raises to P4.

## Common Failure Modes

- **Missing function in `obligation_map`**: silent gap. Validator can't help; the gap is in the protocol team's enumeration.
- **`proof_artifacts` references but no artifact provided**: validator says VALID but recipient cannot reproduce.
- **`trust_base_assumptions` says "best practices"**: useless. Audit must reject.
- **Compliance level claimed > what tool can produce**: e.g., P4 claimed but only Slither used. Validator catches this for P4+.

## Working with Multiple Tools

PARALLAX-5 expects different tools for different obligations. A typical P4 certificate might use:
- A1: Certora rule `solvency_invariant` (PASS)
- A2: halmos symbolic execution (PASS over 12 paths)
- A4: Lean theorem `sibling_reentrancy_guard_preserves_A4` (proved)
- A5: SMT model in QF_NIA (UNSAT for all stale-oracle witnesses)

Three solvers (Z3, CVC5, Yices2) cross-verifying SMT results is recommended for P4+.

## Common Questions

**Q: Does PARALLAX-5 replace audits?**  
A: No. It's an audit report format, not a substitute for the audit. A P3 certificate without an audit narrative is uninformative for non-technical readers.

**Q: What if a basis counterexample is found?**  
A: The framework is intentionally falsifiable. A confirmed counterexample either refutes the adequacy assumption (in which case the basis must be revised), or refines the obligation definitions. Either outcome strengthens the framework.

**Q: Can a P5 certificate fail in production?**  
A: A P5 gate prevents EXECUTION of basis-violating transitions. It cannot prevent off-chain compromise (the basis-unobservable category). It also cannot prevent monitors with non-zero false-negative rate from missing some attacks.

**Q: How do certificates relate to insurance?**  
A: Insurers use the compliance level as a risk-tier input. The `parallax/economics/insurance_calculator.py` module gives a baseline pricing model. Expect P0→P5 to span roughly 6× in expected loss.

## Where to Get Help

- Schema: `paper/supplement/parallax5_certificate.schema.json`
- Validator: `parallax/standard/validator.py`
- Examples: `paper/supplement/real_protocols/*.json`
- Case studies: `case_studies/{vault_4626,bridge_attestation,ai_agent_gate}/`
- The paper: `paper/parallax_axioms.pdf`
