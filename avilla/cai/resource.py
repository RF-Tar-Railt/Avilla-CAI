from __future__ import annotations

from avilla.core.resource import Resource
from avilla.core.utilles.selector import Selector


class CAIResource(Resource[bytes]):
    url: str | None = None
    path: str | None = None
    mainline: Selector | None = None

    def __init__(
        self,
        id: str,
        url: str | None = None,
        path: str | None = None,
        mainline: Selector | None = None,
    ) -> None:
        self.id = id
        self.url = url
        self.path = path
        self.mainline = mainline

    @property
    def type(self) -> str:
        return "cai_resource"

    @property
    def selector(self) -> Selector:
        return (self.mainline.copy() if self.mainline is not None else Selector()).appendix(self.type, self.id)


class CAIImageResource(CAIResource):
    @property
    def type(self) -> str:
        return "picture"


class CAIAudioResource(CAIResource):
    length: int | None = None

    def __init__(
        self,
        id: str,
        url: str | None = None,
        path: str | None = None,
        mainline: Selector | None = None,
        length: int | None = None,
    ) -> None:
        super().__init__(id, url, path, mainline)
        self.length = length

    @property
    def type(self) -> str:
        return "audio"
