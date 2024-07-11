from typing import Iterable, Literal, overload

from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    DeviceListMetadata,
    FutureProofMessage,
    InteractiveMessage,
    Message,
    MessageContextInfo,
)

from thundra.button.v1 import CopyButton, ListButton, QuickReply, Row, Section
from thundra.button.registry import button_registry
from thundra.button.v2 import ListButtonV2, QuickReplyV2, RowV2, SectionV2

Button = QuickReply | ListButton | CopyButton | QuickReplyV2 | ListButtonV2


@overload
def create_button_message(
    interactive_message: InteractiveMessage,
    buttons: Iterable[Button],
    direct_send: Literal[True],
) -> Message: ...


@overload
def create_button_message(
    interactive_message: InteractiveMessage,
    buttons: Iterable[Button],
) -> Message: ...


@overload
def create_button_message(
    interactive_message: InteractiveMessage,
    buttons: Iterable[Button],
    direct_send: Literal[False],
) -> InteractiveMessage: ...


def create_carousel_message(
    interactive_message: InteractiveMessage, cards: Iterable[InteractiveMessage]
) -> Message:
    carousel = InteractiveMessage(
        carouselMessage=InteractiveMessage.CarouselMessage(cards=cards)
    )
    interactive_message.MergeFrom(carousel)
    return Message(
        viewOnceMessage=FutureProofMessage(
            message=Message(
                messageContextInfo=MessageContextInfo(
                    deviceListMetadata=DeviceListMetadata(),
                    deviceListMetadataVersion=2,
                ),
                interactiveMessage=interactive_message,
            )
        )
    )


def create_button_message(
    interactive_message: InteractiveMessage,
    buttons: Iterable[Button],
    direct_send: bool = True,
) -> Message | InteractiveMessage:
    if buttons:
        interactive_message.nativeFlowMessage.MergeFrom(
            InteractiveMessage.NativeFlowMessage(
                buttons=[button.create() for button in buttons],
                messageVersion=2
            )
        )
    if direct_send:
        return Message(
            viewOnceMessage=FutureProofMessage(
                message=Message(
                    messageContextInfo=MessageContextInfo(
                        deviceListMetadata=DeviceListMetadata(),
                        deviceListMetadataVersion=2,
                    ),
                    interactiveMessage=interactive_message,
                )
            )
        )
    return interactive_message


__all__ = (
    'button_registry',
    'ListButton',
    'QuickReply',
    'CopyButton',
    'Row',
    'Section',
    'ListButtonV2',
    'RowV2',
    'QuickReplyV2',
    'SectionV2',
    'create_button_message',
    'create_carousel_message'
)