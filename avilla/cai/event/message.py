from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from cai.client.events.common import (
    GroupMessage,
    NudgeEvent,
    PrivateMessage,
    TempMessage,
)
from cai.client.events.group import GroupNudgeEvent, GroupMessageRecalledEvent
from graia.amnesia.message import __message_chain_class__
from graia.amnesia.builtins.memcache import Memcache
from avilla.core.context import Context
from avilla.core.message import Message
from avilla.core.selector import Selector
from avilla.core.trait.context import EventParserRecorder
from avilla.spec.core.message import MessageReceived, MessageRevoked
from avilla.spec.core.activity import ActivityTrigged

if TYPE_CHECKING:
    from ..account import CAIAccount
    from ..protocol import CAIProtocol

event = EventParserRecorder["CAIProtocol", "CAIAccount"]


@event("group_message")
async def group_message(protocol: CAIProtocol, account: CAIAccount, raw: GroupMessage):
    group = Selector().land(protocol.land.name).group(str(raw.group_id))
    member = group.member(str(raw.from_uin))
    context = Context(
        account=account,
        client=member,
        endpoint=group,
        scene=group,
        selft=group.member(account.id),
    )
    message_result = await protocol.deserialize_message(context, raw.message)
    message = Message(
        describe=Message,
        id=str(raw.seq),  # id=message_result["source"],
        scene=group,
        sender=member,
        content=__message_chain_class__(message_result["content"]),
        time=datetime.fromtimestamp(raw.time),  # time=message_result["time"],
        reply=group.message(str(message_result["reply"]))
        if message_result["reply"]
        else None,
    )
    context._collect_metadatas(message, message)
    memcache = context.avilla.launch_manager.get_interface(Memcache)
    memcache.set(f"_cai_context.message.{message.id}", message, timedelta(seconds=300))
    res = MessageReceived(context, message)
    return res, context


@event("private_message")
async def friend_message(
    protocol: CAIProtocol, account: CAIAccount, raw: PrivateMessage
):
    friend = Selector().land(protocol.land.name).friend(str(raw.from_uin))
    context = Context(
        account=account,
        client=friend,
        endpoint=account.to_selector(),
        scene=friend,
        selft=account.to_selector(),
    )
    message_result = await protocol.deserialize_message(context, raw.message)
    message = Message(
        describe=Message,
        id=str(raw.seq),
        scene=friend,
        sender=friend,
        content=__message_chain_class__(message_result["content"]),
        time=datetime.fromtimestamp(raw.time),  # time=message_result["time"],
        reply=friend.message(str(message_result["reply"]))
        if message_result["reply"]
        else None,
    )
    context._collect_metadatas(message, message)
    memcache = context.avilla.launch_manager.get_interface(Memcache)
    memcache.set(f"_cai_context.message.{message.id}", message, timedelta(seconds=300))
    res = MessageReceived(context, message)
    return res, context


@event("temp_message")
async def temp_message(protocol: CAIProtocol, account: CAIAccount, raw: TempMessage):
    group = Selector().land(protocol.land.name).group(str(raw.group_id))
    member = group.member(str(raw.from_uin))
    context = Context(
        account=account,
        client=member,
        endpoint=member,
        scene=member,
        selft=group.member(account.id),
    )
    message_result = await protocol.deserialize_message(context, raw.message)
    message = Message(
        describe=Message,
        id=str(raw.seq),  # id=message_result["source"],
        scene=member,
        sender=member,
        content=__message_chain_class__(message_result["content"]),
        time=datetime.fromtimestamp(raw.time),  # time=message_result["time"],
        reply=member.message(str(message_result["reply"]))
        if message_result["reply"]
        else None,
    )
    context._collect_metadatas(message, message)
    memcache = context.avilla.launch_manager.get_interface(Memcache)
    memcache.set(f"_cai_context.message.{message.id}", message, timedelta(seconds=300))
    res = MessageReceived(context, message)
    return res, context


@event("NudgeEvent")
async def nudge_event(
    protocol: CAIProtocol, account: CAIAccount, raw: NudgeEvent
):
    nudge_id = Selector().land(protocol.land.name).activity("nudge_trigger")
    nudge_activity = Selector().land(protocol.land.name).nudge(raw.action)
    if raw.group:
        group = Selector().land(protocol.land.name).group(str(raw.group))
        target = group.member(str(raw.target))
        sender = group.member(str(raw.sender))
        context = Context(
            account=account,
            client=sender,
            endpoint=target,
            scene=group,
            selft=group.member(account.id),
        )

        nudge = ActivityTrigged(context, nudge_id, nudge_activity)
        nudge.trigger = sender
        nudge.scene = group
    else:
        friend = Selector().land(protocol.land.name).friend(str(raw.sender))
        context = Context(
            account=account,
            client=friend,
            endpoint=account.to_selector(),
            scene=friend,
            selft=account.to_selector(),
        )
        nudge = ActivityTrigged(context, nudge_id, nudge_activity)
        nudge.trigger = friend
        nudge.scene = friend
    return nudge, context


@event("GroupNudgeEvent")
async def group_nudge_event(
    protocol: CAIProtocol, account: CAIAccount, raw: GroupNudgeEvent
):
    """
    GroupNudgeEvent(
        group_id=931587979,
        template_id=1133,
        template_text='
            <gtip align="center">
            <qq uin="3165388245" col="1" nm="" />
            <img src="http://tianquan.gtimg.cn/nudgeeffect/item/34/client.gif" jp="https://zb.vip.qq.com/v2/pages/nudgeMall?_wv=2&amp;actionId=9&amp;effectId=34" alt="捏了捏"/>
            <qq uin="3542928737" col="1" nm="" tp="0"/>
            <nor txt="的百合铃并被挨了一拳"/>
            </gtip>
        ',
        template_params={
            'nick_str1': '',
            'nick_str2': '',
            'uin_str1': '3165388245',
            'uin_str2': '3542928737',
            'type_str2': '0',
            'suffix_str': '的百合铃并被挨了一拳',
            'action_img_url': 'http://tianquan.gtimg.cn/nudgeeffect/item/34/client.gif',
            'alt_str1': '捏了捏',
            'jp_str1': 'https://zb.vip.qq.com/v2/pages/nudgeMall?_wv=2&amp;actionId=9&amp;effectId=34'
        }
    )

    """
    nudge_id = Selector().land(protocol.land.name).activity("nudge_trigger")
    nudge_activity = (
        Selector()
        .land(protocol.land.name)
        .nudge(str(raw.template_id))
        .action(raw.action_text)
        .suffix(raw.suffix_text)
    )
    group = Selector().land(protocol.land.name).group(str(raw.group_id))
    target = group.member(str(raw.receiver_id))
    sender = group.member(str(raw.sender_id))
    context = Context(
        account=account,
        client=sender,
        endpoint=target,
        scene=group,
        selft=group.member(account.id),
    )
    nudge = ActivityTrigged(context, nudge_id, nudge_activity)
    nudge.trigger = sender
    nudge.scene = group
    return nudge, context


@event("GroupMessageRecalledEvent")
async def group_message_recall(
    protocol: CAIProtocol, account: CAIAccount, raw: GroupMessageRecalledEvent
):
    group = Selector().land(protocol.land.name).group(str(raw.group_id))
    member = group.member(str(raw.operator_id))
    context = Context(
        account=account,
        client=member,
        endpoint=group,
        scene=group,
        selft=group.member(account.id),
    )
    message = group.message(str(raw.msg_seq)).message(str(raw.msg_seq)).time(str(raw.msg_time))
    return MessageRevoked(context, message, member), context
