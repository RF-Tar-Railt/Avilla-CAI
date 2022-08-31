from __future__ import annotations

from cai import Client

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
