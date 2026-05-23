# LangChain Integration

Monetize any LangChain tool with SolvaPay.

## Install

```bash
pip install "solvapay-python[langchain]"
```

## Monetize a tool

```python
from solvapay import SolvaPay
from solvapay.adapters.langchain import monetize_tool

sv = SolvaPay()

# Any LangChain BaseTool-compatible object
monetized = monetize_tool(
    my_langchain_tool,
    product="prd_0QKI8NHF",
    customer_ref_arg="customer_ref",
    client=sv,
)
```

## With `@payable_tool`

If a tool is already decorated with `@payable_tool`, `monetize_tool` reads `__solvapay_meta__` automatically:

```python
from solvapay.paywall import payable_tool
from solvapay.adapters.langchain import monetize_tool

@payable_tool(product="prd_0QKI8NHF")
def web_search(*, customer_ref: str, query: str) -> list[str]: ...

monetized = monetize_tool(web_search, client=sv)
```

## See also

- `examples/langchain-paywall/` — standalone LangChain agent example
- `examples/multi-framework-paywall/` — same tool in MCP + LangChain + async
