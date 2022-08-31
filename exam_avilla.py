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

protocol = CAIProtocol("3542928737", "321456987myTR", "MACOS")
broadcast = create(Broadcast)
avilla = Avilla(broadcast, [protocol], [AiohttpClientService()])
#install()


@broadcast.receiver(MessageReceived)
async def on_message_received(event: MessageReceived, rs: Relationship, account: AbstractAccount):
    print(account)
    if Selector.fragment().as_dyn().group("941310484").member("3165388245").match(rs.ctx):
        await rs.send_message("Hello, Avilla!")


broadcast.loop.run_until_complete(avilla.launch())

