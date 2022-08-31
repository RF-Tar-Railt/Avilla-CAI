from __future__ import annotations

from typing import TYPE_CHECKING

from avilla.core.message import Message
from avilla.core.skeleton.message import MessageTrait
from avilla.core.trait.context import prefix, raise_for_no_namespace, scope
from avilla.core.trait.recorder import default_target, impl, pull
from avilla.core.utilles.selector import Selector

if TYPE_CHECKING:
    from graia.amnesia.message import MessageChain

    from avilla.core.relationship import Relationship


raise_for_no_namespace()

with scope("elizabeth", "friend"), prefix("friend"):

    @default_target(MessageTrait.send)
    def send_friend_message_default_target(rs: Relationship):
        return rs.ctx

    @impl(MessageTrait.send)
    async def send_friend_message(
        rs: Relationship, target: Selector, message: MessageChain, *, reply: Selector | None = None
    ) -> Selector:
        serialized_msg = await rs.protocol.serialize_message(message)
        result = await rs.account.client.send_friend_msg(
            int(target.pattern["friend"]), serialized_msg
        )
        return Selector().land(rs.land).group(target.pattern["friend"]).message(str(result[0])).random(
            str(result[1])).time(str(result[2]))

    @impl(MessageTrait.revoke)
    async def revoke_friend_message(rs: Relationship, message: Selector):
        await rs.account.client.recall_friend_msg(
            int(message.pattern["friend"]),
            (
                int(message.pattern["message"]),
                int(message.pattern["random"]),
                int(message.pattern["time"])
            )
        )
