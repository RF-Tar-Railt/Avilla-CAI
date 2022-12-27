from __future__ import annotations

from typing import TYPE_CHECKING

from avilla.core.selector import Selector
from avilla.core.trait.context import bounds, implement
from avilla.spec.core.message import MessageRevoke
from avilla.cai.account import CAIAccount
if TYPE_CHECKING:

    from avilla.core.context import Context
    from avilla.spec.core.message import MessageRevoke


with bounds("friend.message"):
    @implement(MessageRevoke.revoke)
    async def revoke_friend_message(ctx: Context, message: Selector):
        assert isinstance(ctx.account, CAIAccount)
        await ctx.account.client.recall_friend_msg(
            int(message.pattern["friend"]),
            (
                int(message.pattern["message"]),
                int(message.pattern["random"]),
                int(message.pattern["time"]),
            ),
        )
