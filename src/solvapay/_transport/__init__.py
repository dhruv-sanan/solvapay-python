"""Transport Protocol shapes (HLD V1.4). Not part of the public API."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, ClassVar, Iterable, Mapping, Protocol, runtime_checkable


class Headers:
    """Case-insensitive header mapping (HLD V1.4 T5).

    Stores keys in lowercase. Injection and redaction are case-insensitive.
    """

    def __init__(self, raw: dict[str, str] | None = None) -> None:
        self._data: dict[str, str] = {}
        if raw:
            for key, value in raw.items():
                self._data[key.lower()] = value

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._data.get(key.lower(), default)

    def __getitem__(self, key: str) -> str:
        return self._data[key.lower()]

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            return key.lower() in self._data
        return False

    def items(self) -> Iterable[tuple[str, str]]:
        return self._data.items()

    def to_dict(self) -> dict[str, str]:
        return dict(self._data)

    def __repr__(self) -> str:
        return f"Headers({self._data!r})"


@dataclass(frozen=True)
class Timeout:
    connect: float = 5.0
    read: float = 30.0
    write: float = 30.0
    pool: float = 10.0


@dataclass(frozen=True)
class Context:
    deadline: float | None = None
    cancel_token: object | None = None
    trace_id: str | None = None
    extras: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RequestSpec:
    """Immutable request descriptor (HLD V1.4).

    - json is a Mapping; never mutate — use dataclasses.replace() (HLD T1).
    - No 'retryable' field; retry policy consults OpSpec.retry_safety (HLD T4).
    - params: query-string dict; resolved before reaching the wire.
    """

    method: str
    url: str
    headers: Headers
    json: Mapping[str, Any] | None
    timeout: Timeout = field(default_factory=Timeout)
    context: Context = field(default_factory=Context)
    params: dict[str, Any] | None = None


@dataclass(frozen=True)
class ResponseMetadata:
    status_code: int
    headers: Headers
    elapsed_ms: float
    middleware_trace: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResponseSpec:
    body: dict[str, Any]
    metadata: ResponseMetadata


@runtime_checkable
class Transport(Protocol):
    protocol_version: ClassVar[int]  # must be 1 (HLD T6)

    def send(self, spec: RequestSpec) -> ResponseSpec: ...

    def close(self) -> None: ...


@runtime_checkable
class AsyncTransport(Protocol):
    protocol_version: ClassVar[int]

    async def send(self, spec: RequestSpec) -> ResponseSpec: ...

    async def aclose(self) -> None: ...  # HLD AL2: cascade required
