# Archetype certificate sketches (legacy v8-era schema)

These five JSON files are illustrative archetype certificate sketches that predate Certificate Schema v1.0. They were produced under the v8-era certificate format (`compliance_level`, `obligation_map`, `artifacts` plural) and document the framework's per-archetype obligation structure rather than functioning as v1.0-validating certificates.

The protocols named (Aave V3, Compound V3, Lido, MakerDAO, Uniswap V3) are used as archetype labels only; these sketches are **not** endorsed assessments by any protocol team. Concrete v1.0-conforming named-protocol certificates would require protocol-team engagement and are out of scope for this paper.

For the v1.0-validating examples, see:

- `examples/certificate_uniswap_v3_core.json` — Substrate foundations worked example, AMM-core archetype, validates clean.
- `demos/vault/output/certificate.json` — the worked examples, ERC-4626 inflation attack (vault archetype).
- `demos/bridge/output/certificate.json` — the worked examples, attestation-bridge archetype.
- `demos/agent_gate/output/certificate.json` — the worked examples, AI-agent runtime gate.

| File | Archetype | Schema era |
|---|---|---|
| `aave_v3.json` | Lending protocol (P2) | v8 (legacy) |
| `compound_v3.json` | Lending protocol with modular markets (P3) | v8 (legacy) |
| `lido.json` | Liquid staking (P2) | v8 (legacy) |
| `makerdao.json` | Stablecoin / CDP (P3) | v8 (legacy) |
| `uniswap_v3.json` | AMM core (P3) | v8 (legacy) |
