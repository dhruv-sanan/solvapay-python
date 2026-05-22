# Contributing

## Local development

```bash
git clone https://github.com/dhruv-sanan/solvapay-python
cd solvapay-python
uv sync --all-extras --dev
```

## Running checks

```bash
uv run ruff check src tests        # lint
uv run ruff format --check src tests  # format gate
uv run mypy src                    # type check
uv run pytest -v                   # tests
uv run python tools/api_diff.py    # stability manifest gate
uv run lint-imports --config tools/importlinter.cfg  # layer DAG gate
```

## Layer DAG rules

The SDK has a strict layer hierarchy — see [docs/architecture/layers.md](docs/architecture/layers.md).

**Hard rules:**
- `_transport` must not import `client`, `paywall`, `adapters`, or `operations`
- `operations` must not import `paywall` or `adapters`
- `client` must not import `adapters` or `experimental`

CI fails on violations via `import-linter`.

## PR checklist

- [ ] Tests added for new behavior
- [ ] `CHANGELOG.md` updated
- [ ] `docs/` updated if public API changed
- [ ] Layer DAG respected (`uv run lint-imports` passes)
- [ ] Stability manifest updated if new public exports added

## Commit style

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add AsyncPaywall class
fix(webhooks): set replay_ttl_seconds default correctly
refactor: extract _transport package
docs: update README with MCP quickstart
```

## Adding a new resource namespace

1. Add `OpSpec` entries to `src/solvapay/operations/_registry.py`
2. Create `src/solvapay/operations/<resource>.py` with sync + async methods
3. Wire namespace attr in `SolvaPay.__init__` and `AsyncSolvaPay.__init__`
4. Add deprecated flat shim in `client.py` / `_async_client.py`
5. Tests in `tests/operations/`
