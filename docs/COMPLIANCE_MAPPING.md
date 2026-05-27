# Compliance Mapping

PARALLAX-5 certificates provide machine-checkable evidence for several regulatory frameworks governing AI and value-bearing automated systems. The frameworks covered here are:

* EU AI Act, Regulation (EU) 2024/1689, with enforcement starting August 2, 2026
* DORA, Regulation (EU) 2022/2554, in force since January 17, 2025
* NIST AI Risk Management Framework 1.0, the voluntary US framework
* ISO/IEC 42001:2023, the international AI management systems standard

The mappings appear at two levels. The first level maps each obligation in the substrate to the regulatory clauses where the obligation contributes evidence. The second level maps each field in the certificate schema to the audit-evidence requirement it satisfies. Both layers are designed to drop directly into conformity-assessment documentation, EU AI Act Article 11 technical files, DORA Article 28 third-party risk registers, or ISO 42001 risk-treatment documentation.

This mapping reflects AquaUrsa's reading of the standards as of v1.1.0. A definitive compliance determination is the work of a competent authority, a notified body, or an accredited external auditor. Certificates provide evidence into that determination; they do not constitute the determination itself.

## Obligation × Regulatory Clause

| Obligation | EU AI Act | DORA | NIST AI RMF | ISO/IEC 42001 |
|---|---|---|---|---|
| A1 Value conservation | Art. 15 (accuracy, robustness) | Art. 28(2)(b) ICT integrity | MS-2.6, MG-2.1 | 8.3 operational control |
| A2 Authorization closure | Art. 14 (human oversight) | Art. 28(2)(c) access management | MP-5.1 roles and accountability | 8.4 responsibility and authority |
| A3 Signature integrity | Art. 10 (data governance) | Art. 28(2)(a) information system security | MS-3.2 system performance | 7.5.3 documented information |
| A4 Temporal distinctness | Art. 12 (logging); Art. 15 cybersecurity | Art. 9(3) operational resilience | MS-1.3, MS-2.7 monitoring | 8.5 process implementation |
| A5 External-attestation trust | Art. 13 transparency; Art. 11 documentation | Art. 28, Art. 30 third-party arrangements | MP-5.2, MS-3.3 third-party AI | 8.6 suppliers and third parties |

## Certificate Field × Audit Evidence

The 19-field certificate schema (defined in `schemas/certificate_v1.json`, with examples in `examples/`) carries the evidence required by the standards above. Three groups of fields contribute different kinds of evidence.

### Identity, versioning, and lifecycle fields

| Field | EU AI Act | DORA | ISO 42001 |
|---|---|---|---|
| `certificate_id` (UUID) | Art. 11(1)(c) unique identification | Art. 28 identifiable artifact | 7.5.3 controlled documentation |
| `version` | Art. 11(1)(d) version control | Art. 28 change management | 7.5.3 |
| `issued_at` | Art. 12 temporal logging | Art. 28 temporal audit | 7.5.3 |
| `valid_until` or `expiry` | Art. 17 periodic reassessment | Art. 28 contractual term | 9.1.3 analysis and evaluation |
| `state` (seven-state lifecycle) | Art. 17 operational status | Art. 9 resilience state | 9.1.3 |

### Subject and scope fields

| Field | EU AI Act | DORA |
|---|---|---|
| `subject` (contract address, agent ID, hash) | Art. 11(1)(b) system identification | Art. 28 ICT asset identification |
| `bytecode_hash` (Keccak-256) | Art. 15 tamper evidence | Art. 28(2)(a) integrity controls |
| `chain` or `runtime` | Art. 11(1)(a) operational context | Art. 28 ICT environment |

### Obligation, authority, and depth fields

| Field | EU AI Act | DORA |
|---|---|---|
| `obligations.A1.status` and `.evidence` | Art. 15 accuracy/robustness; Art. 11(1)(e) methodology | Art. 28(2)(b) |
| `obligations.A2.status` and `.evidence` | Art. 14 human oversight; Art. 11(1)(g) | Art. 28(2)(c) |
| `obligations.A3.status` and `.evidence` | Art. 10 data governance; Art. 15 | Art. 28(2)(a) |
| `obligations.A4.status` and `.evidence` | Art. 12 logging | Art. 9(3) |
| `obligations.A5.status` and `.evidence` | Art. 13 transparency; Art. 11(1)(h) third-party | Art. 30 ICT third-party arrangements |
| `obligations._meta.adequacy_condition` | Art. 11(1)(e) methodology | Art. 28(2)(d) |
| `issuer` (issuing organization) | Art. 11(1)(a) accountability | Art. 30 contractual party |
| `issuer_signature` (Ed25519) | Art. 15 cybersecurity; Art. 17 post-market integrity | Art. 28(2)(a) |
| `parent_artifact_doi` | Art. 11(1)(h) supply-chain disclosure | Art. 30(1)(b) ICT third-party documentation |
| `tool_mapping_namespace` | Art. 11(1)(e) methodology version | Art. 28 methodology documentation |
| `level` (P1, P3, P5) | Art. 15 graded assurance | Art. 28 graded criticality |
| `crops_vector` (5-tuple) | Art. 11(1)(f) capability assessment | Art. 28 capability disclosure |

## EU AI Act conformity assessment

A deployer of an Annex III high-risk AI system that uses PARALLAX-5 certificates follows the sequence below before placing the system on the market.

For Article 11 technical documentation, the deployer assembles certificates covering each component subject to the substrate (the AI agent and the smart contracts it touches), a mapping document showing how certificate fields satisfy Annex IV technical-documentation requirements, and a list of the gate's operational limits stating which transitions are accepted and which are rejected.

For the Article 9 risk management system, the deployer documents the five obligations as the formal risk framework, identifies the basis-observable share of the catalog's archetype risks for the deployed protocol, and notes the residual basis-unobservable and ambiguous shares.

For Article 10 data governance, the deployer documents A3 (signature integrity) controls on input data and A5 (external-attestation trust) declarations for off-chain inputs.

For Article 14 human oversight, the deployer documents A2 (authorization closure) controls and the certificate revocation procedure that transitions a certificate out of the `active` state.

For Article 15 accuracy, robustness, and cybersecurity, the deployer documents A1 (value conservation) and A4 (temporal distinctness) controls, the bytecode hash anchoring used to detect tampering, and the gate's maximally-permissive-shield property.

Internal conformity assessment under Annex VI accepts the assembled certificates as the evidence base. Third-party conformity assessment under Annex VII submits certificates and reproducibility receipts to the notified body.

Post-market obligations under Article 17 are satisfied by the certificate lifecycle. The seven-state lifecycle (issued, active, suspended, revoked, reissued, expired, withdrawn) is logged on-chain in the `ParallaxRegistry` contract. Sepolia reference deployment is at `0x8015A98dF9037Cd79a03B291a6fF3C2841992D5b`; mainnet deployment is planned. State transitions are monitored continuously; spontaneous reactivation is impossible by construction. Revocation events emit `CertificateRevoked` events for downstream monitoring.

## DORA Articles 28-30

For a financial entity using PARALLAX-5-certified third-party AI agents or smart contracts, the certificates provide evidence for Article 28 general principles (formal documentation of automated decision-making under 28(1); information-system security under 28(2)(a) via A3, A4, and bytecode hash; integrity under 28(2)(b) via A1; access management under 28(2)(c) via A2; methodology documentation under 28(2)(d) via the adequacy condition and paper reference; third-party arrangements register under 28(7) via issuer and parent-artifact-DOI fields).

Article 29 concentration risk is structurally bounded at the substrate level. The Standard text is published under CC0 with non-capturability commitments documented in `docs/CHARTER.md`. Tool-level concentration concerns (over-reliance on findings from a single static analyzer) are addressed by the compositional verification architecture: adding additional tools to the stack increases coverage and cannot reduce it.

Article 30 contractual arrangements with ICT third parties are addressed through the Master Services Agreement for Co-Pilot SaaS Enterprise tier customers. The MSA covers service descriptions, processing locations, service-level KPIs, security-incident assistance, and cooperation rights with competent authorities. Contact AquaUrsa for the current MSA template.

## NIST AI RMF alignment

The four-function model (Govern, Map, Measure, Manage) maps to the substrate as follows.

Under Govern, the substrate's CC0 Standard text and the structural non-capturability commitments documented in `docs/CHARTER.md` contribute to GV-4.1 (organizational practices for critical thinking and safety-first mindset).

Under Map, MP-3.1 internal context is satisfied by the substrate's explicit scope (value-bearing-state slice with stated boundaries). MP-5.1 roles and responsibilities is satisfied by the certificate `issuer` field. MP-5.2 third-party considerations is satisfied by the `parent_artifact_doi` and tool-mapping fields.

Under Measure, MS-1.3 quantitative assessments is satisfied by the five obligations and the basis-observability predicate. MS-2.6 acceptance/rejection is satisfied by the step-secure gate. MS-2.7 operational metrics is satisfied by the certificate level and CROPS vector. MS-3.2 performance metrics is satisfied by the paper-canonical 129 Python fire tests, 24 Foundry tests, and zero `sorry`. MS-3.3 third-party AI monitoring is satisfied by on-chain certificate lifecycle events.

Under Manage, MG-2.1 resources for risk management is satisfied by the open-source substrate combined with the Co-Pilot SaaS. MG-3.1 third-party risk is satisfied by certificate parentage chains. MG-4.1 post-deployment monitoring is satisfied by the same lifecycle infrastructure that handles EU AI Act Article 17.

## ISO/IEC 42001:2023

| Clause | Evidence |
|---|---|
| 5.1 Leadership and commitment | Founder and advisor signoff on `docs/CHARTER.md` |
| 6.1.4 Risk treatment | Five obligations as the treatment framework |
| 7.5.3 Controlled documentation | Certificate schema and on-chain registry |
| 8.3 Operational planning and control | Step-secure gate's accept/reject semantics |
| 8.4 Responsibility and authority | A2 authorization-closure documentation |
| 8.5 Process implementation | Seven-state certificate lifecycle |
| 8.6 Suppliers and third parties | A5 external-attestation evidence |
| 9.1.3 Analysis and evaluation | Certificate state transitions and audit trail |

## Concrete workflow: Big 4 consulting firm delivering a conformity assessment

A Big 4 firm preparing an EU AI Act conformity assessment for a DeFi protocol client follows the sequence below.

The client deployment has a PARALLAX-5 P3 certificate covering its core contracts. The assessment task is to produce Annex IV technical documentation suitable for either internal (Annex VI) or third-party (Annex VII) conformity assessment.

The substrate's contribution to the documentation begins with the certificate's `obligations.*.evidence` fields, which satisfy Annex IV §1(c) on testing methodology. The certificate's `parent_artifact_doi` reference points the assessor to the substrate's paper and verification artifact, satisfying Annex IV §1(d) on design specifications. The on-chain certificate state and lifecycle events satisfy Annex IV §2 on post-market monitoring. The certificate's CROPS vector contributes to Annex IV §1(e) on risk-management measures.

The auditor's task is to validate that the certificate's evidence chain reproduces from public artifacts using `RUN_VERIFICATION.sh` and that the certificate's `subject` field matches the deployed contract addresses. Once validated, the Annex IV documentation is assembled with the certificate as foundational evidence. The auditor signs the conformity opinion.

This is the operational answer to the question "what does a Big 4 firm sell when it sells a PARALLAX-5-based AI Act conformity assessment to its clients?" The answer is methodology, expert opinion, and accountability. The substrate provides the reproducible evidence base on which that opinion can defensibly rest.

## Liability allocation

The substrate is published under Apache-2.0 with the standard warranty disclaimer. Anyone can verify its claims; AquaUrsa does not warrant fitness for any specific regulatory purpose. The substrate is open source; the warranty disclaimer is standard.

The Co-Pilot SaaS commercial offering operates under a Master Services Agreement with negotiated warranty terms. Standard B2B SaaS warranty norms apply.

An auditor using PARALLAX-5 certificates as evidence retains professional liability for their conformity-assessment opinion. The substrate provides evidence; the auditor provides judgment. This is the standard allocation for any audit relying on third-party evidence.

A notified body issuing a conformity certificate under EU AI Act Annex VII retains regulatory liability for that certificate. PARALLAX-5 certificates fed into the notified body's process are inputs to the assessment, not outputs from it.

## Engagement

For Big 4 firms or specialized auditors preparing compliance assessments, the open-source substrate is freely usable without engagement. For commercial engagements (compliance mapping reviews, custom integrations, expert support for high-stakes assessments), contact `research@aquaursa.io`. The Enterprise SaaS tier includes a DORA-aligned documentation template.

For financial entities preparing DORA documentation, the Enterprise tier documentation template handles the standard cases. For protocol-specific PARALLAX-5 binding work, the public grant track is the appropriate path; for private engagement, contact AquaUrsa directly.

For notified bodies and competent authorities, AquaUrsa is open to dialogue on certification-process integration. Contact `research@aquaursa.io`.

## Versioning

This mapping is versioned alongside the substrate. Regulatory changes (AI Act amendments, ISO 42001 revisions, NIST AI RMF updates) trigger a coordinated update to this document, the certificate schema if affected, and `CHANGELOG.md`. The mapping currently reflects PARALLAX-5 v1.1.0 and was last reviewed on 2026-05-27.

## Caveats

This mapping represents AquaUrsa's reading of the standards. Three classes of caveat apply.

First, mapping a transition-level obligation to a regulatory clause requires interpretive judgment. The interpretation in this document represents AquaUrsa's best reading; alternative readings exist and are defensible.

Second, a certificate is evidence rather than complete documentation. A full conformity assessment requires additional artifacts beyond what the certificate provides. For example, AI Act Article 10 requires training data documentation that the certificate does not contain.

Third, jurisdictional differences are real. EU AI Act is binding regulation; NIST AI RMF is voluntary; ISO 42001 is an international standard adopted differently in different jurisdictions. This document does not adjudicate between jurisdictions.

For high-stakes regulatory submissions, consult external counsel and an accredited auditor.
