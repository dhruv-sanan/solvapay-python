"""Shared Pydantic model — used by all three runtimes."""

from __future__ import annotations

from pydantic import BaseModel


class WebSearchInput(BaseModel):
    """Input model for the web_search tool."""

    customer_ref: str
    query: str
    max_results: int = 5
