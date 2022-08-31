from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import TYPE_CHECKING
from cai.client.models import Group, GroupMember

from avilla.core.cell.cells import Nick, Privilege, Summary
from avilla.core.exceptions import permission_error_message
from avilla.core.message import Message
from avilla.core.skeleton.message import MessageTrait
from avilla.core.skeleton.privilege import MuteTrait, PrivilegeTrait
from avilla.core.skeleton.scene import SceneTrait
from avilla.core.skeleton.summary import SummaryTrait
from avilla.core.trait.context import prefix, raise_for_no_namespace, scope
from avilla.core.trait.recorder import default_target, impl, pull, query
from avilla.core.utilles.selector import Selector

if TYPE_CHECKING:
    from graia.amnesia.message import MessageChain

    from avilla.core.relationship import Relationship

raise_for_no_namespace()

with scope("avilla-cai", "group"), prefix("group"):
    @default_target(MessageTrait.send)
    def send_group_message_default_target(rs: Relationship):
        return rs.mainline


    @impl(MessageTrait.send)
    async def send_group_message(
            rs: Relationship, target: Selector, message: MessageChain, *, reply: Selector | None = None
    ) -> Selector:
        serialized_msg = await rs.protocol.serialize_message(message)
        result = await rs.account.client.send_group_msg(
            int(target.pattern["group"]),
            serialized_msg
        )
        return Selector().land(rs.land).group(target.pattern["group"]).message(str(result[0])).random(
            str(result[1])).time(str(result[2]))


    @impl(MessageTrait.revoke)
    async def revoke_group_message(rs: Relationship, message: Selector):
        await rs.account.client.recall_group_msg(
            int(message.pattern["group"]),
            (
                int(message.pattern["message"]),
                int(message.pattern["random"]),
                int(message.pattern["time"])
            )
        )


    @impl(MuteTrait.mute)
    async def mute_member(rs: Relationship, target: Selector, duration: timedelta):
        privilege_info = await rs.pull(Privilege, target)
        if not privilege_info.effective:
            self_privilege_info = await rs.pull(Privilege >> Summary, rs.self)
            raise PermissionError(
                permission_error_message(
                    f"Mute.mute@{target.path}", self_privilege_info.name, ["group_owner", "group_admin"]
                )
            )
        time = max(0, min(int(duration.total_seconds()), 2592000))  # Fix time parameter
        if not time:
            return
        await rs.account.client.mute_member(
            int(target.pattern["group"]),
            int(target.pattern["member"]),
            time
        )


    @impl(MuteTrait.unmute)
    async def unmute_member(rs: Relationship, target: Selector):
        raise NotImplementedError


    @impl(MuteTrait.mute_all)
    async def group_mute_all(rs: Relationship, target: Selector):
        raise NotImplementedError


    @impl(MuteTrait.unmute_all)
    async def group_unmute_all(rs: Relationship, target: Selector):
        raise NotImplementedError


    @impl(SceneTrait.leave).pin("group")
    async def leave(rs: Relationship, target: Selector):
        raise NotImplementedError


    @impl(SceneTrait.remove_member)
    async def remove_member(rs: Relationship, target: Selector, reason: str | None = None):
        raise NotImplementedError


    @pull(Summary).of("group")
    async def get_summary(rs: Relationship, target: Selector | None) -> Summary:
        raise NotImplementedError


    @impl(SummaryTrait.set_name).pin("group")
    async def group_set_name(rs: Relationship, target: Selector, name: str):
        raise NotImplementedError


    @pull(Privilege).of("group.member")
    async def group_get_privilege_info(rs: Relationship, target: Selector | None) -> Privilege:
        raise NotImplementedError


    @pull(Privilege >> Summary).of("group.member")
    async def group_get_privilege_summary_info(rs: Relationship, target: Selector | None) -> Summary:
        raise NotImplementedError


    @pull(Nick).of("group.member")
    async def get_member_nick(rs: Relationship, target: Selector | None) -> Nick:
        raise NotImplementedError


    @query(None, "group")
    async def get_groups(rs: Relationship, upper: None, predicate: Selector):
        result: list[Group] = rs.account.client.get_group_list()
        for i in result:
            group = Selector().group(str(i.group_id))
            if predicate.match(group):
                yield group


    @query("group", "member")
    async def get_group_members(rs: Relationship, upper: Selector, predicate: Selector):
        result: list[GroupMember] = await rs.account.client.get_group_member_list(int(upper.pattern["group"]))
        for i in result:
            member = Selector().group(str(i.group.group_id)).member(str(i.member_uin))
            if predicate.match(member):
                yield member
