from typing import Iterable, Literal, NewType, overload

from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    DeviceListMetadata,
    FutureProofMessage,
    InteractiveMessage,
    Message,
    MessageContextInfo,
)

from thundra.button.v1 import CopyButton, ListButton, QuickReply

from thundra.button.v2 import ListButtonV2, QuickReplyV2

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


def create_button_message(
    interactive_message: InteractiveMessage,
    buttons: Iterable[Button],
    direct_send: bool = True,
) -> Message | InteractiveMessage:
    if buttons:
        interactive_message.nativeFlowMessage.MergeFrom(
            InteractiveMessage.NativeFlowMessage(
                buttons=[button.create() for button in buttons]
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
