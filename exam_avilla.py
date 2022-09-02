import asyncio
import os

from creart import create
from graia.amnesia.builtins.aiohttp import AiohttpClientService
from graia.broadcast import Broadcast
from arclet.alconna import Alconna, Args, Option, ArgField, CommandMeta

from avilla.core.account import AbstractAccount
from avilla.core.application import Avilla
from avilla.core.elements import Picture, Notice
from avilla.core.event.message import MessageReceived, MessageRevoked
from avilla.core.relationship import Relationship
from avilla.core.skeleton.message import MessageTrait
from avilla.core.utilles.selector import Selector

from avilla.cai.protocol import CAIProtocol
from avilla.cai.config import CAIConfig
from avilla.cai.element import Custom, Emoji, Shake, Face

protocol = CAIProtocol(
    CAIConfig(os.getenv("CAI_ACCOUNT", ""), os.getenv("CAI_PASSWORD", ""))
)
broadcast = create(Broadcast)
avilla = Avilla(broadcast, [protocol], [AiohttpClientService()])
alc = Alconna(
    "test",
    headers=[Notice],
    main_args=Args["content", Notice, ArgField(completion=lambda: "test completion")],
    meta=CommandMeta("测试命令1"),
)
alc1 = Alconna(
    "test1",
    options=[Option("--say", Args["content", str]), Option("--sad")],
    meta=CommandMeta("测试命令2"),
)


@broadcast.receiver(MessageReceived)
async def on_message_received(
    event: MessageReceived, rs: Relationship, account: AbstractAccount
):
    if rs.ctx.follows("friend(3165388245)") and event.message.content.startswith(
        "hello"
    ):
        print(1, account)
        print(2, rs.ctx, rs.mainline, rs.self)
        print(3, event, event.message.content)
        print(4, await rs.send_message("Hello, Avilla!"))
    elif rs.ctx.follows(
        "group.member(3165388245)"
    ) and event.message.content.startswith("hello"):
        msg = await rs.send_message("this msg will be recalled in 2s.")
        await asyncio.sleep(2)
        await rs.send_message([Face(12)])
        await rs.cast(MessageTrait).revoke(msg)
        await rs.send_message([Picture("test.png")])
        await rs.send_message("next will be emoji")
        await rs.send_message([Emoji("test.png")])
        await rs.send_message([Shake(0, Selector().contact("3165388245"))])


@broadcast.receiver(MessageRevoked)
async def on_message_revoked(
    event: MessageRevoked, rs: Relationship, account: AbstractAccount
):
    print("[mainline]", rs.mainline)
    print("[operator]", event.operator)
    print("[message]", event.message)
    await rs.send_message([Custom(b"Hey! I'm a human!")])


@broadcast.receiver(MessageReceived)
async def test_(rs: Relationship, event: MessageReceived):
    if rs.ctx.follows("group.member(3165388245)"):
        if (res := alc.parse(event.message.content)).matched:
            await rs.send_message(f"{res.source.get_help()}")
        elif (res := alc1.parse(event.message.content)).matched:
            await rs.send_message(f"{res.source.get_help()}")


avilla.launch_manager.launch_blocking(loop=broadcast.loop)
