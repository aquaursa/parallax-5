"""The PARALLAX-5 five-obligation vocabulary.

A1 — Value conservation
A2 — Authorization closure
A3 — Signature integrity
A4 — Temporal distinctness
A5 — External-attestation trust boundary

See paper §3 and `docs/CERTIFICATE_SCHEMA.md` for the formal definitions.
"""
from .obligations import (
    ObligationId, Obligation, ALL_OBLIGATIONS, OBLIGATION_BY_ID, obligation_lookup,
    A1_SHARE_ASSET_CONSERVATION,
    A2_AUTHORIZATION_CLOSURE,
    A3_SIGNATURE_INTEGRITY,
    A4_TEMPORAL_DISTINCTNESS,
    A5_ORACLE_TRUST_BOUNDARY,
)

__all__ = [
    "ObligationId", "Obligation", "ALL_OBLIGATIONS", "OBLIGATION_BY_ID", "obligation_lookup",
    "A1_SHARE_ASSET_CONSERVATION",
    "A2_AUTHORIZATION_CLOSURE",
    "A3_SIGNATURE_INTEGRITY",
    "A4_TEMPORAL_DISTINCTNESS",
    "A5_ORACLE_TRUST_BOUNDARY",
]
