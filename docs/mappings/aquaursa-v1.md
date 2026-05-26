# tool-mapping/aquaursa-v1

> Companion narrative to `mappings/aquaursa-v1.json`.
> Author: AquaUrsa Research · License: CC0-1.0 · Substrate: v1.1.0+

`tool-mapping/aquaursa-v1` is the substrate's reference mapping from
analysis-tool findings to the PARALLAX-5 obligation taxonomy. It is
one mapping in the registered-mapping pattern; the protocol it
satisfies is described in `docs/MAPPING_PROTOCOL.md`, and the
registration process for additional mappings is described in
`mappings/README.md`.

This document is the **narrative** companion to the JSON instance.
For the actual depth values, see `mappings/aquaursa-v1.json`. For
the formal schema both files satisfy, see
`schemas/mapping_protocol_v1.json`.

## What it covers

`aquaursa-v1` covers four EVM-focused analysis tools at pinned
versions:

| Tool | Version pin | Documentation |
|---|---|---|
| Slither | 0.10.x | https://github.com/crytic/slither/wiki/Detector-Documentation |
| Mythril | 0.24.x | https://github.com/SmartContractSecurity/SWC-registry |
| halmos | 0.2.x | https://github.com/a16z/halmos |
| ObligationSol | parallax5-v6 | https://parallax.xyz/research |

Non-EVM tooling (Solana Anchor, Move, Substrate ink!, Substrate
pallets) is out of scope for v1; a separate `tool-mapping/aquaursa-v2`
namespace will be opened when the non-EVM analyzer ecosystem
matures.

## Depth values at a glance

| Tool | A1 | A2 | A3 | A4 | A5 |
|---|:-:|:-:|:-:|:-:|:-:|
| Slither | 2 | 2 | 0 | 2 | 0 |
| Mythril | 3 | 3 | 2 | 3 | 0 |
| halmos | 4 | 4 | 4 | 4 | 4 |
| ObligationSol | 2 | 2 | 0 | 2 | 2 |
| **Joint (pointwise max)** | **4** | **4** | **4** | **4** | **4** |

The joint row is the joint capability under the substrate's
Compositional Coverage Theorem (`lean/Parallax5/Compositional.lean`).
Whether the joint capability is *realized* on a particular contract
depends on whether each tool is actually run and produces its
maximum-depth output for that contract; the matrix above is the
ceiling, not a per-contract guarantee.

## Methodology

For each tool, the AquaUrsa team:

1. Read the tool's documented detector / finding catalog.
2. For each finding identifier, considered: "Does this finding, when
   triggered, constitute evidence that some specific obligation is
   violated for the analyzed contract?"
3. If yes, mapped it to one obligation and chose a depth on the
   six-level ladder based on the form of evidence the tool produces:
   - **Depth 2 (static detector)** for pattern matchers that flag
     code constructs.
   - **Depth 3 (symbolic path)** for symbolic execution tools that
     exhibit a path-condition witness.
   - **Depth 4 (formal property)** for user-property-based
     verification tools (halmos), conditional on a property file.
4. Wrote a justification explaining the reasoning. Justifications
   are subject to community review; pull requests adding or
   refining justifications are welcomed.

The substrate paper §4 (`paper/parallax-5.tex`) provides the
underlying theory; this mapping is the empirical calibration.

## Worked examples

Three compositional examples are included in the JSON instance:

- **DAO 2016 (A4 reentrancy)** — joint depth-3 on A4 from three
  tools agreeing.
- **Mango Markets (A5 oracle manipulation, $115M)** — joint depth-2
  on A5; ObligationSol is *necessary* (not just useful) because the
  other three tools have depth-0 on A5.
- **Beanstalk governance attack ($182M, A2)** — joint depth-4 on A2
  from halmos with property; the other tools provide complementary
  lower-depth evidence.

These examples are illustrative; they do not constitute a
benchmark. The substrate's empirical study (paper §10) provides
the 53-incident corpus and forward-test methodology.

## Calibration changes since v1.0.0

`aquaursa-v1` is in v1.0.0 in the substrate v1.1.0 release. No
calibration changes from the v1.0.1 substrate (where the same
values lived in `schemas/tool_mapping_v1.json`); the v1.1.0 change
is the namespace refactor, not a change to any depth value.

A v1.1.0 of the mapping (with refined justifications) is planned
once community feedback is in. v2 of the mapping namespace
(`tool-mapping/aquaursa-v2`) is reserved for non-EVM tooling.

## Citation

```bibtex
@dataset{aquaursa_tool_mapping_v1_2026,
  author    = {{AquaUrsa Research}},
  title     = {{tool-mapping/aquaursa-v1: PARALLAX-5 reference
                tool-finding to obligation mapping}},
  year      = {2026},
  version   = {1.0.0},
  publisher = {Zenodo},
  url       = {https://github.com/aquaursa/parallax-5/blob/main/mappings/aquaursa-v1.json}
}
```
