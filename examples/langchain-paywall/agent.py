"""LangChain agent with a paywalled tool.

Shows how monetize_tool gates a custom LangChain tool behind a SolvaPay
paywall. When the customer is over-limit, the agent receives a structured
dict with the checkout URL and surfaces it to the user instead of running
the tool.

Run:
    cp .env.example .env   # fill in your keys
    uv run python agent.py
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI

from solvapay import SolvaPay
from solvapay.langchain import monetize_tool

load_dotenv()

PRODUCT_REF = os.environ.get("SOLVAPAY_PRODUCT_REF", "prd_demo")

sv = SolvaPay()


def _web_search(customer_ref: str, query: str) -> str:
    """Stub web search. Replace with a real search API in production."""
    return f"[stub] Top results for '{query}': ..."


raw_search_tool = Tool.from_function(
    name="web_search",
    func=_web_search,
    description=(
        "Search the web for a query. "
        "Input: customer_ref (str), query (str). "
        "Returns a summary of top results."
    ),
)

# Gate the tool behind a SolvaPay paywall.
# When within_limits is False, the tool returns a structured paywall dict
# instead of calling _web_search, so the agent can surface the checkout URL.
search_tool = monetize_tool(raw_search_tool, product=PRODUCT_REF, client=sv)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. If a tool returns paywall_required=True, "
                   "tell the user they need to upgrade and share the checkout_url."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

agent = create_tool_calling_agent(llm, [search_tool], prompt)
executor = AgentExecutor(agent=agent, tools=[search_tool], verbose=True)

if __name__ == "__main__":
    customer = os.environ.get("DEMO_CUSTOMER_REF", "cus_demo")
    print(f"\nRunning agent for customer: {customer}\n")
    result = executor.invoke(
        {"input": f"Search for 'AI agent frameworks 2025'. My customer_ref is {customer}."}
    )
    print("\n--- Final output ---")
    print(result["output"])
