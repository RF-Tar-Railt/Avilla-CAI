from richuru import install
import asyncio
from creart import create
from graia.amnesia.builtins.aiohttp import AiohttpClientService
from graia.broadcast import Broadcast

from avilla.core.account import AbstractAccount

from avilla.core.application import Avilla
from avilla.core.elements import Picture
from avilla.core.event.message import MessageReceived, MessageRevoked
from avilla.core.message import Message
from avilla.core.relationship import Relationship
from avilla.core.skeleton.message import MessageTrait
from avilla.core.utilles.selector import DynamicSelector, Selector
from avilla.cai.protocol import CAIProtocol
from avilla.cai.config import CAIConfig

protocol = CAIProtocol(CAIConfig("3542928737", "321456987myTR"))
broadcast = create(Broadcast)
avilla = Avilla(broadcast, [protocol], [AiohttpClientService()])
#install()


@broadcast.receiver(MessageReceived)
async def on_message_received(event: MessageReceived, rs: Relationship, account: AbstractAccount):
    if Selector.fragment().as_dyn().group("*").member("3165388245").match(rs.ctx):
        print(1, account)
        print(2, rs.ctx, rs.mainline, rs.self)
        print(3, event, event.message.content)
        print(4, await rs.send_message("Hello, Avilla!"))
        msg = await rs.send_message("this msg will be recalled in 10s.")
        await asyncio.sleep(10)
        await rs.cast(MessageTrait).revoke(msg)
        await rs.send_message([Picture("test.png")])
    elif Selector.fragment().as_dyn().group("*").member("3542928737").match(rs.ctx):
        print(5, account)
        print(6, rs.ctx, rs.mainline, rs.self)
        print(7, event, event.message.content)


@broadcast.receiver(MessageRevoked)
async def on_message_revoked(event: MessageRevoked, rs: Relationship, account: AbstractAccount):
    print(8, account)
    print(9, rs.ctx, rs.mainline, rs.self)
    print(10, event, event.message, event.operator)

avilla.launch_manager.launch_blocking(loop=broadcast.loop)
