# FastMCP Paywall Demo

A Model Context Protocol (MCP) server with two tools gated behind a SolvaPay paywall, built with [FastMCP](https://github.com/jlowin/fastmcp) and the community [solvapay-python](https://github.com/dhruv-sanan/solvapay-python) SDK.

**What this proves:** any Python MCP server can monetize tools per-call by stacking `@paywall.require` over `@mcp.tool()`. No backend changes needed.

## Tools

| Name | Price | What it does |
|---|---|---|
| `summarize_url(url)` | $0.02 / call | Fetches a URL and returns a 280-char preview. |
| `analyze_text(text)` | $0.05 / call | Returns word/char/sentence counts + avg word length. |

When the customer's limit is reached, the tool returns:
```json
{"paywall_required": true, "checkout_url": "https://solvapay.com/c/sess_..."}
```

The LLM can render the checkout link directly to the user.

## Run in 60 seconds

```bash
git clone https://github.com/dhruv-sanan/solvapay-python
cd solvapay-python/examples/fastmcp-paywall
cp .env.example .env
# Fill in SOLVAPAY_SECRET_KEY, SOLVAPAY_PRODUCT_REF, SOLVAPAY_DEMO_CUSTOMER_REF

uv sync
uv run python claim.py        # smoke test (no Claude Desktop needed)
```

Expected: two tool responses (or a paywall dict if your demo customer is over their limit).

## Plug into Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "solvapay-paywall-demo": {
      "command": "uv",
      "args": ["--directory", "/abs/path/to/examples/fastmcp-paywall", "run", "python", "server.py"],
      "env": {
        "SOLVAPAY_SECRET_KEY": "sk_sandbox_...",
        "SOLVAPAY_PRODUCT_REF": "prd_..."
      }
    }
  }
}
```

Restart Claude Desktop. Ask Claude: *"summarize https://example.com"* — Claude should call the tool, hit the paywall, and surface the checkout URL.

## How the gating works

`server.py` decorates each tool with `@paywall.require(product=PRODUCT_REF, client=sv)` from the SolvaPay Python SDK. The decorator runs `check_limits` against SolvaPay before each call. On `withinLimits=False`, it raises `PaywallRequired` carrying the hosted-checkout URL.

A small `_gated` helper converts the exception into a structured dict so the LLM can render the URL gracefully instead of seeing a stack trace.

## Customizing per-tool pricing

Pricing is defined in your SolvaPay dashboard (per-product or per-meter). To split the price between the two tools:
- Create separate products (one per tool) and pass distinct `product=...` to each decorator.
- OR: keep one product and use SolvaPay metering with different `meter_name` values per tool.

> **Production note:** `customer_ref` defaults to an env-var for demo convenience. In production, extract it from the MCP session context (e.g., `mcp.context.session.user_id`) to gate per real user.

## License

MIT — same as the main SDK.
