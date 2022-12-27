from __future__ import annotations

from typing import Awaitable, Callable, TypedDict

from avilla.cai.account import CAIAccount
from avilla.cai.client import CAIClient
from avilla.cai.config import CAIConfig
from avilla.cai.service import CAIService
from avilla.core.application import Avilla
from avilla.core.context import Context
from avilla.core.event import AvillaEvent
from avilla.core.message import Message
from avilla.core.platform import Abstract, Land, Platform
from avilla.core.protocol import BaseProtocol
from avilla.core.selector import Selector
from avilla.core.trait.context import ElementParse, EventParse, wrap_artifacts
from cai.client.events import Event as CAIEvent
from cai.client.message_service.models import Element as CAIElement
from cai.client.message_service.models import ReplyElement
from graia.amnesia.message import __message_chain_class__
from graia.amnesia.message.element import Element
from graia.amnesia.builtins.memcache import MemcacheService, Memcache
from loguru import logger
from typing_extensions import TypeAlias

from .trait import ElementResumer, ElementResume

class MessageDeserializeResult(TypedDict):
    content: list[Element]
    reply: str | None


EventParser: TypeAlias = "Callable[[CAIProtocol, CAIAccount, CAIEvent], Awaitable[tuple[AvillaEvent, Context]]]"
ElementParser: TypeAlias = Callable[[Context, CAIElement], Awaitable[Element]]


class CAIProtocol(BaseProtocol):
    platform = Platform(
        Land(
            "avilla-cai",
            [{"name": "GraiaxCommunity"}],
            humanized_name="Avilla-CAI - CAI for avilla",
        ),
        Abstract(
            protocol="cai",
            maintainers=[{"name": "wyapx"}, {"name": "yanyongyu"}],
            humanized_name="CAI - Another Bot Framework for Tencent QQ Written in Python",
        ),
    )

    with wrap_artifacts() as implementations:
        import avilla.cai.impl as _  # noqa
        import avilla.cai.impl.friend as _  # noqa
        import avilla.cai.impl.friend_message as _  # noqa
        import avilla.cai.impl.group as _  # noqa
        import avilla.cai.impl.group_member as _  # noqa
        import avilla.cai.impl.group_message as _  # noqa
        import avilla.cai.impl.query as _  # noqa

    with wrap_artifacts() as event_parsers:
        import avilla.cai.event.message as _  # noqa

    with wrap_artifacts() as message_parsers:
        import avilla.cai.message_parse as _  # noqa

    with wrap_artifacts() as message_resumers:
        import avilla.cai.message_resume as _  # noqa

    with wrap_artifacts() as context_sources:
        import avilla.cai.impl.context_source as _  # noqa

    service: CAIService

    def __init__(self, *config: CAIConfig):
        self.configs: list[CAIConfig] = list(set(config))
        super().__init__()

    def ensure(self, avilla: Avilla):
        self.avilla = avilla
        self.service = CAIService(self)
        avilla.launch_manager.add_service(MemcacheService(1))
        avilla.launch_manager.add_service(self.service)
        for config in self.configs:
            client = CAIClient(self, config)
            self.service.clients.append(client)
            avilla.launch_manager.add_launchable(client)

    async def serialize_message(
        self,
        message: __message_chain_class__,
        context: Context,
        reply: Selector | None = None,
    ) -> list[CAIElement]:
        result: list[CAIElement] = []
        if reply:
            memcache = context.avilla.launch_manager.get_interface(Memcache)
            origin: Message | None = memcache.get(f"_cai_context.message.{reply.pattern['message']}")
            assert origin is not None
            result.append(
                ReplyElement(
                    seq=int(origin.id),
                    time=int(origin.time.timestamp()),
                    sender=int(origin.sender.last_value),
                    message=await self.serialize_message(origin.content, context, origin.reply),
                )
            )
        for element in message.content:
            resumer: ElementResumer | None = self.message_resumers.get(
                ElementResume(element.__class__)
            )
            if resumer is None:
                raise NotImplementedError(
                    f'expected element "{element.__class__}" implemented for {element}'
                )
            result.append(await resumer(context, element))
        return result

    async def deserialize_message(self, context: Context, message: list[CAIElement]):
        serialized: list[Element] = []
        result: MessageDeserializeResult = {"content": serialized, "reply": None}
        for raw_element in message:
            if not hasattr(raw_element, "type"):
                raise KeyError(f'expected "type" exists for {raw_element}')
            element_type = raw_element.type
            if isinstance(raw_element, ReplyElement):
                result["reply"] = str(raw_element.seq)
                continue
            parser: ElementParser | None = self.message_parsers.get(
                ElementParse(element_type)
            )
            if parser is None:
                raise NotImplementedError(
                    f'expected element "{element_type}" implemented for {raw_element}'
                )
            serialized.append(await parser(context, raw_element))
        return result

    async def parse_event(
        self, account: CAIAccount, event: CAIEvent, *, error: bool = False
    ):
        if not hasattr(event, "type"):
            raise KeyError(f'expected "type" exists for {event}')
        event_type = event.type
        parser: EventParser | None = self.event_parsers.get(EventParse(event_type))
        if parser is None:
            if error:
                raise NotImplementedError(
                    f'expected event "{event_type}" implemented for {event}'
                )
            logger.warning(
                f"Event type {event_type} is not supported by {self.__class__.__name__}",
                event,
            )
            return
        return await parser(self, account, event)
