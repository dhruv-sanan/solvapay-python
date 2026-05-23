# Changelog Fragments

This directory contains towncrier changelog fragments. Each file represents one change entry.

## Fragment naming

```
<issue_or_pr_number>.<type>
```

**Types:** `feature`, `bugfix`, `doc`, `removal`

**Examples:**
```
42.feature     → "Add RetryTransport middleware"
55.bugfix      → "Fix idempotency key not sent on retry"
60.doc         → "Document api_version pinning"
99.removal     → "Remove deprecated SolvaPayAPIError alias"
```

## Required for PRs

Any PR that touches `src/` **must** include at least one fragment. PRs without a fragment will fail CI.

Example fragment content:
```
Add ``api_version`` kwarg to ``SolvaPay`` and ``AsyncSolvaPay`` for server-side API version pinning.
```

## Building the changelog

```bash
uv run towncrier build --version 0.9.0 --draft   # preview
uv run towncrier build --version 0.9.0            # write to CHANGELOG.md
```
