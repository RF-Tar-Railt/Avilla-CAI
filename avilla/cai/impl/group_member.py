from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from avilla.cai.account import CAIAccount
from avilla.core.exceptions import permission_error_message
from avilla.core.selector import Selector
from avilla.core.trait.context import bounds, implement, pull
from avilla.spec.core.activity.skeleton import ActivityTrigger
from avilla.spec.core.privilege import MuteTrait, Privilege
from avilla.spec.core.privilege.metadata import MuteInfo
from avilla.spec.core.privilege.skeleton import PrivilegeTrait
from avilla.spec.core.profile import Nick, Summary
from avilla.spec.core.scene.skeleton import SceneTrait
from cai.client.models import GroupMember

if TYPE_CHECKING:
    from avilla.core.context import Context


privilege_trans = defaultdict(
    lambda: "group_member", {"owner": "group_owner", "admin": "group_admin"}
)
privilege_level = defaultdict(lambda: 0, {"owner": 2, "admin": 1})

with bounds("group.member"):

    @pull(MuteInfo)
    async def get_member_mute_info(ctx: Context, target: Selector):
        assert target is not None
        assert isinstance(ctx.account, CAIAccount)
        members: list[GroupMember] = await ctx.account.client.get_group_member_list(
            int(target.pattern["group"])
        )
        try:
            result = next(
                filter(lambda x: x.uin == int(target.pattern["member"]), members)
            )
        except StopIteration as e:
            raise RuntimeError from e
        now = datetime.now()
        return MuteInfo(
            MuteInfo,
            (result.shutup_timestamp - int(now.timestamp())) > 0,
            timedelta(seconds=(result.shutup_timestamp - int(now.timestamp()))),
            None,
        )

    @implement(MuteTrait.mute)
    async def mute_member(ctx: Context, target: Selector, duration: timedelta):
        privilege_info = await ctx.pull(Privilege, target)
        if not privilege_info.effective:
            self_privilege_info = await ctx.pull(Privilege >> Summary, ctx.self)
            raise PermissionError(
                permission_error_message(
                    f"mute@{target.path}",
                    self_privilege_info.name,
                    ["group_owner", "group_admin"],
                )
            )
        time = max(0, min(int(duration.total_seconds()), 2592000))  # Fix time parameter
        if not time:
            return
        assert isinstance(ctx.account, CAIAccount)
        await ctx.account.client.mute_member(
            int(target.pattern["group"]), int(target.pattern["member"]), time
        )

    @implement(MuteTrait.unmute)
    async def unmute_member(ctx: Context, target: Selector):
        privilege_info = await ctx.pull(Privilege, target)
        if not privilege_info.effective:
            self_privilege_info = await ctx.pull(Privilege >> Summary, ctx.self)
            raise PermissionError(
                permission_error_message(
                    f"unmute@{target.path}",
                    self_privilege_info.name,
                    ["group_owner", "group_admin"],
                )
            )
        assert isinstance(ctx.account, CAIAccount)
        await ctx.account.client.mute_member(
            int(target.pattern["group"]), int(target.pattern["member"]), 0
        )

    @pull(Summary)
    async def get_member_summary(ctx: Context, target: Selector) -> Summary:
        assert isinstance(ctx.account, CAIAccount)
        result: list[GroupMember] = await ctx.account.client.get_group_member_list(
            int(target.pattern["group"])
        )
        try:
            member = next(
                filter(lambda x: x.uin == int(target.pattern["member"]), result)
            )
        except StopIteration as e:
            raise RuntimeError from e
        return Summary(Summary, member.member_card, member.memo)

    @pull(Privilege)
    async def get_member_privilege(ctx: Context, target: Selector):
        assert isinstance(ctx.account, CAIAccount)
        result: list[GroupMember] = await ctx.account.client.get_group_member_list(
            int(target.pattern["group"])
        )
        try:
            self = next(
                filter(lambda x: x.uin == int(ctx.self.pattern["member"]), result)
            )
            member = next(
                filter(lambda x: x.uin == int(target.pattern["member"]), result)
            )
        except StopIteration as e:
            raise RuntimeError from e
        return Privilege(
            Privilege,
            privilege_level[self.role.value] > 0,
            privilege_level[self.role.value] > privilege_level[member.role.value],
        )

    @pull(Privilege >> Summary)
    async def get_member_privilege_summary_info(
        ctx: Context, target: Selector | None
    ) -> Summary:
        assert isinstance(ctx.account, CAIAccount)
        if not target:
            result: list[GroupMember] = await ctx.account.client.get_group_member_list(
                int(ctx.self.pattern["group"])
            )
            try:
                self = next(
                    filter(lambda x: x.uin == int(ctx.self.pattern["member"]), result)
                )
            except StopIteration as e:
                raise RuntimeError from e
            return Summary(
                Privilege >> Summary,
                privilege_trans[self.role.value],
                "the permission info of current account in the group",
            )
        result: list[GroupMember] = await ctx.account.client.get_group_member_list(
            int(target.pattern["group"])
        )
        try:
            member = next(
                filter(lambda x: x.uin == int(target.pattern["member"]), result)
            )
        except StopIteration as e:
            raise RuntimeError from e
        return Summary(
            Privilege >> Summary,
            privilege_trans[member.role.value],
            "the permission info of current account in the group",
        )

    @pull(Privilege >> Privilege)
    async def get_member_privilege_of_privilege(ctx: Context, target: Selector):
        assert isinstance(ctx.account, CAIAccount)
        result: list[GroupMember] = await ctx.account.client.get_group_member_list(
            int(target.pattern["group"])
        )
        try:
            member = next(
                filter(lambda x: x.uin == int(target.pattern["member"]), result)
            )
        except StopIteration as e:
            raise RuntimeError from e
        return Privilege(
            Privilege >> Privilege,
            privilege_level[member.role.value] == 2,
            privilege_level[member.role.value] == 2,
        )

    @pull(Privilege >> Privilege >> Summary)
    async def get_member_privilege_of_privilege_summary(ctx: Context, target: Selector):
        assert isinstance(ctx.account, CAIAccount)
        result: list[GroupMember] = await ctx.account.client.get_group_member_list(
            int(target.pattern["group"])
        )
        try:
            member = next(
                filter(lambda x: x.uin == int(target.pattern["member"]), result)
            )
        except StopIteration as e:
            raise RuntimeError from e
        return Summary(
            Privilege >> Privilege >> Summary,
            privilege_trans[member.role.value],
            "the permission of controling administration of the group, "
            "to be noticed that is only group owner could do this.",
        )

    @implement(PrivilegeTrait.upgrade)
    async def upgrade_member(ctx: Context, target: Selector, dest: str | None = None):
        if not (await get_member_privilege_of_privilege(ctx, target)).available:
            self_privilege_info = await ctx.pull(Privilege >> Summary, ctx.self)
            raise PermissionError(
                permission_error_message(
                    f"upgrade_permission@{target.path}",
                    self_privilege_info.name,
                    ["group_owner"],
                )
            )
        assert isinstance(ctx.account, CAIAccount)
        await ctx.account.client.set_group_admin(
            int(target.pattern["group"]), int(target.pattern["member"]), is_admin=True
        )

    @implement(PrivilegeTrait.downgrade)
    async def downgrade_member(ctx: Context, target: Selector, dest: str | None = None):
        if not (await get_member_privilege_of_privilege(ctx, target)).available:
            self_privilege_info = await ctx.pull(Privilege >> Summary, ctx.self)
            raise PermissionError(
                permission_error_message(
                    f"upgrade_permission@{target.path}",
                    self_privilege_info.name,
                    ["group_owner"],
                )
            )
        assert isinstance(ctx.account, CAIAccount)
        await ctx.account.client.set_group_admin(
            int(target.pattern["group"]), int(target.pattern["member"]), is_admin=False
        )

    @implement(SceneTrait.remove_member)
    async def remove_member(ctx: Context, target: Selector, reason: str | None = None):
        assert isinstance(ctx.account, CAIAccount)
        raise NotImplementedError

    @pull(Nick)
    async def get_member_nick(ctx: Context, target: Selector) -> Nick:
        assert isinstance(ctx.account, CAIAccount)
        result: list[GroupMember] = await ctx.account.client.get_group_member_list(
            int(target.pattern["group"])
        )
        try:
            member = next(
                filter(lambda x: x.uin == int(target.pattern["member"]), result)
            )
        except StopIteration as e:
            raise RuntimeError from e
        return Nick(
            Nick, member.name or member.nick, member.member_card, member.special_title
        )


#
# with bounds("group.member.nudge"):
#
#     @implement(ActivityTrigger.trigger)
#     async def send_member_nudge(ctx: Context, target: Selector):
#         await ctx.account.call(
#             "sendNudge",
#             {"__method__": "update", "target": int(target["member"]), "subject": int(target["group"]), "kind": "Group"},
#         )
