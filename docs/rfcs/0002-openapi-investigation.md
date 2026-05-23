# RFC 0002 — OpenAPI Spec Investigation

**Status:** Open  
**Date:** 2026-05-23  
**Author:** Dhruv Sanan  
**HLD reference:** §V1.9

## Question

Does SolvaPay publish an OpenAPI / Swagger spec for the server API?
If yes, it activates the `_generated/` model slot in HLD §V1.9 for V3.

## Action items

- [ ] File GitHub issue against `solvapay/solvapay-sdk` asking whether an OpenAPI spec is published
- [ ] Check standard paths: `https://api.solvapay.com/openapi.json`, `https://api.solvapay.com/v1/openapi.json`
- [ ] Check SolvaPay developer docs for spec download link

## Current approach (no spec)

Without an OpenAPI spec, models are hand-written in `src/solvapay/models.py` and validated against the real sandbox API. The `_generated/` slot in `src/solvapay/` is reserved but empty (HLD §V1.9).

## If spec is found

1. Compare spec endpoints against `src/solvapay/operations/_registry.py` — identify gaps
2. Evaluate `openapi-python-client` or `datamodel-code-generator` for model generation
3. Plan V3 `_generated/` activation — coordinate with HLD §V1.9 gating criteria

## If spec is not available

Leave `_generated/` slot reserved. Continue manual model maintenance. Re-evaluate at V3 planning.

## Findings

> TBD — pending backend response to GitHub issue.
