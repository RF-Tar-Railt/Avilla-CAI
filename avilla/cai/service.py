from __future__ import annotations
import asyncio
from functools import partial
from typing import TYPE_CHECKING, Set, Literal, Dict, Tuple
from cai import Client
from cai.client.events import Event
from launart import Launart, Service
from loguru import logger

from avilla.core.utilles.selector import Selector
from avilla.cai.utils import wait_fut, login_resolver
from avilla.cai.config import CAIConfig
from avilla.cai.account import CAIAccount

if TYPE_CHECKING:
    from .protocol import CAIProtocol


class CAIService(Service):
    id = "cai.service"
    supported_interface_types = set()

    protocol: CAIProtocol
    client_map: Dict[Client, CAIConfig]

    def __init__(self, protocol: CAIProtocol):
        self.protocol = protocol
        self.client_map = {}
        super().__init__()

    def had_client(self, account_id: str):
        return any(account_id == str(config.account) for config in self.client_map.values())

    def get_client(self, account_id: str):
        for client, config in self.client_map.items():
            if str(config.account) == account_id:
                return client
        raise ValueError(f"Account {account_id} not found")

    async def _cai_event_hook(self, _: Client, event: Event, account: CAIAccount):
        parsed_event = await self.protocol.event_parser.parse_event(
            self.protocol, account, event
        )
        if parsed_event:
            await self.protocol.record_event(parsed_event)
            self.protocol.post_event(parsed_event)

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
            for client, config in self.client_map.items():
                logger.opt(colors=True).info(
                    f"waiting for <magenta>{config.account}</> login...",
                    alt=f"waiting for [magenta]{config.account}[/] login...",
                )
                try:
                    if config.cache_siginfo and config.cache_path.exists():
                        logger.debug(f"using account {config.account}'s siginfo")
                        await client.token_login(config.cache_path.open("rb").read())
                    else:
                        await client.login()
                except Exception as e:
                    await login_resolver(client, e)
                account = CAIAccount(str(config.account), self.protocol)
                self.protocol.avilla.add_account(account)
                logger.opt(colors=True).success(
                    f"<green>Registered account:</> <magenta>{config.account}</>",
                    alt=f"[green]Registered account:[/] [magenta]{config.account}[/]",
                )
                client.add_event_listener(partial(self._cai_event_hook, account=account))
        async with self.stage("blocking"):
            exit_signal = asyncio.create_task(manager.status.wait_for_sigexit())
            while not exit_signal.done():
                await wait_fut(
                    [asyncio.sleep(0.5), exit_signal],
                    return_when=asyncio.FIRST_COMPLETED,
                )
        async with self.stage("cleanup"):
            for client, config in self.client_map.items():
                await client.close()
                if config.cache_siginfo:
                    data = client.dump_sig()
                    config.cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with config.cache_path.open("wb+") as f:
                        f.write(data)
                    logger.success(f"account {config.account}'s siginfo saved.")

