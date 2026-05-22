"""CustomerRef resolvers — extract customer_ref from call args/kwargs (HLD V1.6 PW2).

Protocol is private; built-in resolvers are public.
"""

from __future__ import annotations

from typing import Any


class KwargsResolver:
    """Resolve customer_ref from kwargs by name."""

    def __init__(self, key: str = "customer_ref") -> None:
        self._key = key

    def resolve(self, *args: Any, **kwargs: Any) -> str:
        val = kwargs.get(self._key)
        if not isinstance(val, str):
            raise ValueError(
                f"KwargsResolver: expected str kwarg '{self._key}', got {type(val).__name__}"
            )
        return val


class PositionalResolver:
    """Resolve customer_ref from positional args by index."""

    def __init__(self, index: int = 0) -> None:
        self._index = index

    def resolve(self, *args: Any, **kwargs: Any) -> str:
        try:
            val = args[self._index]
        except IndexError as exc:
            raise ValueError(
                f"PositionalResolver: no positional arg at index {self._index}"
            ) from exc
        if not isinstance(val, str):
            raise ValueError(
                f"PositionalResolver: expected str at index {self._index}, got {type(val).__name__}"
            )
        return val


class PydanticBodyResolver:
    """Resolve customer_ref from a Pydantic model kwarg."""

    def __init__(self, body_arg: str = "body", field: str = "customer_ref") -> None:
        self._body_arg = body_arg
        self._field = field

    def resolve(self, *args: Any, **kwargs: Any) -> str:
        body = kwargs.get(self._body_arg)
        if body is None:
            raise ValueError(
                f"PydanticBodyResolver: kwarg '{self._body_arg}' not found"
            )
        val = getattr(body, self._field, None)
        if not isinstance(val, str):
            raise ValueError(
                f"PydanticBodyResolver: field '{self._field}' is not a str"
            )
        return val
