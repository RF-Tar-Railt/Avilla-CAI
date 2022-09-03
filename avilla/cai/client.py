from __future__ import annotations

from typing import TYPE_CHECKING
from cai import Client
from cai.client.events import Event
from launart import Launchable, Launart
from contextlib import suppress
from loguru import logger
from avilla.core.event import AvillaEvent
from avilla.core.event.message import MessageReceived
from avilla.core.event.lifecycle import AccountStatusChanged
from avilla.core.cell.cells import Summary

from .config import CAIConfig
from .utils import login_resolver

if TYPE_CHECKING:
    from .account import CAIAccount
    from .protocol import CAIProtocol


class CAIClient(Launchable):
    protocol: CAIProtocol
    config: CAIConfig
    client: Client
    account: CAIAccount

    @property
    def required(self):
        return {"cai.service"}

    @property
    def stages(self):
        return {"preparing", "cleanup"}

    def register(self):
        # NOTE: for hot registration
        # FIXME: require testing

        if self.account not in self.protocol.avilla.accounts:
            self.protocol.avilla.add_account(self.account)
            logger.opt(colors=True).success(
                f"<green>Registered account: </><magenta>{self.config.account}</>",
                alt=f"[green]Registered account: [magenta]{self.config.account}[/]",
            )
            self.client.add_event_listener(self._cai_event_hook)

    def __init__(self, protocol: CAIProtocol, config: CAIConfig) -> None:
        super().__init__()
        from avilla.cai.account import CAIAccount

        self.id = ".".join(
            [
                "cai",
                "client",
                str(config.account)
            ]
        )
        self.protocol = protocol
        self.config = config
        self.client = Client(int(self.config.account), self.config.password, self.config.protocol)
        self.account = CAIAccount(str(self.config.account), self.protocol)

    async def record_event(self, event: AvillaEvent):
        if isinstance(event, MessageReceived):
            rs = await self.account.get_relationship(event.ctx)
            if (
                event.ctx.pattern[event.ctx.latest_key] == self.account.id
                and event.ctx.pattern.get("land") == self.account.land.name
            ):
                name: str = ""
                with suppress(NotImplementedError):
                    name = (await rs.pull(Summary, event.message.mainline)).name
                mainline = event.message.mainline.pattern[event.message.mainline.latest_key]
                logger.info(
                    f"{self.account.land.name}: [send]"
                    f"[{event.message.mainline.latest_key.title()}({f'{name}, ' if name else ''}{mainline})]"
                    f" <- {str(event.message.content)!r}"
                )
            else:
                main_name: str = ""
                with suppress(NotImplementedError):
                    main_name = (await rs.pull(Summary, event.message.mainline)).name
                mainline = event.message.mainline.pattern[event.message.mainline.latest_key]
                ctx_name: str = ""
                with suppress(NotImplementedError):
                    ctx_name = (await rs.pull(Summary, event.message.sender)).name
                ctx = event.ctx.pattern[event.ctx.latest_key]
                out = f"[{event.message.mainline.latest_key.title()}({f'{main_name}, ' if main_name else ''}{mainline})]"
                if ctx != mainline:
                    out += f" {ctx_name or event.ctx.latest_key.title()}({ctx})"

                logger.info(
                    f"{self.account.land.name}: [recv]{out}"
                    f" -> {str(event.message.content)!r}"
                )
        elif not isinstance(event, AccountStatusChanged):
            logger.info(
                f"{self.account.land.name}: {event.__class__.__name__} from "
                f"{'.'.join(f'{k}({v})' for k, v in event.ctx.pattern.items() if k != 'land')}"
            )

    async def _cai_event_hook(self, _: Client, event: Event):
        parsed_event = await self.protocol.event_parser.parse_event(
            self.protocol, self.account, event
        )
        if parsed_event:
            await self.record_event(parsed_event)
            self.protocol.post_event(parsed_event)

    async def launch(self, manager: Launart):
        async with self.stage("preparing"):
            logger.opt(colors=True).info(
                f"waiting for <magenta>{self.config.account}</> login...",
                alt=f"waiting for [magenta]{self.config.account}[/] login...",
            )
            try:
                if self.config.cache_siginfo and self.config.cache_path.exists():
                    logger.debug(f"using account {self.config.account}'s siginfo")
                    await self.client.token_login(self.config.cache_path.open("rb").read())
                else:
                    await self.client.login()
            except Exception as e:
                await login_resolver(self.client, e)
            self.register()
        async with self.stage("cleanup"):
            await self.client.session.close()
            if self.config.cache_siginfo:
                data = self.client.dump_sig()
                self.config.cache_path.parent.mkdir(parents=True, exist_ok=True)
                with self.config.cache_path.open("wb+") as f:
                    f.write(data)
                logger.success(f"account {self.config.account}'s siginfo saved.")
