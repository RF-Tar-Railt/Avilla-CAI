from richuru import install
from creart import create
from graia.amnesia.builtins.aiohttp import AiohttpClientService
from graia.broadcast import Broadcast

from avilla.core.account import AbstractAccount

from avilla.core.application import Avilla
from avilla.core.elements import Picture
from avilla.core.event.message import MessageReceived
from avilla.core.message import Message
from avilla.core.relationship import Relationship
from avilla.core.resource import LocalFileResource
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
        print(2, rs.ctx, rs.mainline, rs.self, rs.cache)
        print(3, event, event.message)
        print(await rs.send_message("Hello, Avilla!"))
    else:
        print(4, account)
        print(5, rs.ctx, rs.mainline, rs.self, rs.cache)
        print(6, event, event.message)

avilla.launch_manager.launch_blocking(loop=broadcast.loop)
