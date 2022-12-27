from __future__ import annotations

from typing import TYPE_CHECKING

from avilla.core.trait.context import EventParserRecorder
from avilla.spec.core.application import AccountAvailable, AccountUnavailable
from cai.client.events.common import BotOfflineEvent, BotOnlineEvent

if TYPE_CHECKING:
    from ..account import CAIAccount
    from ..protocol import CAIProtocol

event = EventParserRecorder["CAIProtocol", "CAIAccount"]


@event("BotOnlineEvent")
async def bot_online_event(
    protocol: CAIProtocol, account: CAIAccount, raw: BotOnlineEvent
):
    assert int(account.id) == raw.qq
    return AccountAvailable(protocol.avilla, account), None


@event("BotOfflineEvent")
async def bot_off_event(
    protocol: CAIProtocol, account: CAIAccount, raw: BotOfflineEvent
):
    assert int(account.id) == raw.qq
    return AccountUnavailable(protocol.avilla, account), None
