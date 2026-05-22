"""Merchant + Platform resource namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING

from solvapay._transport import Headers, RequestSpec
from solvapay.models import Merchant, PlatformConfig
from solvapay.operations._registry import REGISTRY

if TYPE_CHECKING:
    from solvapay._transport import AsyncTransport, Transport


class MerchantOperations:
    def __init__(
        self,
        *,
        sync_transport: Transport | None,
        async_transport: AsyncTransport | None,
    ) -> None:
        self._sync = sync_transport
        self._async = async_transport

    def get(self) -> Merchant:
        assert self._sync is not None
        resp = self._sync.send(
            RequestSpec(
                method="GET",
                url=REGISTRY["merchant.get"].path_template,
                headers=Headers(),
                json=None,
            )
        )
        return Merchant.model_validate(resp.body)

    def get_platform_config(self) -> PlatformConfig:
        assert self._sync is not None
        resp = self._sync.send(
            RequestSpec(
                method="GET",
                url=REGISTRY["platform.get_config"].path_template,
                headers=Headers(),
                json=None,
            )
        )
        return PlatformConfig.model_validate(resp.body)

    async def aget(self) -> Merchant:
        assert self._async is not None
        resp = await self._async.send(
            RequestSpec(
                method="GET",
                url=REGISTRY["merchant.get"].path_template,
                headers=Headers(),
                json=None,
            )
        )
        return Merchant.model_validate(resp.body)

    async def aget_platform_config(self) -> PlatformConfig:
        assert self._async is not None
        resp = await self._async.send(
            RequestSpec(
                method="GET",
                url=REGISTRY["platform.get_config"].path_template,
                headers=Headers(),
                json=None,
            )
        )
        return PlatformConfig.model_validate(resp.body)
