from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Coroutine, Any
from graia.amnesia.message import MessageChain
from cai.client import Event
from cai.client.events.common import GroupMessage, PrivateMessage, TempMessage
from cai.client.message_service.models import ReplyElement
from loguru import logger

from avilla.core.event.message import MessageReceived
from avilla.core.message import Message
from avilla.core.utilles.event_parser import AbstractEventParser, event
from avilla.core.utilles.selector import Selector
from avilla.core.event import AvillaEvent

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
    event_parser: dict[str, Callable[[Any, CAIProtocol, CAIAccount, Event], Coroutine[None, None, AvillaEvent | None]]] = {}

    def get_event_type(self, raw: Event) -> str:
        return raw.type

    async def parse_event(
        self, protocol: CAIProtocol, account: CAIAccount, raw: Event, *, error: bool = False
    ) -> AvillaEvent | None:
        event_type = self.get_event_type(raw)
        deserializer = self.event_parser.get(event_type)
        if deserializer is None:
            if error:
                raise NotImplementedError(f"Event type {event_type} is not supported.")
            logger.warning(f"Event type {event_type} is not supported by {self.__class__.__name__}", raw)
            return
        return await deserializer(self, protocol, account, raw)

    @event("group_message")
    async def group_message(self, protocol: CAIProtocol, account: CAIAccount, raw: GroupMessage):
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
                content=MessageChain(await protocol.message_deserializer.parse_sentence(protocol, message_chain)),
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
    async def friend_message(self, protocol: CAIProtocol, account: CAIAccount, raw: PrivateMessage):
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
                content=MessageChain(await protocol.message_deserializer.parse_sentence(protocol, message_chain)),
                time=datetime.fromtimestamp(source.time),
                reply=Selector().land(protocol.land.name).friend(str(raw.from_uin)).message(str(quote.id))
                if quote is not None
                else None,
            ),
            account=account,
        )

    @event("temp_message")
    async def temp_message(self, protocol: CAIProtocol, account: CAIAccount, raw: TempMessage):
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
                content=MessageChain(await protocol.message_deserializer.parse_sentence(protocol, message_chain)),
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
