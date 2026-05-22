"""Tests: stable/experimental/deprecated return identity (HLD V1.2 SM1)."""

from __future__ import annotations

import pytest

from solvapay._stability import MANIFEST, deprecated, experimental, stable


class _TestClass:
    pass


def test_stable_returns_identity() -> None:
    result = stable(_TestClass)
    assert result is _TestClass


def test_stable_isinstance_works() -> None:
    cls = stable(_TestClass)
    assert isinstance(cls(), _TestClass)


def test_stable_registers_in_manifest() -> None:
    class _Fresh:
        pass

    stable(_Fresh)
    names = {name for _, name in MANIFEST}
    assert "_Fresh" in names


def test_experimental_returns_identity() -> None:
    class _Exp:
        pass

    with pytest.warns(RuntimeWarning):
        result = experimental(_Exp)
    assert result is _Exp


def test_experimental_warns_once_per_process() -> None:
    import warnings

    class _Exp2:
        pass

    with pytest.warns(RuntimeWarning):
        experimental(_Exp2)

    # Second call to same symbol: no warning (once-per-process)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        experimental(_Exp2)
    runtime_warns = [w for w in caught if issubclass(w.category, RuntimeWarning)]
    assert len(runtime_warns) == 0, "experimental() should only warn once per symbol"


def test_deprecated_returns_identity() -> None:
    class _Dep:
        pass

    result = deprecated(removed_in="2.0")(_Dep)
    assert result is _Dep


def test_deprecated_registers_in_manifest() -> None:
    class _Dep2:
        pass

    deprecated(removed_in="3.0")(_Dep2)
    records = {name: rec for (_, name), rec in MANIFEST.items()}
    assert "_Dep2" in records
    assert records["_Dep2"].removed_in == "3.0"
    assert records["_Dep2"].tier == "deprecated"
