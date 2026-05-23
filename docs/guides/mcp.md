# MCP Integration

Monetize any MCP tool with SolvaPay using `@payable_tool`.

## Install

```bash
pip install "solvapay-python[mcp]"
```

## Stamp a tool

```python
from solvapay.paywall import payable_tool

@payable_tool(product="prd_0QKI8NHF")
def web_search(*, customer_ref: str, query: str) -> list[str]:
    """Search the web."""
    return [...]
```

## Register with FastMCP

```python
from fastmcp import FastMCP
from solvapay.adapters.mcp import register_payable_tool_fastmcp

mcp = FastMCP("my-server")
register_payable_tool_fastmcp(mcp, web_search)
```

## Schema flavors

```python
from solvapay.adapters.mcp import (
    payable_tool_mcp_schema,
    payable_tool_anthropic_tool,
    payable_tool_openai_function,
    payable_tool_langchain_args_schema,
)

mcp_schema = payable_tool_mcp_schema(web_search)
anthropic_tool = payable_tool_anthropic_tool(web_search)
openai_fn = payable_tool_openai_function(web_search)
langchain_schema = payable_tool_langchain_args_schema(web_search)
```

## Multi-framework example

See `examples/multi-framework-paywall/` for a complete example running one tool across FastMCP, LangChain, and raw async.
