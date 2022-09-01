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

from avilla.cai.protocol import CAIProtocol
from avilla.cai.config import CAIConfig

protocol = CAIProtocol(CAIConfig("YourAccount", "YourPassword"))
broadcast = create(Broadcast)
avilla = Avilla(broadcast, [protocol], [AiohttpClientService()])


@broadcast.receiver(MessageReceived)
async def on_message_received(event: MessageReceived, rs: Relationship, account: AbstractAccount):
    if rs.ctx.follows("group.member(master-account)"):
        await rs.send_message("Hello, Avilla!")


avilla.launch_manager.launch_blocking(loop=broadcast.loop)
```
