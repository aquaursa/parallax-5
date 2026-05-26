# PARALLAX-5 Governance & Certificate Lifecycle


## Certificate lifecycle

```
                                                           ┌─────────┐
                                                           │ revoke  │
                          ┌──────────┐    ┌──────────┐    │  (rare) │
                          │ issue    │ → │ verify   │ → │ publish │
                          └──────────┘    └──────────┘    └────┬────┘
                                                                │
                                                          ┌─────▼─────┐
                                                          │  active   │
                                                          └─────┬─────┘
                                                                │
                                            ┌───────────────────┼───────────────┐
                                            ▼                   ▼               ▼
                                     ┌────────────┐    ┌──────────────┐ ┌───────────┐
                                     │ revalidate │    │  supersede   │ │  expire   │
                                     │ (renewal)  │    │  (upgrade)   │ │  (T+180d) │
                                     └────────────┘    └──────────────┘ └───────────┘
```

### 1. Issue

A certificate is issued by an **Issuer** (DID) signing the canonical JSON of the certificate. The issuer can be:
- The protocol team itself (self-attestation; lowest trust)
- An audit firm (third-party attestation; moderate trust)
- A consortium (multi-issuer certificate; high trust)
- The PARALLAX-5 reference issuer (machine-attested from open-source tool runs)

### 2. Verify

Anyone can validate the certificate against the schema:
```bash
parallax5 validate cert.json
```

Verification checks:
- Schema conformance (Draft 2020-12)
- Compliance-level invariants (P3+ requires proof artifacts; P4+ requires theorem prover; P5 requires runtime gate)
- Issuer signature
- Proof artifact hash availability
- Date validity

### 3. Publish

The certificate is published to a public registry. Options:
- The protocol's own repo at `.parallax/cert.json`
- A central registry (e.g., a future `parallax5.io`)
- A federation of registries (each chain operates its own)

### 4. Revalidation triggers

A certificate must be revalidated if any of these occur:

| Trigger | Why |
|---|---|
| Contract upgrade | Code changed → properties may no longer hold |
| Proxy implementation change | Effective code is now different |
| Oracle source change | A5 assumptions changed |
| Verifier quorum change | A5 quorum/diversity changed |
| Governance parameter change | OA2 trust-base changed |
| Chain deployment change | New chain with potentially different runtime semantics |
| Proof tool version change | Verdict may differ on new tool version |
| Exploit affecting a dependency | A5/OA3 controls may be invalidated |
| 180 days elapsed | Default expiry |

### 5. Revocation

A certificate may be revoked early if a basis violation is discovered or a trust-base assumption fails. Revocation is signed by the issuer; if the issuer is unwilling/unable, a community challenge process governs revocation.

### 6. Supersession

A new certificate supersedes the prior one. Both remain in the registry; the older is marked superseded. Insurers and consumers always reference the current certificate, but the history is auditable.

## Trust model

| Property | Requirement |
|---|---|
| **Certificate integrity** | Signed by issuer (DID); canonical JSON pre-image hashed |
| **Proof artifact integrity** | SHA-256 hashes of all referenced tool outputs |
| **Tool version pinning** | Each proof_artifact records `tool` and `version` |
| **Issuer identity** | Issuer DID must resolve to a verifiable public key (DID-URL or DNS) |
| **Revocation registry** | Append-only log; revoked certs cannot be unrevoked |
| **Audit trail** | Every state transition (issue/verify/revalidate/supersede/revoke) is logged with timestamp + actor |
| **Conflict resolution** | Disputes about correctness of a certificate go through the falsification challenge (see [FALSIFICATION_CHALLENGE.md](FALSIFICATION_CHALLENGE.md)) |

## Fake-certificate prevention

A fake certificate is structurally impossible if the validator is used: schema validation fails on missing required fields, mismatched hashes, invalid signatures, or missing proof artifacts. The only attack is a legitimately-signed certificate with overclaim — where the issuer references proof artifacts that don't actually verify.

Mitigation:
1. **Hashes are content-addressed**: anyone can re-fetch the artifact and re-hash.
2. **Tool versions are pinned**: anyone can re-run the tool at that version.
3. **Independent re-verification is invited**: the falsification challenge bounty rewards confirmed overclaim.

## Tool version pinning

Each proof artifact records:

```json
"A1": {
  "tool": "halmos",
  "version": "0.3.3",
  "verdict": "PASS",
  "paths_explored": 47,
  "artifact_hash": "sha256:..."
}
```

A consumer of the certificate can:
1. Install halmos 0.3.3.
2. Fetch the test file by hash.
3. Re-run halmos; verdict must match.

If the verdict differs (tool fixed a bug, semantics changed), the certificate is invalid and must be revalidated against the new tool version.

## Revocation registry

A minimal append-only log:

```
2026-05-25T12:00:00Z  REVOKE  p5cert-example-vault-2026-04-15  reason="A1 counterexample found"  by="did:web:examplefinance.io"
```

Distributed via the same registries that host certificates. Insurers query the registry before underwriting; CI workflows poll on each PR.

## Conflict resolution

When two parties disagree about a certificate's validity:

1. The challenger submits a basis counterexample to the falsification challenge.
2. A panel (issuer + ≥2 independent reviewers) reviews.
3. If the counterexample is confirmed: certificate is revoked, framework is updated.
4. If not confirmed: counterexample is documented as "considered but not refuting" and the certificate stands.

This is the same model as CVE: every dispute produces durable public record.
