from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from avilla.cai.account import CAIAccount
from avilla.cai.element import Custom, Emoji, Face, Flash, Shake
from avilla.cai.trait import resume
from avilla.core.elements import Audio, Notice, NoticeAll, Picture, Video
from avilla.core.exceptions import UnsupportedOperation
from cai.client.message_service.models import (
    AtAllElement,
    AtElement,
    CustomDataElement,
    FaceElement,
    ShakeElement,
    TextElement,
)
from graia.amnesia.message.element import Text

if TYPE_CHECKING:
    from avilla.core.context import Context


@resume(Text)
async def plain(context: Context, element: Text):
    return TextElement(element.text)


@resume(Notice)
async def at(context: Context, element: Notice):
    return AtElement(target=int(element.target.pattern["member"]))


@resume(NoticeAll)
async def at_all(context: Context, element: NoticeAll):
    return AtAllElement()


@resume(Face)
async def face(context: Context, element: Face):
    return FaceElement(element.id)


@resume(Picture)
async def image(context: Context, element: Picture):
    assert isinstance(context.account, CAIAccount)
    raw = await context.fetch(element.resource)
    scene = context.scene
    if not (gid := scene.pattern.get("group")):
        raise UnsupportedOperation("current cai can only send image in group")
    return await context.account.client.upload_image(int(gid), BytesIO(raw))


@resume(Emoji)
async def emoji(context: Context, element: Emoji):
    assert isinstance(context.account, CAIAccount)
    raw = await context.fetch(element.resource)
    scene = context.scene
    if not (gid := scene.pattern.get("group")):
        raise UnsupportedOperation("current cai can only send image in group")
    return await context.account.client.upload_image(int(gid), BytesIO(raw), True)


@resume(Flash)
async def flash_image(context: Context, element: Flash):
    assert isinstance(context.account, CAIAccount)
    raw = await context.fetch(element.resource)
    scene = context.scene
    if not (gid := scene.pattern.get("group")):
        raise UnsupportedOperation("current cai can only send flash-image in group")
    return (
        await context.account.client.upload_image(int(gid), BytesIO(raw))
    ).to_flash()


@resume(Audio)
async def voice(context: Context, element: Audio):
    assert isinstance(context.account, CAIAccount)
    raw = await context.fetch(element.resource)
    scene = context.scene
    if not (gid := scene.pattern.get("group")):
        raise UnsupportedOperation("current cai can only send voice in group")
    return await context.account.client.upload_voice(int(gid), BytesIO(raw))


@resume(Video)
async def video(context: Context, element: Video):
    assert isinstance(context.account, CAIAccount)
    raw = await context.fetch(element.resource)
    scene = context.scene
    if not (gid := scene.pattern.get("group")):
        raise UnsupportedOperation("current cai can only send voice in group")
    return await context.account.client.upload_video(
        int(gid), BytesIO(raw), BytesIO(raw)
    )


@resume(Shake)
async def shake(context: Context, element: Shake):
    return ShakeElement(element.stype, int(element.target.pattern["contact"]))


@resume(Custom)
async def custom(context: Context, element: Custom):
    return CustomDataElement(element.data)
