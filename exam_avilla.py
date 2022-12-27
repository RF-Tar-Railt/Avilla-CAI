import asyncio
import os

from creart import create
from launart import Launart
from graia.amnesia.builtins.aiohttp import AiohttpClientService
from graia.broadcast import Broadcast
from arclet.alconna import Alconna, Args, Option, Field, CommandMeta, Arparma

from avilla.core.account import AbstractAccount
from avilla.core.application import Avilla
from avilla.core.elements import Picture, Notice
from avilla.spec.core.message import MessageReceived, MessageRevoked
from avilla.core.context import Context
from avilla.spec.core.message import MessageSend, MessageRevoke
from avilla.core.selector import Selector

from avilla.cai.protocol import CAIProtocol
from avilla.cai.config import CAIConfig
from avilla.cai.element import Custom, Emoji, Shake, Face

launart = Launart()
launart.add_service(AiohttpClientService())
protocol = CAIProtocol(
    CAIConfig(os.getenv("CAI_ACCOUNT", ""), os.getenv("CAI_PASSWORD", ""), "MACOS", config_root=".config")
)
broadcast = create(Broadcast)
avilla = Avilla(broadcast, launart, [protocol])

alc = Alconna(
    "test",
    [Notice],
    Args["content", Notice, Field(completion=lambda: "test completion")],
    meta=CommandMeta("测试命令1"),
)
alc1 = Alconna(
    "test1",
    Option("--say", Args["content", str]),
    Option("--sad"),
    meta=CommandMeta("测试命令2"),
)


@broadcast.receiver(MessageReceived)
async def on_message_received(
    event: MessageReceived, ctx: Context, account: AbstractAccount
):
    if ctx.client.follows("friend(3165388245)") and event.message.content.startswith(
        "hello"
    ):
        print(1, account)
        print(2, ctx.client, ctx.scene, ctx.self)
        print(3, event, event.message.content)
        print(4, await ctx.scene.send_message("Hello, Avilla!"))
    elif ctx.client.follows(
        "group.member(3165388245)"
    ) and event.message.content.startswith("hello"):
        msg = await ctx.scene.send_message("this msg will be recalled in 2s.")
        await asyncio.sleep(2)
        await ctx.scene.send_message([Face(12)])
        await ctx.wrap(MessageRevoke).revoke(msg)
        await ctx.scene.send_message([Picture("test.png")])
        await ctx.scene.send_message("next will be emoji")
        await ctx.scene.send_message([Emoji("test.png")])
        await ctx.scene.send_message([Shake(0, Selector().contact("3165388245"))])


@broadcast.receiver(MessageRevoked)
async def on_message_revoked(
    event: MessageRevoked, ctx: Context, account: AbstractAccount
):
    print("[scene]", ctx.scene)
    print("[operator]", event.operator)
    print("[message]", event.message)
    await ctx.scene.send_message([Custom(b"Hey! I'm a human!")])

#
# @broadcast.receiver(MessageReceived, dispatchers=[Alc(alc1, send_flag='reply')])
# async def test_(rs: Relationship, event: MessageReceived, res: Arpamar):
#     if rs.ctx.follows("group.member(3165388245)"):
#         await rs.send_message(f"{res}")


avilla.launch_manager.launch_blocking(loop=broadcast.loop)
