from __future__ import annotations

from avilla.core.application import Avilla
from avilla.core.platform import Abstract, Land, Platform
from avilla.core.protocol import BaseProtocol
from avilla.core.trait.context import wrap_namespace

from avilla.cai.event_parser import CAIEventParser
from avilla.cai.message_deserializer import CAIMessageDeserializer
from avilla.cai.message_serializer import CAIMessageSerializer
from avilla.cai.service import CAIService
from avilla.cai.config import CAIConfig
from avilla.cai.client import CAIClient


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
    event_parser: CAIEventParser = CAIEventParser()
    message_serializer: CAIMessageSerializer = CAIMessageSerializer()
    message_deserializer: CAIMessageDeserializer = CAIMessageDeserializer()

    with wrap_namespace() as impl_namespace:
        import avilla.cai.impl as _  # noqa
        import avilla.cai.impl.group as _  # noqa
        import avilla.cai.impl.friend as _  # noqa

    service: CAIService

    def __init__(self, *config: CAIConfig):
        self.configs: list[CAIConfig] = list(set(config))
        super().__init__()

    def ensure(self, avilla: Avilla):
        self.avilla = avilla
        self.service = CAIService(self)
        avilla.launch_manager.add_service(self.service)
        for config in self.configs:
            client = CAIClient(self, config)
            self.service.clients.append(client)
            avilla.launch_manager.add_launchable(client)
