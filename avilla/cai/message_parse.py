from __future__ import annotations

from typing import TYPE_CHECKING

from cai.client.message_service.models import (
    AtElement,
    TextElement,
    ImageElement,
    FlashImageElement,
    VoiceElement,
    VideoElement,
    ShakeElement,
    CustomDataElement,
    FaceElement,
)
from graia.amnesia.message.element import Text

from avilla.core.elements import Audio, Notice, NoticeAll, Picture, Video
from avilla.core.trait.context import element

from .element import Flash, Shake, Custom, Face, Emoji
from .resource import CAIAudioResource, CAIImageResource, CAIVideoResource

if TYPE_CHECKING:
    from avilla.core.context import Context


@element("text")
async def plain(context: Context, raw: TextElement):
    return Text(raw.content)


@element("at")
async def at(context: Context, raw: AtElement):
    if not context.scene.follows("group"):
        raise ValueError(
            f"At(Notice) element expected used in group scene, which currently {context.scene}"
        )
    return Notice(context.scene.member(str(raw.target)).display(raw.display or ""))


@element("at_all")
async def at_all(context: Context, _):
    return NoticeAll()


@element("face")
async def at_all(context: Context, raw: FaceElement):
    return Face(raw.id)


@element("image")
async def image(context: Context, raw: ImageElement):
    res = CAIImageResource(raw.filename, raw.url)
    return Emoji(res) if raw.is_emoji else Picture(res)


@element("flash_image")
async def flash_image(context: Context, raw: FlashImageElement):
    return Flash(CAIImageResource(raw.filename, raw.url))


@element("voice")
async def voice(context: Context, raw: VoiceElement):
    return Audio(CAIAudioResource(raw.file_name, raw.url, length=raw.size))


@element("video")
async def video(context: Context, raw: VideoElement):
    return Video(
        CAIVideoResource(
            raw.file_name,
            raw.file_md5,
            raw.file_size,
            raw.file_time,
            raw.thumb_size,
            raw.thumb_md5,
        )
    )


@element("shake")
async def shake(context: Context, raw: ShakeElement):
    return Shake(raw.stype, context.scene.contact(str(raw.uin)))


@element("custom_daata")
async def custom(context: Context, raw: CustomDataElement):
    return Custom(raw.data)
