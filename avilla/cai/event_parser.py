from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Coroutine, Any
from graia.amnesia.message import MessageChain
from cai.client import Event
from cai.client.events.group import GroupMessageRecalledEvent, GroupNudgeEvent
from cai.client.events.common import (
    GroupMessage,
    PrivateMessage,
    TempMessage,
    BotOnlineEvent,
    BotOfflineEvent,
    NudgeEvent,
)
from cai.client.message_service.models import ReplyElement
from loguru import logger

from avilla.core.event import AvillaEvent
from avilla.core.event.lifecycle import AccountAvailable, AccountUnavailable
from avilla.core.event.message import MessageReceived, MessageRevoked
from avilla.core.event.activity import ActivityTrigged
from avilla.core.message import Message
from avilla.core.utilles.event_parser import AbstractEventParser, event
from avilla.core.utilles.selector import Selector


if TYPE_CHECKING:
    from .account import CAIAccount
    from .protocol import CAIProtocol


@dataclass
class _Source:
    id: int
    time: int


@dataclass
class _Quote:
    id: int
    sender_id: int


class CAIEventParser(AbstractEventParser["CAIProtocol"]):
    event_parser: dict[
        str,
        Callable[
            [Any, CAIProtocol, CAIAccount, Event],
            Coroutine[None, None, AvillaEvent | None],
        ],
    ] = {}

    def get_event_type(self, raw: Event) -> str:
        return raw.type

    async def parse_event(
        self,
        protocol: CAIProtocol,
        account: CAIAccount,
        raw: Event,
        *,
        error: bool = False,
    ) -> AvillaEvent | None:
        event_type = self.get_event_type(raw)
        deserializer = self.event_parser.get(event_type)
        if deserializer is None:
            if error:
                raise NotImplementedError(f"Event type {event_type} is not supported.")
            logger.warning(
                f"Event type {event_type} is not supported by {self.__class__.__name__}",
                raw,
            )
            return
        return await deserializer(self, protocol, account, raw)

    @event("BotOnlineEvent")
    async def bot_online_event(
        self, protocol: CAIProtocol, account: CAIAccount, raw: BotOnlineEvent
    ):
        assert int(account.id) == raw.qq
        return AccountAvailable(account)

    @event("BotOfflineEvent")
    async def bot_online_event(
        self, protocol: CAIProtocol, account: CAIAccount, raw: BotOfflineEvent
    ):
        assert int(account.id) == raw.qq
        return AccountUnavailable(account)

    @event("group_message")
    async def group_message(
        self, protocol: CAIProtocol, account: CAIAccount, raw: GroupMessage
    ):
        message_chain = raw.message
        source = _Source(raw.seq, raw.time)
        quote = None
        for i in message_chain:
            if isinstance(i, ReplyElement):
                quote = _Quote(i.seq, i.sender)
                # quote = _Quote(i["id"], i["groupId"], i["senderId"], i["targetId"], i["origin"])
        if source is None:
            raise ValueError("Source not found.")
        return MessageReceived(
            message=Message(
                describe=Message,
                id=str(source.id),
                mainline=Selector().land(protocol.land.name).group(str(raw.group_id)),
                sender=Selector()
                .land(protocol.land.name)
                .group(str(raw.group_id))
                .member(str(raw.from_uin)),
                content=MessageChain(
                    await protocol.message_deserializer.parse_sentence(
                        protocol, message_chain
                    )
                ),
                time=datetime.fromtimestamp(source.time),
                reply=Selector()
                .land(protocol.land.name)
                .group(str(raw.group_id))
                .message(str(quote.id))
                if quote is not None
                else None,
            ),
            account=account,
        )

    @event("private_message")
    async def private_message(
        self, protocol: CAIProtocol, account: CAIAccount, raw: PrivateMessage
    ):
        message_chain = raw.message
        source = _Source(raw.seq, raw.time)
        quote = None
        for i in message_chain:
            if isinstance(i, ReplyElement):
                quote = _Quote(i.seq, i.sender)
        if source is None:
            raise ValueError("Source not found.")
        return MessageReceived(
            message=Message(
                describe=Message,
                id=str(source.id),
                mainline=Selector().land(protocol.land.name).friend(str(raw.from_uin)),
                sender=Selector().land(protocol.land.name).friend(str(raw.from_uin)),
                content=MessageChain(
                    await protocol.message_deserializer.parse_sentence(
                        protocol, message_chain
                    )
                ),
                time=datetime.fromtimestamp(source.time),
                reply=Selector()
                .land(protocol.land.name)
                .friend(str(raw.from_uin))
                .message(str(quote.id))
                if quote is not None
                else None,
            ),
            account=account,
        )

    @event("temp_message")
    async def temp_message(
        self, protocol: CAIProtocol, account: CAIAccount, raw: TempMessage
    ):
        message_chain = raw.message
        source = _Source(raw.seq, raw.time)
        quote = None
        for i in message_chain:
            if isinstance(i, ReplyElement):
                quote = _Quote(i.seq, i.sender)
        if source is None:
            raise ValueError("Source not found.")
        return MessageReceived(
            message=Message(
                describe=Message,
                id=str(source.id),
                mainline=Selector()
                .land(protocol.land.name)
                .group(str(raw.group_id))
                .member(str(raw.from_uin)),
                sender=Selector()
                .land(protocol.land.name)
                .group(str(raw.group_id))
                .member(str(raw.from_uin)),
                content=MessageChain(
                    await protocol.message_deserializer.parse_sentence(
                        protocol, message_chain
                    )
                ),
                time=datetime.fromtimestamp(source.time),
                reply=Selector()
                .land(protocol.land.name)
                .group(str(raw.group_id))
                .member(str(raw.from_uin))
                .message(str(quote.id))
                if quote is not None
                else None,
            ),
            account=account,
        )

    @event("GroupMessageRecalledEvent")
    async def group_message_recall(
        self, protocol: CAIProtocol, account: CAIAccount, raw: GroupMessageRecalledEvent
    ):
        return MessageRevoked(
            message=Selector()
            .land(protocol.land)
            .group(str(raw.group_id))
            .message(str(raw.msg_seq))
            .random(str(raw.msg_random))
            .time(str(raw.msg_time)),
            operator=Selector()
            .land(protocol.land)
            .group(str(raw.group_id))
            .member(str(raw.operator_id)),
            account=account,
            time=datetime.fromtimestamp(raw.msg_time),
        )

    @event("NudgeEvent")
    async def nudge_event(
        self, protocol: CAIProtocol, account: CAIAccount, raw: NudgeEvent
    ):
        nudge = ActivityTrigged(account)
        nudge.id = Selector().activity("nudge_trigger")
        nudge.activity = Selector().nudge(raw.action)
        if raw.group:
            nudge.mainline = Selector().group(str(raw.group))
            nudge.trigger = Selector().group(str(raw.group)).member(str(raw.sender))
            nudge.extra['target'] = Selector().group(str(raw.group)).member(str(raw.target))
        else:
            nudge.mainline = Selector().friend(str(raw.sender))
            nudge.trigger = Selector().friend(str(raw.sender))
            nudge.extra['target'] = Selector().friend(str(raw.target))
        return nudge

    @event("GroupNudgeEvent")
    async def group_nudge_event(
        self, protocol: CAIProtocol, account: CAIAccount, raw: GroupNudgeEvent
    ):
        """
        GroupNudgeEvent(
            group_id=931587979,
            template_id=1133,
            template_text='
                <gtip align="center">
                <qq uin="3165388245" col="1" nm="" />
                <img src="http://tianquan.gtimg.cn/nudgeeffect/item/34/client.gif" jp="https://zb.vip.qq.com/v2/pages/nudgeMall?_wv=2&amp;actionId=9&amp;effectId=34" alt="捏了捏"/>
                <qq uin="3542928737" col="1" nm="" tp="0"/>
                <nor txt="的百合铃并被挨了一拳"/>
                </gtip>
            ',
            template_params={
                'nick_str1': '',
                'nick_str2': '',
                'uin_str1': '3165388245',
                'uin_str2': '3542928737',
                'type_str2': '0',
                'suffix_str': '的百合铃并被挨了一拳',
                'action_img_url': 'http://tianquan.gtimg.cn/nudgeeffect/item/34/client.gif',
                'alt_str1': '捏了捏',
                'jp_str1': 'https://zb.vip.qq.com/v2/pages/nudgeMall?_wv=2&amp;actionId=9&amp;effectId=34'
            }
        )

        """
        nudge = ActivityTrigged(account)
        nudge.id = Selector().activity("nudge_trigger")
        nudge.activity = Selector().nudge(str(raw.template_id)).action(raw.action_text).suffix(raw.suffix_text)
        nudge.mainline = Selector().group(str(raw.group_id))
        nudge.trigger = Selector().group(str(raw.group_id)).member(str(raw.sender_id))
        nudge.extra['target'] = Selector().group(str(raw.group_id)).member(str(raw.receiver_id))
        return nudge
