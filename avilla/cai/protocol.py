from __future__ import annotations

from cai import Client
from loguru import logger
from avilla.core.event import AvillaEvent
from avilla.core.event.message import MessageReceived
from avilla.core.application import Avilla
from avilla.core.platform import Abstract, Land, Platform
from avilla.core.protocol import BaseProtocol
from avilla.core.trait.context import wrap_namespace

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
        import avilla.cai.impl as _
        import avilla.cai.impl.group as _
        import avilla.cai.impl.friend as _

    service: CAIService

    def __init__(self, *config: CAIConfig):
        self.configs = list(set(config))
        super().__init__()

    def ensure(self, avilla: Avilla):
        self.avilla = avilla
        self.service = CAIService(self)
        avilla.launch_manager.add_service(self.service)
        for config in self.configs:
            self.service.client_map[Client(int(config.account), config.password, config.protocol)] = config

    @staticmethod
    def record_event(event: AvillaEvent):
        if isinstance(event, MessageReceived):
            if (
                    event.ctx.pattern[event.ctx.latest_key] == event.account.id and
                    event.ctx.pattern.get('land') == event.account.land.name
            ):
                logger.info(
                    f"[{event.account.land.name}]"
                    f"[SEND] {'.'.join(f'{k}({v})' for k, v in event.message.mainline.pattern.items() if k != 'land')}"
                    f" <- {str(event.message.content)!r}"
                )
            else:
                logger.info(
                    f"[{event.account.land.name}]"
                    f"[RECV] {'.'.join(f'{k}({v})' for k, v in event.ctx.pattern.items() if k != 'land')}"
                    f" -> {str(event.message.content)!r}"
                )
        else:
            logger.info(
                f"[{event.account.land.name}] {event.__class__.__name__} from "
                f"{'.'.join(f'{k}({v})' for k, v in event.ctx.pattern.items() if k != 'land')}"
            )
