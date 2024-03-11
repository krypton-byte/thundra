from typing import NewType, TypeVar, Union
from neonize.proto.def_pb2 import (
    ImageMessage,
    Conversation,
    VideoMessage,
    DocumentMessage,
    ExtendedTextMessage,
    AudioMessage,
    StickerMessage,
)
from neonize.proto.def_pb2 import (
    AudioMessage,
    ButtonsMessage,
    ContactsArrayMessage,
    DocumentMessage,
    EventMessage,
    ExtendedTextMessage,
    GroupInviteMessage,
    ImageMessage,
    ListMessage,
    ListResponseMessage,
    LiveLocationMessage,
    Message,
    MessageHistoryBundle,
    PollCreationMessage,
    ProductMessage,
    StickerMessage,
    VideoMessage,
)

MediaMessageType = Union[
    ImageMessage,
    AudioMessage,
    VideoMessage,
    StickerMessage,
    DocumentMessage,
]

TextMessageType = Union[
    ExtendedTextMessage,
    str,
]

MessageType = Union[MediaMessageType, TextMessageType]
MessageWithContextInfoType = (
    ImageMessage
    | ContactsArrayMessage
    | ExtendedTextMessage
    | DocumentMessage
    | AudioMessage
    | VideoMessage
    | LiveLocationMessage
    | StickerMessage
    | GroupInviteMessage
    | GroupInviteMessage
    | ProductMessage
    | ListMessage
    | ListMessage
    | ListResponseMessage
    | ButtonsMessage
    | ButtonsMessage
    | PollCreationMessage
    | MessageHistoryBundle
    | EventMessage
    | ContactsArrayMessage
)
