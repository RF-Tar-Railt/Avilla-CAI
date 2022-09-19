from __future__ import annotations


from loguru import logger
from typing import TYPE_CHECKING
from contextlib import suppress
from cai.client.models import Friend
from graia.amnesia.message import MessageChain
from avilla.core.cell.cells import Nick, Summary
from avilla.core.skeleton.message import MessageRevoke, MessageSend
from avilla.core.trait.context import prefix, raise_for_no_namespace, scope
from avilla.core.trait.recorder import default_target, impl, pull, query
from avilla.core.utilles.selector import Selector

from avilla.cai.account import CAIAccount

if TYPE_CHECKING:

    from avilla.core.relationship import Relationship


raise_for_no_namespace()

with scope("avilla-cai", "friend"), prefix("friend"):

    @default_target(MessageSend.send)
    def send_friend_message_default_target(rs: Relationship):
        return rs.ctx

    @impl(MessageSend.send)
    async def send_friend_message(
        rs: Relationship,
        target: Selector,
        message: MessageChain,
        *,
        reply: Selector | None = None,
    ) -> Selector:
        assert isinstance(rs.account, CAIAccount)
        serialized_msg = await rs.protocol.serialize_message(message)
        result = await rs.account.client.send_friend_msg(
            int(target.pattern["friend"]), serialized_msg
        )
        name = ""
        with suppress(NotImplementedError):
            name = (await rs.pull(Summary, target)).name
        logger.info(  # TODO: wait for solution of ActiveMessage
            f"{rs.account.land.name}: [send]"
            f"[Friend({f'{name}, ' if name else ''}{target.pattern['friend']})]"
            f" <- {str(message)!r}"
        )
        return (
            Selector()
            .land(rs.land)
            .friend(target.pattern["friend"])
            .message(str(result[0]))
            .random(str(result[1]))
            .time(str(result[2]))
        )

    @impl(MessageRevoke.revoke)
    async def revoke_friend_message(rs: Relationship, message: Selector):
        assert isinstance(rs.account, CAIAccount)
        await rs.account.client.recall_friend_msg(
            int(message.pattern["friend"]),
            (
                int(message.pattern["message"]),
                int(message.pattern["random"]),
                int(message.pattern["time"]),
            ),
        )

    @pull(Nick).of("friend")
    async def get_friend_nick(rs: Relationship, target: Selector | None) -> Nick:
        assert target is not None
        assert isinstance(rs.account, CAIAccount)
        friend = await rs.account.client.get_friend(int(target.pattern["friend"]))
        assert isinstance(friend, Friend)
        return Nick(Nick, friend.nick, friend.remark, "")

    @pull(Summary).of("friend")
    async def get_summary(rs: Relationship, target: Selector | None) -> Summary:
        assert target is not None
        assert isinstance(rs.account, CAIAccount)
        friend = await rs.account.client.get_friend(int(target.pattern["friend"]))
        assert isinstance(friend, Friend)
        return Summary(
            describe=Summary, name=friend.nick, description=friend.term_description
        )

    @query(None, "friend")
    async def get_friends(rs: Relationship, upper: None, predicate: Selector):
        assert isinstance(rs.account, CAIAccount)
        result: list[Friend] = await rs.account.client.get_friend_list()
        for i in result:
            friend = Selector().friend(str(i.uin))
            if predicate.match(friend):
                yield friend
