from __future__ import annotations

from typing import TYPE_CHECKING, Any
from cai import Client
from avilla.core.account import AbstractAccount
from avilla.core.context import Context
from avilla.core.selector import Selector

if TYPE_CHECKING:
    from .protocol import CAIProtocol


class CAIAccount(AbstractAccount):
    protocol: CAIProtocol

    async def get_context(self, target: Selector, *, via: Selector | None = None) -> Context:
        # TODO: 对象存在性检查
        if "land" not in target:
            target = target.land(self.protocol.land)
        if target.path == "land.group":
            return Context(self, target, target, target.member(self.id), self.to_selector())
        elif target.path == "land.friend":
            return Context(self, target, target, self.to_selector(), self.to_selector())
        elif target.path == "land.group.member":
            return Context(
                self,
                target,
                Selector().land(self.land.name).group(target.pattern["group"]),
                Selector().land(self.land.name).group(target.pattern["group"]).member(self.id),
                self.to_selector(),
            )
        else:
            raise NotImplementedError()

    @property
    def client(self) -> Client:
        return self.protocol.service.get_client(self.id).client

    @property
    def available(self) -> bool:
        return self.client.connected

    async def call(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        return await (getattr(self.client, endpoint)(**(params or {})))
        # params = params or {}
        # method: CallMethod = params.pop("__method__")
        # if params.pop("__use_session__", True):
        #     await self.connection.status.wait_for_available()  # wait until session_key is present
        #     session_key = self.connection.status.session_key
        #     params["sessionKey"] = session_key
        # return await self.connection.call(endpoint, method, params)
