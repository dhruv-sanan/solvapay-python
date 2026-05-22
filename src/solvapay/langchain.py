"""Deprecated shim. Use solvapay.adapters.langchain instead."""

from __future__ import annotations

import warnings

from solvapay.adapters.langchain import LangChainToolProtocol, monetize_tool

warnings.warn(
    "solvapay.langchain is deprecated; use solvapay.adapters.langchain",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["LangChainToolProtocol", "monetize_tool"]
