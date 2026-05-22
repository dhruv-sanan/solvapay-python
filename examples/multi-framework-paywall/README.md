# Multi-Framework Paywall Demo

> **One tool. Three runtimes. One paywall.**  
> `solvapay-python` v0.8 — AI-agent moat demonstrated.

The same `web_search` function — decorated once with `@payable_tool` — runs paywalled across:

1. **FastMCP** — as an MCP tool for Claude Desktop / Claude Code
2. **LangChain** — inside a LangChain agent via `monetize_tool`
3. **Raw async** — direct `AsyncSolvaPay` gate check + tool call

## 60-second setup

```bash
cp .env.example .env
# Fill in SOLVAPAY_SECRET_KEY, SOLVAPAY_PRODUCT_REF, DEMO_CUSTOMER_REF
uv sync
```

## Runtime 1 — FastMCP server

```bash
uv run python server_mcp.py
```

Connect via Claude Desktop (add to `claude_desktop_config.json`) or Claude Code's `/mcp` command.

## Runtime 2 — LangChain agent

```bash
uv run python agent_langchain.py
```

## Runtime 3 — Raw async script

```bash
uv run python script_async.py
```

## How it works

```
web_search (decorated with @payable_tool)
    │
    ├─ FastMCP  ──→ register_payable_tool_fastmcp(mcp, web_search)
    ├─ LangChain ─→ monetize_tool(lc_tool, product=..., client=sv)
    └─ Async raw ─→ sv.limits.acheck(...) → gate manually → web_search.__wrapped__(...)
```

`PayableToolMeta._meta_version = 1` is stamped on the function. Any framework can
read `fn.__solvapay_meta__` to discover the product, plan, and resolver — without
importing SolvaPay.
