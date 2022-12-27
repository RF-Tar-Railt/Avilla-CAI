from __future__ import annotations

from typing import TYPE_CHECKING

from graia.amnesia.builtins.aiohttp import AiohttpClientInterface

from avilla.core.trait.context import bounds, fetch, get_artifacts
from avilla.core.trait.signature import CompleteRule
from avilla.cai.resource import CAIImageResource, CAIAudioResource, CAIResource
from loguru import logger


if TYPE_CHECKING:
    from avilla.core.context import Context

with bounds("group"):
    get_artifacts().setdefault(CompleteRule("member"), "group.member")


@fetch(CAIImageResource)
@fetch(CAIAudioResource)
async def fetch_from_url(ctx: Context, res: CAIResource) -> bytes:
    if not res.url:
        raise NotImplementedError
    logger.debug(ctx.avilla.launch_manager._service_bind)
    client = ctx.avilla.launch_manager.get_interface(AiohttpClientInterface)
    # NOTE: wait for amnesia's fix on this.
    return await (await client.request("GET", res.url)).io().read()
