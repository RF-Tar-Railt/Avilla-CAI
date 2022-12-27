# Avilla CAI

avilla 的 cai协议适配

## 示例

```python
from creart import create
from launart import Launart
from graia.amnesia.builtins.aiohttp import AiohttpClientService
from graia.broadcast import Broadcast

from avilla.core import Avilla, Context, MessageReceived
from avilla.cai.protocol import CAIProtocol
from avilla.cai.config import CAIConfig

broadcast = create(Broadcast)
launart = Launart()
launart.add_service(AiohttpClientService())
avilla = Avilla(broadcast, launart, [CAIProtocol(CAIConfig("YourAccount", "YourPassword"))])


@broadcast.receiver(MessageReceived)
async def on_message_received(ctx: Context, event: MessageReceived):
    if ctx.client.follows("group.member(master-account)"):
        await ctx.scene.send_message("Hello, Avilla!")


launart.launch_blocking(loop=broadcast.loop)
```
