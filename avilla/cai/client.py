from __future__ import annotations

import traceback
from typing import TYPE_CHECKING
from cai import Client
from cai.client.events import Event
from launart import Launchable, Launart
from contextlib import suppress
from loguru import logger
from avilla.core.event import AvillaEvent
from avilla.spec.core.message import MessageReceived
from avilla.spec.core.application import AccountStatusChanged
from avilla.spec.core.profile import Summary

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

        self.id = f"cai.client.{config.account}"
        self.protocol = protocol
        self.config = config
        self.client = Client(int(self.config.account), self.config.password, self.config.protocol)
        self.account = CAIAccount(str(self.config.account), self.protocol)

    async def record_event(self, event: AvillaEvent):
        if isinstance(event, MessageReceived):
            _mr: MessageReceived = event
            ctx = _mr.context
            sender = _mr.message.sender
            if (
                sender.last_value == self.account.id
                and sender['land'] == self.account.land.name
            ):
                name: str = ""
                with suppress(NotImplementedError):
                    name = (await ctx.pull(Summary, _mr.message.scene)).name
                scene_id = _mr.message.scene.last_value
                logger.info(
                    f"{self.account.land.name}: [send]"
                    f"[{_mr.message.scene.last_key.title()}({f'{name}, ' if name else ''}{scene_id})]"
                    f" <- {str(_mr.message.content)!r}"
                )
            else:
                main_name: str = ""
                with suppress(NotImplementedError):
                    main_name = (await ctx.pull(Summary, _mr.message.scene)).name
                scene_id = _mr.message.scene.last_value
                sender_name: str = ""
                with suppress(NotImplementedError):
                    sender_name = (await ctx.pull(Summary, sender)).name
                sender_id = sender.last_value
                out = f"[{_mr.message.scene.last_key.title()}({f'{main_name}, ' if main_name else ''}{scene_id})]"
                if sender_id != scene_id:
                    out += f" {sender_name or sender.last_key.title()}({sender_id})"

                logger.info(
                    f"{self.account.land.name}: [recv]{out}"
                    f" -> {str(_mr.message.content)!r}"
                )
        elif not isinstance(event, AccountStatusChanged):
            logger.info(
                f"{self.account.land.name}: {event.__class__.__name__} from "
                f"{'.'.join(f'{k}({v})' for k, v in event.context.self.pattern.items() if k != 'land')}"
            )

    async def _cai_event_hook(self, _: Client, event: Event):
        parsed_event, _ctx = await self.protocol.parse_event(
            self.account, event
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
                try:
                    if self.config.cache_siginfo and self.config.cache_path.exists():
                        logger.debug(f"using account {self.config.account}'s siginfo")
                        await self.client.token_login(self.config.cache_path.open("rb").read())
                    else:
                        await self.client.login()
                except Exception as e:
                    await login_resolver(self.client, e)
                self.register()
            except Exception as e:
                logger.warning(e)
                manager.status.exiting = True
                traceback.print_exc()
        async with self.stage("cleanup"):
            if self.client.connected:
                await self.client.session.close()
                if self.config.cache_siginfo:
                    data = self.client.dump_sig()
                    self.config.cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with self.config.cache_path.open("wb+") as f:
                        f.write(data)
                    logger.success(f"account {self.config.account}'s siginfo saved.")
