"""Deprecated shim. Use solvapay.adapters.langchain instead."""

from __future__ import annotations

import warnings

warnings.warn(
    "solvapay.langchain is deprecated; use solvapay.adapters.langchain",
    DeprecationWarning,
    stacklevel=2,
)

from solvapay.adapters.langchain import LangChainToolProtocol, monetize_tool

__all__ = ["monetize_tool", "LangChainToolProtocol"]
