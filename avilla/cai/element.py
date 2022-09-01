from __future__ import annotations

from avilla.core.utilles.selector import Selector
from avilla.core.elements import Picture, Element


class Custom(Element):
    data: bytes

    def __init__(self, data: bytes):
        self.data = data

    def __str__(self) -> str:
        return "[$Custom]"


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