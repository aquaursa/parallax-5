# PARALLAX-5 Mapping Registry

This directory holds the registered tool-mappings recognized by the
PARALLAX-5 coordinator. A *mapping* assigns evidence-depth grades to
analysis-tool findings under the substrate's five-obligation
taxonomy (A1–A5). The mapping is what lets the coordinator answer
"given these tool outputs, what P-level certificate is defensible?"

The substrate ships one mapping, `aquaursa-v1.json`, as a reference
calibration authored by AquaUrsa Research. **It is not the only
admissible mapping.** Other authors (tool vendors, audit firms,
academic groups) are invited to publish their own mappings; the
coordinator accepts any mapping that validates against
`schemas/mapping_protocol_v1.json` and certificates explicitly name
which mapping they used.

## Namespace

Each mapping has a globally-unique namespace of the form

```
tool-mapping/{author}-v{major}
```

where `{author}` is lower-case ASCII identifying the mapping
authority and `{major}` is the integer major version. Examples:

- `tool-mapping/aquaursa-v1`
- `tool-mapping/audit-firm-x-v2`
- `tool-mapping/research-group-y-v1`

The namespace is enforced by both `schemas/mapping_protocol_v1.json`
(on the mapping document itself) and `schemas/certificate_v1.json`
(on the `mapping` field of every issued certificate).

## Versioning

Each mapping uses semantic versioning. The major component must
match the namespace's `-v{major}` suffix.

- **Major** bump: incompatible change in coverage interpretation.
  A certificate referencing a v1 mapping is not auto-portable to v2.
- **Minor** bump: adds tools, adds entries, or refines depth values.
  Backward-compatible.
- **Patch** bump: justification-text or typo fixes only; no semantic
  change to any depth value.

## Registering a new mapping

1. Author a JSON document conforming to
   `schemas/mapping_protocol_v1.json` (validates with
   `jsonschema -i your_mapping.json schemas/mapping_protocol_v1.json`).
2. Deposit a permanent copy on Zenodo (or equivalent). Cite the DOI
   in your mapping's `publication.doi_target` field.
3. Submit a pull request adding your file under `mappings/`. The CI
   pipeline validates the file against the schema and runs the
   coordinator's compositional checks (see `tests/test_mapping_*`).
4. License: CC0 or another permissive license consistent with the
   substrate's Non-Capturability Charter (Article 2).

## Using a mapping

The PARALLAX-5 coordinator accepts a `--mapping NAMESPACE` flag on
all certificate-emitting commands:

```bash
parallax5 certify --mapping tool-mapping/aquaursa-v1 ./findings.json
```

When `--mapping` is omitted, the coordinator defaults to
`tool-mapping/aquaursa-v1`. The chosen namespace is recorded in the
emitted certificate's `mapping` field so verifiers can independently
re-check the per-tool depth claims.

## Conformance

Every mapping in this directory must:

1. Validate against `schemas/mapping_protocol_v1.json`.
2. Use the same five-obligation taxonomy (A1–A5) and six-level
   depth ladder (0–5).
3. Be published under a permissive license.
4. Have a stable URL or DOI for each released major version.

The substrate's `tests/test_mapping_*` enforces (1) and (2) on every
file in this directory; (3) and (4) are enforced by the PR-review
process.

## Open questions

- **Cross-mapping comparison**: if two mappings assign different
  depths to the same tool finding, which is right? The coordinator
  itself takes no position — it certifies under the mapping the
  user chose. Comparing mappings is a research question; the
  substrate's Compositional Coverage Theorem applies WITHIN a
  mapping, not across them.
- **Mapping aggregation**: should the coordinator support taking the
  pointwise max across multiple mappings? Proposed but not yet
  implemented; see paper §4 for the underlying lattice argument.
