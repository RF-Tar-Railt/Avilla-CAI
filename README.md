# Avilla CAI

avilla 的 cai协议适配

## 示例

```python
from creart import create
from graia.amnesia.builtins.aiohttp import AiohttpClientService
from graia.broadcast import Broadcast
from avilla.core.account import AbstractAccount
from avilla.core.application import Avilla
from avilla.core.event.message import MessageReceived
from avilla.core.relationship import Relationship
from avilla.core.utilles.selector import Selector

from avilla.cai.protocol import CAIProtocol

protocol = CAIProtocol("YourAccount", "YourPassword")
broadcast = create(Broadcast)
avilla = Avilla(broadcast, [protocol], [AiohttpClientService()])


@broadcast.receiver(MessageReceived)
async def on_message_received(event: MessageReceived, rs: Relationship, account: AbstractAccount):
    if Selector.fragment().as_dyn().group("*").member("master-account").match(rs.ctx):
        await rs.send_message("Hello, Avilla!")


avilla.launch_manager.launch_blocking(loop=broadcast.loop)
```
