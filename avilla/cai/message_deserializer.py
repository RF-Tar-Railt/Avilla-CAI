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
)

from graia.amnesia.message.element import Element as GraiaElement, Text
from graia.broadcast.utilles import run_always_await

from avilla.core.elements import Audio, Notice, NoticeAll, Picture, Unknown
from avilla.core.utilles.message_deserializer import MessageDeserializer, deserializer
from avilla.core.utilles.selector import Selector

from avilla.cai.element import FlashImage
from avilla.cai.resource import CAIAudioResource, CAIImageResource

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

    async def parse_element(self, protocol: CAIProtocol, raw: Element) -> GraiaElement:
        element_type = self.get_element_type(raw)
        _deserializer = self.element_deserializer.get(element_type)
        if _deserializer is None:
            return Unknown(type=element_type, raw_data=raw)
        return await run_always_await(_deserializer, self, protocol, raw)  # type: ignore

    @deserializer("text")
    def plain(self, protocol: "CAIProtocol", raw: TextElement):
        return Text(raw.content)

    @deserializer("at")
    def at(self, protocol: "CAIProtocol", raw: AtElement):
        return Notice(Selector().contact(raw.target))  # 请使用 rs.complete.

    @deserializer("at_all")
    def at_all(self, protocol: "CAIProtocol", raw: AtAllElement):
        return NoticeAll()

    @deserializer("image")
    def image(self, protocol: "CAIProtocol", raw: ImageElement):
        # mainline 后续修饰
        return Picture(CAIImageResource(raw.filename, raw.url))

    @deserializer("flash_image")
    def flash_image(self, protocol: "CAIProtocol", raw: FlashImageElement):
        return FlashImage(CAIImageResource(raw.filename, raw.url))

    @deserializer("voice")
    def voice(self, protocol: "CAIProtocol", raw: VoiceElement):
        return Audio(CAIAudioResource(raw.file_name, raw.url, length=raw.size))

    # TODO: 更多的消息元素支持
