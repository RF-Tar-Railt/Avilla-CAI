from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Awaitable, Callable

from avilla.core.trait.context import get_artifacts
from avilla.core.trait.signature import ArtifactSignature
from cai.client.message_service.models import Element as CAIElement
from graia.amnesia.message.element import Element
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from avilla.core.context import Context


@dataclass(eq=True, frozen=True)
class ElementResume(ArtifactSignature):
    element_type: type


ElementResumer: TypeAlias = "Callable[[Context, Element], Awaitable[CAIElement]]"


def resume(element_type: type):
    def wrapper(handler: ElementResumer):
        artifacts = get_artifacts()
        artifacts[ElementResume(element_type)] = handler
        return handler

    return wrapper
