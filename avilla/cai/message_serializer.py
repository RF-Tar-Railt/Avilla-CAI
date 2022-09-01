from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Type, Callable, Coroutine, Any
from cai.client.message_service.models import (
    Element,
    AtElement,
    AtAllElement,
    TextElement,
    ShakeElement,
    CustomDataElement
)
from graia.amnesia.message.element import Text, Element as GraiaElement

from avilla.core.context import ctx_relationship
from avilla.core.elements import Audio, Notice, NoticeAll, Picture, Video
from avilla.core.exceptions import UnsupportedOperation
from avilla.core.utilles.message_serializer import MessageSerializer, element as elem_rec
from avilla.cai.element import Flash, Custom, Shake

if TYPE_CHECKING:
    from .protocol import CAIProtocol


class CAIMessageSerializer(MessageSerializer["CAIProtocol"]):
    element_serializer: dict[
        Type[GraiaElement],
        Callable[[Any, CAIProtocol, Any], Element | Coroutine[None, None, Element]],
    ] = {}

    @elem_rec(Text)
    def plain(self, protocol: "CAIProtocol", element: Text):
        return TextElement(element.text)

    @elem_rec(Notice)
    def at(self, protocol: "CAIProtocol", element: Notice):
        return AtElement(target=int(element.target['member']))

    @elem_rec(NoticeAll)
    def at_all(self, protocol: "CAIProtocol", element: NoticeAll):
        return AtAllElement()

    @elem_rec(Picture)
    async def image(self, protocol: "CAIProtocol", element: Picture):
        rs = ctx_relationship.get()
        raw = await rs.fetch(element.resource)
        mainline = rs.mainline
        if not (gid := mainline.pattern.get('group')):
            raise UnsupportedOperation("current cai can only send image in group")
        return await rs.account.client.upload_image(int(gid), BytesIO(raw))

    @elem_rec(Flash)
    async def flash_image(self, protocol: "CAIProtocol", element: Flash):
        rs = ctx_relationship.get()
        raw = await rs.fetch(element.resource)
        mainline = rs.mainline
        if not (gid := mainline.pattern.get('group')):
            raise UnsupportedOperation("current cai can only send flash-image in group")
        return (await rs.account.client.upload_image(int(gid), BytesIO(raw))).to_flash()

    @elem_rec(Audio)
    async def voice(self, protocol: "CAIProtocol", element: Audio):
        rs = ctx_relationship.get()
        raw = await rs.fetch(element.resource)
        mainline = rs.mainline
        if not (gid := mainline.pattern.get('group')):
            raise UnsupportedOperation("current cai can only send voice in group")
        return await rs.account.client.upload_voice(int(gid), BytesIO(raw))

    @elem_rec(Video)
    async def voice(self, protocol: "CAIProtocol", element: Video):
        rs = ctx_relationship.get()
        raw = await rs.fetch(element.resource)
        mainline = rs.mainline
        if not (gid := mainline.pattern.get('group')):
            raise UnsupportedOperation("current cai can only send voice in group")
        return await rs.account.client.upload_video(int(gid), BytesIO(raw), BytesIO(raw))

    @elem_rec(Shake)
    def shake(self, protocol: "CAIProtocol", element: Shake):
        return ShakeElement(element.stype, int(element.target.pattern['contact']))

    @elem_rec(Custom)
    def shake(self, protocol: "CAIProtocol", element: Custom):
        return CustomDataElement(element.data)
