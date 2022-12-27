from __future__ import annotations

from collections import defaultdict
from datetime import timedelta, datetime
from typing import TYPE_CHECKING 
from cai.client.models import Group, GroupMember
from graia.amnesia.builtins.memcache import Memcache
from avilla.core.message import Message
from avilla.core.metadata import MetadataOf
from avilla.core.selector import Selector
from avilla.core.trait.context import bounds, implement, pull
from avilla.spec.core.message import MessageSend
from avilla.spec.core.privilege import MuteAllTrait, Privilege, MuteTrait
from avilla.spec.core.profile import Summary, SummaryTrait
from avilla.spec.core.scene import SceneTrait

from avilla.cai.account import CAIAccount

if TYPE_CHECKING:
    from graia.amnesia.message import __message_chain_class__
    from avilla.core.context import Context
    from ..protocol import CAIProtocol

with bounds("group"):

    @implement(MessageSend.send)
    async def send_group_message(
            ctx: Context, target: Selector, message: __message_chain_class__, *, reply: Selector | None = None
    ) -> Selector:
        if TYPE_CHECKING:
            assert isinstance(ctx.protocol, CAIProtocol)
        assert isinstance(ctx.account, CAIAccount)
        serialized_msg = await ctx.protocol.serialize_message(message, ctx, reply=reply)
        result = await ctx.account.client.send_group_msg(
            int(target.pattern["group"]),
            serialized_msg
        )
        message_metadata = Message(
            describe=Message,
            id=str(result[0]),
            scene=Selector().land(ctx.land).group(str(target.pattern["group"])),
            content=message,
            time=datetime.now(),
            sender=Selector().land(ctx.land).group(str(target.pattern["group"])).member(ctx.account.id),
        )
        message_selector = message_metadata.to_selector().random(str(result[1])).time(str(result[2]))
        ctx._collect_metadatas(message_selector, message_metadata)
        memcache = ctx.avilla.launch_manager.get_interface(Memcache)
        memcache.set(f"_cai_context.message.{message_metadata.id}", message, timedelta(seconds=300))
        return message_selector


    @implement(MuteAllTrait.mute_all)
    async def group_mute_all(ctx: Context, target: Selector):
        assert isinstance(ctx.account, CAIAccount)
        raise NotImplementedError


    @implement(MuteAllTrait.unmute_all)
    async def group_unmute_all(ctx: Context, target: Selector):
        assert isinstance(ctx.account, CAIAccount)
        raise NotImplementedError


    @implement(SceneTrait.leave)
    async def leave(ctx: Context, target: Selector):
        assert isinstance(ctx.account, CAIAccount)
        raise NotImplementedError


    @implement(SceneTrait.remove_member)
    async def remove_member(ctx: Context, target: Selector, reason: str | None = None):
        assert isinstance(ctx.account, CAIAccount)
        raise NotImplementedError


    @pull(Summary)
    async def get_summary(ctx: Context, target: Selector | None) -> Summary:
        assert target is not None
        assert isinstance(ctx.account, CAIAccount)
        group = await ctx.account.client.get_group(int(target.pattern["group"]))
        assert isinstance(group, Group)
        return Summary(describe=Summary, name=group.group_name, description=group.group_memo)

    @implement(SummaryTrait.set_name)
    async def group_set_name(ctx: Context, target: Selector, name: str):
        assert isinstance(ctx.account, CAIAccount)
        raise NotImplementedError

    @pull(Summary)
    async def get_summary(ctx: Context, target: Selector | None) -> Summary:
        assert isinstance(ctx.account, CAIAccount)
        result: list[GroupMember] = await ctx.account.client.get_group_member_list(int(ctx.self.pattern["group"]))
        try:
            self = next(filter(lambda x: x.uin == int(ctx.self.pattern["member"]), result))
        except StopIteration as e:
            raise RuntimeError from e
        if not target:
            return Summary(
                Summary,
                self.member_card,
                self.memo
            )
        try:
            member = next(filter(lambda x: x.uin == int(target.pattern["member"]), result))
        except StopIteration as e:
            raise RuntimeError from e
        return Summary(
                Summary,
                member.member_card,
                member.memo
            )

    @pull(Privilege)
    async def group_get_privilege_info(ctx: Context, target: Selector | None) -> Privilege:
        assert isinstance(ctx.account, CAIAccount)
        result: list[GroupMember] = await ctx.account.client.get_group_member_list(int(ctx.self.pattern["group"]))
        try:
            self = next(filter(lambda x: x.uin == int(ctx.account.id), result))
        except StopIteration as e:
            raise RuntimeError from e
        if target is None:
            return Privilege(
                Privilege,
                self.role.value in {"owner", "admin"},
                self.role.value in {"owner", "admin"},
            )
        try:
            member = next(filter(lambda x: x.uin == int(target.pattern["member"]), result))
        except StopIteration as e:
            raise RuntimeError from e
        return Privilege(
            Privilege,
            self.role.value in {"owner", "admin"},
            (self.role.value == "owner" and member.role.value != "owner")
            or (
                    self.role.value in {"owner", "admin"}
                    and member.role.value not in {"owner", "admin"}
            ),
        )


    #
    # @pull(Nick).of("group.member")
    # async def get_member_nick(ctx: Context, target: Selector | None) -> Nick:
    #     assert target is not None
    #     assert isinstance(ctx.account, CAIAccount)
    #     result: list[GroupMember] = await ctx.account.client.get_group_member_list(int(target.pattern["group"]))
    #     try:
    #         member = next(filter(lambda x: x.uin == int(target.pattern["member"]), result))
    #     except StopIteration as e:
    #         raise RuntimeError from e
    #     return Nick(Nick, member.name or member.nick, member.member_card, member.special_title)
    #


