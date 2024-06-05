from typing import Union
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    ImageMessage,
    VideoMessage,
    DocumentMessage,
    ExtendedTextMessage,
    AudioMessage,
    StickerMessage,
)
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
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
