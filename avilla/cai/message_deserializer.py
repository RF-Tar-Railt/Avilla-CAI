from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Any, Coroutine

from cai.client.message_service.models import (
    Element,
    AtElement,
    AtAllElement,
    TextElement,
    ImageElement,
    FlashImageElement,
    VoiceElement,
    VideoElement,
    ShakeElement,
    CustomDataElement
)

from graia.amnesia.message.element import Element as GraiaElement, Text

from avilla.core.elements import Audio, Notice, NoticeAll, Picture, Video
from avilla.core.utilles.message_deserializer import MessageDeserializer, deserializer
from avilla.core.utilles.selector import Selector

from avilla.cai.element import Flash, Shake, Custom
from avilla.cai.resource import CAIAudioResource, CAIImageResource, CAIVideoResource

if TYPE_CHECKING:
    from .protocol import CAIProtocol


class CAIMessageDeserializer(MessageDeserializer["CAIProtocol"]):
    element_deserializer: dict[
        str,
        Callable[[Any, CAIProtocol, Element], Coroutine[None, None, GraiaElement]]
        | Callable[[Any, CAIProtocol, Element], GraiaElement],
    ] = {}
    ignored_types: set[str] = {"reply"}

    def get_element_type(self, raw: Element) -> str:
        return raw.type

    @deserializer("text")
    def plain(self, protocol: "CAIProtocol", raw: TextElement):
        return Text(raw.content)

    @deserializer("at")
    def at(self, protocol: "CAIProtocol", raw: AtElement):
        return Notice(Selector().contact(str(raw.target)).display(raw.display))  # 请使用 rs.complete.

    @deserializer("at_all")
    def at_all(self, protocol: "CAIProtocol", raw: AtAllElement):
        return NoticeAll()

    @deserializer("image")
    def image(self, protocol: "CAIProtocol", raw: ImageElement):
        # mainline 后续修饰
        return Picture(CAIImageResource(raw.filename, raw.url))

    @deserializer("flash_image")
    def flash_image(self, protocol: "CAIProtocol", raw: FlashImageElement):
        return Flash(CAIImageResource(raw.filename, raw.url))

    @deserializer("voice")
    def voice(self, protocol: "CAIProtocol", raw: VoiceElement):
        return Audio(CAIAudioResource(raw.file_name, raw.url, length=raw.size))

    @deserializer("video")
    def video(self, protocol: "CAIProtocol", raw: VideoElement):
        return Video(CAIVideoResource(
            raw.file_name, raw.file_md5, raw.file_size, raw.file_time, raw.thumb_size, raw.thumb_md5
        ))

    @deserializer("shake")
    def shake(self, protocol: "CAIProtocol", raw: ShakeElement):
        return Shake(raw.stype, Selector().contact(str(raw.uin)))

    @deserializer("custom_daata")
    def custom(self, protocol: "CAIProtocol", raw: CustomDataElement):
        return Custom(raw.data)

    # TODO: 更多的消息元素支持
