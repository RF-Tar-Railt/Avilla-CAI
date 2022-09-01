from __future__ import annotations

from contextlib import suppress
from cai import Client
from loguru import logger
from avilla.core.event import AvillaEvent
from avilla.core.event.message import MessageReceived
from avilla.core.event.lifecycle import AccountStatusChanged
from avilla.core.application import Avilla
from avilla.core.platform import Abstract, Land, Platform
from avilla.core.protocol import BaseProtocol
from avilla.core.trait.context import wrap_namespace
from avilla.core.cell.cells import Summary

from avilla.cai.event_parser import CAIEventParser
from avilla.cai.message_deserializer import CAIMessageDeserializer
from avilla.cai.message_serializer import CAIMessageSerializer
from avilla.cai.service import CAIService
from avilla.cai.config import CAIConfig


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
    event_parser = CAIEventParser()
    message_serializer = CAIMessageSerializer()
    message_deserializer = CAIMessageDeserializer()
    """
    query_handlers: ClassVar[list[type[ProtocolAbstractQueryHandler]]] = [
        ElizabethGroupQuery,
        ElizabethRootQuery,
    ]
    """

    with wrap_namespace() as impl_namespace:
        import avilla.cai.impl as _  # noqa
        import avilla.cai.impl.group as _  # noqa
        import avilla.cai.impl.friend as _  # noqa

    service: CAIService

    def __init__(self, *config: CAIConfig):
        self.configs = list(set(config))
        super().__init__()

    def ensure(self, avilla: Avilla):
        self.avilla = avilla
        self.service = CAIService(self)
        avilla.launch_manager.add_service(self.service)
        for config in self.configs:
            self.service.client_map[
                Client(int(config.account), config.password, config.protocol)
            ] = config

    @staticmethod
    async def record_event(event: AvillaEvent):
        if isinstance(event, MessageReceived):
            rs = await event.account.get_relationship(event.ctx)
            if (
                event.ctx.pattern[event.ctx.latest_key] == event.account.id
                and event.ctx.pattern.get("land") == event.account.land.name
            ):
                name = ""
                with suppress(NotImplementedError):
                    name = (await rs.pull(Summary, event.message.mainline)).name
                mainline = event.message.mainline.pattern[event.message.mainline.latest_key]
                logger.info(
                    f"{event.account.land.name} >> [send]"
                    f"[{event.message.mainline.latest_key}({f'{name}, ' if name else ''}{mainline})]"
                    f" <- {str(event.message.content)!r}"
                )
            else:
                main_name = ""
                with suppress(NotImplementedError):
                    main_name = (await rs.pull(Summary, event.message.mainline)).name
                mainline = event.message.mainline.pattern[event.message.mainline.latest_key]
                ctx_name = ""
                with suppress(NotImplementedError):
                    ctx_name = (await rs.pull(Summary, event.message.sender)).name
                ctx = event.ctx.pattern[event.ctx.latest_key]
                out = f"[{event.message.mainline.latest_key}({f'{main_name}, ' if main_name else ''}{mainline})]"
                if ctx != mainline:
                    out += f" {ctx_name or event.ctx.latest_key}({ctx})"

                logger.info(
                    f"{event.account.land.name} >> [recv]{out}"
                    f" -> {str(event.message.content)!r}"
                )
        elif not isinstance(event, AccountStatusChanged):
            logger.info(
                f"{event.account.land.name} >> {event.__class__.__name__} from "
                f"{'.'.join(f'{k}({v})' for k, v in event.ctx.pattern.items() if k != 'land')}"
            )
