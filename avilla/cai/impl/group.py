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
        assert target is not None
        group = await rs.account.client.get_group(int(target.pattern["group"]))
        assert isinstance(group, Group)
        return Summary(describe=Summary, name=group.group_name, description=group.group_memo)

    @pull(Summary).of("group.member")
    async def get_summary(rs: Relationship, target: Selector | None) -> Summary:
        result: list[GroupMember] = await rs.account.client.get_group_member_list(int(target.pattern["group"]))
        try:
            self = next(filter(lambda x: x.uin == int(rs.account.id), result))
        except StopIteration as e:
            raise RuntimeError from e
        if not target:
            return Summary(
                Summary,
                self.name,
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

    @impl(SummaryTrait.set_name).pin("group")
    async def group_set_name(rs: Relationship, target: Selector, name: str):
        raise NotImplementedError


    @pull(Privilege).of("group.member")
    async def group_get_privilege_info(rs: Relationship, target: Selector | None) -> Privilege:
        result: list[GroupMember] = await rs.account.client.get_group_member_list(int(target.pattern["group"]))
        try:
            self = next(filter(lambda x: x.uin == int(rs.account.id), result))
        except StopIteration as e:
            raise RuntimeError from e
        if not target:
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


    @pull(Privilege >> Summary).of("group.member")
    async def group_get_privilege_summary_info(rs: Relationship, target: Selector | None) -> Summary:
        privilege_trans = defaultdict(lambda: "group_member", {"owner": "group_owner", "admin": "group_admin"})
        result: list[GroupMember] = await rs.account.client.get_group_member_list(int(target.pattern["group"]))
        try:
            self = next(filter(lambda x: x.uin == int(rs.account.id), result))
        except StopIteration as e:
            raise RuntimeError from e
        if not target:
            return Summary(
                Privilege >> Summary,
                privilege_trans[self.role.value],
                "the permission info of current account in the group",
            )
        try:
            member = next(filter(lambda x: x.uin == int(target.pattern["member"]), result))
        except StopIteration as e:
            raise RuntimeError from e
        return Summary(
            Privilege >> Summary,
            privilege_trans[member.role.value],
            "the permission info of current account in the group",
        )


    @impl(PrivilegeTrait.upgrade)
    async def group_set_admin(rs: Relationship, target: Selector, dest: str | None):
        assert target.follows("group.member")
        await rs.account.client.set_group_admin(
            int(target.pattern['group']),
            int(target.pattern['member']),
            is_admin=True
        )


    @impl(PrivilegeTrait.downgrade)
    async def group_set_admin(rs: Relationship, target: Selector, dest: str | None):
        assert target.follows("group.member")
        await rs.account.client.set_group_admin(
            int(target.pattern['group']),
            int(target.pattern['member']),
            is_admin=False
        )


    @pull(Nick).of("group.member")
    async def get_member_nick(rs: Relationship, target: Selector | None) -> Nick:
        assert target is not None
        result: list[GroupMember] = await rs.account.client.get_group_member_list(int(target.pattern["group"]))
        try:
            member = next(filter(lambda x: x.uin == int(target.pattern["member"]), result))
        except StopIteration as e:
            raise RuntimeError from e
        return Nick(Nick, member.name or member.nick, member.member_card, member.special_title)


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
