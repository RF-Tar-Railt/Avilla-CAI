from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Set, Literal, List
from launart import Launart, Service
from avilla.cai.client import CAIClient

if TYPE_CHECKING:
    from .protocol import CAIProtocol


class CAIService(Service):
    id = "cai.service"
    supported_interface_types = set()

    protocol: CAIProtocol
    clients: List[CAIClient]

    def __init__(self, protocol: CAIProtocol):
        self.protocol = protocol
        self.clients = []
        super().__init__()

    def had_client(self, account_id: str):
        return any(
            account_id == str(client.config.account) for client in self.clients
        )

    def get_client(self, account_id: str):
        for client in self.clients:
            if str(client.config.account) == account_id:
                return client
        raise ValueError(f"Account {account_id} not found")

    def get_interface(self, interface_type):
        return None

    @property
    def required(self) -> Set[str]:
        return {"http.client/aiohttp"}

    @property
    def stages(self) -> Set[Literal["preparing", "blocking", "cleanup"]]:
        return {"preparing", "blocking", "cleanup"}

    async def launch(self, manager: Launart):
        async with self.stage("preparing"):
            for client in self.clients:
                client.config.init_dir()

        async with self.stage("blocking"):
            if self.clients:
                await asyncio.wait(
                    [
                        client.status.wait_for(
                            "waiting-for-cleanup",  # type: ignore
                            "cleanup",  # type: ignore
                            "finished",  # type: ignore
                        )
                        for client in self.clients
                    ]
                )

        async with self.stage("cleanup"):
            ...  # TODO
