from __future__ import annotations

from typing import TYPE_CHECKING

from avilla.core.context import Context
from avilla.core.event import RelationshipCreated, RelationshipDestroyed
from avilla.core.selector import Selector
from avilla.core.trait.context import EventParserRecorder
from cai.client.events.group import (
    GroupLuckyCharacterChangedEvent,
    GroupLuckyCharacterClosedEvent,
    GroupLuckyCharacterInitEvent,
    GroupLuckyCharacterNewEvent,
    GroupLuckyCharacterOpenedEvent,
    GroupMemberJoinedEvent,
    GroupMemberLeaveEvent,
    GroupMemberMutedEvent,
    GroupMemberPermissionChangeEvent,
    GroupMemberSpecialTitleChangedEvent,
    GroupMemberUnMutedEvent,
    GroupNameChangedEvent,
    TransferGroupEvent,
)

if TYPE_CHECKING:
    from ..account import CAIAccount
    from ..protocol import CAIProtocol

event = EventParserRecorder["CAIProtocol", "CAIAccount"]


@event("GroupMemberJoinedEvent")
async def group_member_joined_event(
    protocol: CAIProtocol, account: CAIAccount, raw: GroupMemberJoinedEvent
):
    group = Selector().land(protocol.land.name).group(str(raw.group_id))
    member = group.member(str(raw.uin))
    context = Context(
        account=account,
        client=member,
        endpoint=group,
        scene=group,
        selft=group.member(account.id),
    )
    return RelationshipCreated(context, member, group, context.self), context


@event("GroupMemberLeaveEvent")
async def group_member_leave_event(
    protocol: CAIProtocol, account: CAIAccount, raw: GroupMemberLeaveEvent
):
    group = Selector().land(protocol.land.name).group(str(raw.group_id))
    member = group.member(str(raw.uin))
    context = Context(
        account=account,
        client=member,
        endpoint=group,
        scene=group,
        selft=group.member(account.id),
    )
    res = RelationshipDestroyed(context, member, group, context.self)
    if raw.operator and raw.operator != raw.uin:
        res.mediums.append(group.member(str(raw.operator)))
    return res, context
