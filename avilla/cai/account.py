from __future__ import annotations

from typing import TYPE_CHECKING, Any
from cai import Client
from avilla.core.account import AbstractAccount
from avilla.core.relationship import Relationship
from avilla.core.utilles.selector import Selector

if TYPE_CHECKING:
    from .protocol import CAIProtocol


class CAIAccount(AbstractAccount):
    protocol: CAIProtocol

    async def get_relationship(self, target: Selector, *, via: Selector | None = None) -> Relationship:
        # TODO: 对象存在性检查
        if "land" not in target:
            target = Selector().mixin(f"land.{target.path}", target)
        if target.path == "land.group":
            return Relationship(self.protocol, target, target, target.copy().member(self.id), self)
        elif target.path == "land.friend":
            return Relationship(self.protocol, target, target, self.to_selector(), self)
        elif target.path == "land.group.member":
            return Relationship(
                self.protocol,
                target,
                Selector().land(self.land.name).group(target.pattern["group"]),
                Selector().land(self.land.name).group(target.pattern["group"]).member(self.id),
                self,
            )
        else:
            raise NotImplementedError()

    @property
    def client(self) -> Client:
        return self.protocol.service.get_client(self.id)

    @property
    def available(self) -> bool:
        return self.client.connected

    async def call(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        ...
        # params = params or {}
        # method: CallMethod = params.pop("__method__")
        # if params.pop("__use_session__", True):
        #     await self.connection.status.wait_for_available()  # wait until session_key is present
        #     session_key = self.connection.status.session_key
        #     params["sessionKey"] = session_key
        # return await self.connection.call(endpoint, method, params)
