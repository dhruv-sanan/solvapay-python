"""Packaging integrity tests."""

from __future__ import annotations

import importlib.resources


def test_py_typed_marker_present() -> None:
    assert importlib.resources.files("solvapay").joinpath("py.typed").is_file()
