from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from avilla.core.context import Context
from avilla.core.request import Request
from avilla.core.selector import Selector
from avilla.core.trait.context import EventParserRecorder
from avilla.spec.core.request import RequestReceived
from cai.client.events.group import JoinGroupRequestEvent

if TYPE_CHECKING:
    from ..account import CAIAccount
    from ..protocol import CAIProtocol

event = EventParserRecorder["CAIProtocol", "CAIAccount"]


@event("JoinGroupRequestEvent")
async def join_group_request_event(
    protocol: CAIProtocol, account: CAIAccount, raw: JoinGroupRequestEvent
):
    land = Selector().land(protocol.land.name)
    group = land.group(str(raw.group_id))
    sender = (
        land.friend(str(raw.from_uin))
        if raw.is_invited
        else land.stranger(str(raw.from_uin))
    )
    context = Context(
        account=account,
        client=sender,
        endpoint=group,
        scene=group,
        selft=group.member(account.id),
    )
    request = Request(
        Request,
        f"{raw.seq}|{raw.time}|{raw.uid}",
        protocol.land,
        group,
        sender,
        account,
        datetime.fromtimestamp(float(raw.time)),
        response="join_group_request",
    )
    return RequestReceived(context, request), context
