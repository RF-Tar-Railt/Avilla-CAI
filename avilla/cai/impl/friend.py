from __future__ import annotations

from datetime import datetime, timedelta

from loguru import logger
from typing import TYPE_CHECKING
from contextlib import suppress
from cai.client.models import Friend
from graia.amnesia.builtins.memcache import Memcache
from avilla.cai.account import CAIAccount


from avilla.core.message import Message
from avilla.core.selector import Selector
from avilla.core.trait.context import bounds, implement, pull
from avilla.spec.core.message import MessageRevoke, MessageSend
from avilla.spec.core.profile.metadata import Nick, Summary

if TYPE_CHECKING:
    from graia.amnesia.message import __message_chain_class__

    from avilla.core.context import Context
    from ..protocol import CAIProtocol


with bounds("friend"):

    @implement(MessageSend.send)
    async def send_friend_message(
        ctx: Context, target: Selector, message: __message_chain_class__, *, reply: Selector | None = None
    ) -> Selector:
        if TYPE_CHECKING:
            assert isinstance(ctx.protocol, CAIProtocol)
        assert isinstance(ctx.account, CAIAccount)
        serialized_msg = await ctx.protocol.serialize_message(message, ctx, reply=reply)
        result = await ctx.account.client.send_friend_msg(
            int(target.pattern["friend"]), serialized_msg
        )
        name = ""
        with suppress(NotImplementedError):
            name = (await ctx.pull(Summary, target)).name
        logger.info(  # TODO: wait for solution of ActiveMessage
            f"{ctx.account.land.name}: [send]"
            f"[Friend({f'{name}, ' if name else ''}{target.pattern['friend']})]"
            f" <- {str(message)!r}"
        )
        message_metadata = Message(
            describe=Message,
            id=str(result[0]),
            scene=Selector().land(ctx.land).friend(str(target.pattern["friend"])),
            content=message,
            time=datetime.now(),
            sender=ctx.account.to_selector(),
        )
        message_selector = message_metadata.to_selector().random(str(result[1])).time(str(result[2]))
        ctx._collect_metadatas(message_selector, message_metadata)
        memcache = ctx.avilla.launch_manager.get_interface(Memcache)
        memcache.set(f"_cai_context.message.{message_metadata.id}", message, timedelta(seconds=300))
        return message_selector


    @pull(Nick)
    async def get_friend_nick(ctx: Context, target: Selector | None) -> Nick:
        assert target is not None
        assert isinstance(ctx.account, CAIAccount)
        friend = await ctx.account.client.get_friend(int(target.pattern["friend"]))
        assert isinstance(friend, Friend)
        return Nick(Nick, friend.nick, friend.remark, "")

    @pull(Summary)
    async def get_summary(ctx: Context, target: Selector | None) -> Summary:
        assert target is not None
        assert isinstance(ctx.account, CAIAccount)
        friend = await ctx.account.client.get_friend(int(target.pattern["friend"]))
        assert isinstance(friend, Friend)
        return Summary(
            describe=Summary, name=friend.nick, description=friend.term_description
        )

