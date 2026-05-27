# Contributing to PARALLAX-5

Thanks for your interest. PARALLAX-5 is a standard. The repository accepts
contributions in two distinct modes:

1. **Implementation contributions** to the reference tooling (Apache-2.0):
   the coordinator, validator, certifier, registry contract, and supporting
   code under `src/`, `parallax/`, `registry/`, and `scripts/`.
2. **Standard-text contributions** to the public coordination layer (CC0):
   the obligation vocabulary, depth scale, CROPS dimensions, walkaway
   taxonomy, and certificate field semantics. These flow through the Fork
   Protocol (`docs/FORK_PROTOCOL.md`).

## Implementation contributions

- Open an issue describing the change you'd like to make before submitting
  a substantial pull request.
- Add tests. The substrate's gates are the only way a change can be
  trusted: a contribution that doesn't extend coverage isn't load-bearing.
- Run `./RUN_VERIFICATION.sh` locally before opening a PR. All gates must
  remain green: 2,152 compositional checks, 19 CROPS tests, 129 Python fire tests (aggregate),
  24 Foundry tests, paper compiles cleanly.
- CI runs the same gates on every push (`.github/workflows/ci.yml`).

## Standard-text contributions

The substrate's standard text is dedicated under CC0 with structural
non-capturability commitments. Contributions to the standard text are
governed by the Fork Protocol, not by this repository's maintainers.
Anyone may fork the standard, propose pull-backs, and seek
compatibility-level alignment with this repository's reference text.

If you'd like to discuss an addition to the standard before forking,
open an issue and tag it `standard-text`.

## Reporting security issues

See `SECURITY.md`.

## Code of conduct

Be civil, be specific, and assume good faith.
