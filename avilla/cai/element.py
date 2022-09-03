from __future__ import annotations

from graia.amnesia.message.element import Element
from avilla.core.utilles.selector import Selector
from avilla.core.elements import Picture


class Custom(Element):
    data: bytes

    def __init__(self, data: bytes):
        self.data = data

    def __str__(self) -> str:
        return f"[$Custom:data={self.data}]"


class Face(Element):
    id: int

    def __init__(self, face_id: int):
        self.id = face_id

    def __str__(self) -> str:
        return f"[$Face:id={self.id}]"


class Emoji(Picture):
    def __str__(self) -> str:
        return "[$Emoji]"


class Flash(Picture):
    def __str__(self) -> str:
        return "[$Flash]"


class Shake(Element):
    stype: int
    target: Selector

    def __init__(self, stype: int, target: Selector):
        self.stype = stype
        self.target = target

    def __str__(self) -> str:
        return f"[$Shake:type={self.stype}]"