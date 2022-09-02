from __future__ import annotations

from avilla.core.resource import Resource
from avilla.core.utilles.selector import Selector


class CAIResource(Resource[bytes]):
    url: str | None = None
    mainline: Selector | None = None

    def __init__(
        self,
        id: str,
        url: str | None = None,
        mainline: Selector | None = None,
    ) -> None:
        self.id = id
        self.url = url
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
        mainline: Selector | None = None,
        length: int | None = None,
    ) -> None:
        super().__init__(id, url, mainline)
        self.length = length

    @property
    def type(self) -> str:
        return "audio"


class CAIVideoResource(CAIResource):
    md5: bytes | None = None
    size: int | None = None
    length: int | None = None
    thumb_size: int | None = None
    thumb_md5: bytes | None = None

    def __init__(
            self,
            id: str,
            md5: bytes | None = None,
            size: int | None = None,
            length: int | None = None,
            thumb_size: int | None = None,
            thumb_md5: bytes | None = None,
            mainline: Selector | None = None,
    ) -> None:
        super().__init__(id, mainline=mainline)
        self.md5 = md5
        self.size = size
        self.length = length
        self.thumb_size = thumb_size
        self.thumb_md5 = thumb_md5

    @property
    def type(self) -> str:
        return "video"
