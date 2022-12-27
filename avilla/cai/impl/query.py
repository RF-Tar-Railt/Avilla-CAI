from __future__ import annotations

from typing import TYPE_CHECKING

from avilla.cai.account import CAIAccount
from avilla.core.selector import Selector
from avilla.core.trait.context import query
from cai.client.models import Friend, Group, GroupMember

if TYPE_CHECKING:
    from avilla.core.context import Context


@query("friend")
async def get_friends(ctx: Context, upper: None, predicate: Selector):
    assert isinstance(ctx.account, CAIAccount)
    result: list[Friend] = await ctx.account.client.get_friend_list()
    for i in result:
        friend = Selector().friend(str(i.uin))
        if predicate.match(friend):
            yield friend


@query("group")
async def get_groups(ctx: Context, upper: None, predicate: Selector):
    assert isinstance(ctx.account, CAIAccount)
    result: list[Group] = await ctx.account.client.get_group_list()
    for i in result:
        group = Selector().group(str(i.group_id))
        if predicate.match(group):
            yield group


@query("group", "member")
async def get_group_members(ctx: Context, upper: Selector, predicate: Selector):
    assert isinstance(ctx.account, CAIAccount)
    result: list[GroupMember] = await ctx.account.client.get_group_member_list(
        int(upper.pattern["group"])
    )
    for i in result:
        member = Selector().group(str(i.group.group_id)).member(str(i.member_uin))
        if predicate.match(member):
            yield member
