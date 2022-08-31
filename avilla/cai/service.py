from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Set, Literal
from cai import Client
from cai.client import Event
from launart import Launart, Service
from loguru import logger

from avilla.cai.utils import wait_fut, login_resolver

if TYPE_CHECKING:
    from .protocol import CAIProtocol


class CAIService(Service):
    id = "cai.service"
    supported_interface_types = set()

    protocol: CAIProtocol
    client: Client

    def __init__(self, protocol: CAIProtocol, client: Client):
        self.protocol = protocol
        self.client = client
        self.client.add_event_listener(self._cai_event_hook)
        super().__init__()

    async def _cai_event_hook(self, _: Client, event: Event):
        event = await self.protocol.event_parser.parse_event(
            self.protocol, self.protocol.build_account(), event
        )
        if event:
            self.protocol.post_event(event)

    def get_interface(self, interface_type):
        return None

    @property
    def required(self) -> Set[str]:
        return set()

    @property
    def stages(self) -> Set[Literal["preparing", "blocking", "cleanup"]]:
        return {"preparing", "blocking", "cleanup"}

    async def launch(self, manager: Launart):
        async with self.stage("preparing"):
            try:
                await self.client.login()
            except Exception as e:
                await login_resolver(self.client, e)
            self.protocol.avilla.add_account(self.protocol.build_account())
            print(self.protocol.get_account())
            logger.opt(colors=True).success(
                f"<green>Registered account:</> <magenta>{self.protocol._account}</>",
                alt=f"[green]Registered account:[/] [magenta]{self.protocol._account}[/]",
            )
        async with self.stage("blocking"):
            exit_signal = asyncio.create_task(manager.status.wait_for_sigexit())
            while not exit_signal.done():
                await wait_fut(
                    [asyncio.sleep(0.5), exit_signal],
                    return_when=asyncio.FIRST_COMPLETED,
                )
        async with self.stage("cleanup"):
            await self.client.close()
