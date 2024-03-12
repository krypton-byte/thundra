from logging import exception
import sys
import magic
from typing import Iterable, Literal, Optional, Self, Tuple, Type, TypeVar
from enum import Enum
from neonize import NewClient
from neonize.proto.def_pb2 import Conversation, ImageMessage, Message as MessageProto
from neonize.proto.Neonize_pb2 import Message
from neonize.proto.def_pb2 import (
    ExtendedTextMessage,
    VideoMessage,
)
from .types import MessageType, MediaMessageType, TextMessageType
from dataclasses import dataclass
from pathlib import Path
from logging import getLogger
import logging
import math
import os


log = getLogger("Thundra")
cwd = os.getcwd().split("/")
base_workdir = Path(__file__).parent


@dataclass
class Workdir:
    db: Path
    workspace_dir: Optional[Path] = None

    @property
    def workspace(self) -> Path:
        return self.workspace_dir or self.db_workspace

    @property
    def db_workspace(self):
        return self.db


workdir = Workdir(db=Path(""))

for i in range(len(cwd) - 1):
    if i == 0:
        dir_path = os.getcwd()
    else:
        dir_path = "/".join(cwd[:-i])
    if "thundra.toml" in os.listdir(dir_path):
        workdir = Workdir(db=Path(dir_path), workspace_dir=Path(dir_path))
        break

# if not vars().get('workdir'):
#     print("📛 Workdir Undefined")
#     sys.exit(1)


@dataclass
class ChainMessage:
    message: MessageProto
    neonize_message: Optional[Message] = None

    def to_json(self):
        type = get_message_type(self.message)
        text = self.text
        data = {
            "message": {
                "type": "text"
                if isinstance(type, (ExtendedTextMessage, str))
                else type.__name__,
                **(
                    {"caption": text}
                    if isinstance(type, MediaMessageType.__args__)
                    else {"text": text}
                    if text
                    else {}
                ),
            }
        }
        if isinstance(type, MediaMessageType.__args__) and self.neonize_message:
            data["message"]["file_id"] = self.neonize_message.Info.ID
        try:
            if isinstance(type, str):
                return data
            attr = type.__name__[0].lower() + type.__name__[1:]
            quoted = getattr(self.message, attr).contextInfo.quotedMessage
            if isinstance(quoted, MessageProto) and quoted.ListFields():
                data["message"].update(
                    {"quoted": self.__class__(message=quoted).to_json()}
                )
        except Exception as e:
            print("error", e)
        return data

    @property
    def type(self):
        for field_name, _ in self.message.ListFields():
            if field_name.name.endswith("Message"):
                return field_name.name
            elif field_name.name == "Conversation":
                return field_name.name
        return "text"

    @property
    def text(self):
        return self.extract_text(self.message)

    @classmethod
    def extract_text(cls, message: MessageProto):
        if message.imageMessage.ListFields():
            imageMessage: ImageMessage = message.imageMessage
            return imageMessage.caption
        elif message.extendedTextMessage.ListFields():
            extendedTextMessage: ExtendedTextMessage = message.extendedTextMessage
            return extendedTextMessage.text
        elif message.videoMessage.ListFields():
            videoMessage: VideoMessage = message.videoMessage
            return videoMessage.caption
        elif message.conversation:
            return message.conversation
        return ""


def get_tag(message: MessageProto):
    for _, value in message.ListFields():
        try:
            return value.contextInfo.mentionedJid
        except Exception:
            pass
    return []


def get_message_type(message: MessageProto) -> MessageType:
    for field_name, v in message.ListFields():
        if field_name.name.endswith("Message"):
            return v
        elif field_name.name == "conversation":
            return v
    raise IndexError()


def get_user_id(message: Message):
    source = message.Info.MessageSource
    return f"{source.Chat.User}{source.Sender.User}"


class MediaTypeToMMS(Enum):
    MediaImage = "image"
    MediaAudio = "audio"
    MediaVideo = "video"
    MediaDocument = "document"
    MediaHistory = "md-msg-hist"
    MediaAppState = "md-app-state"
    MediaLinkThumbnail = "thumbnail-link"

    # @classmethod
    # def from_message(cls, message: MessageProto):
    #     return {
    #         ImageMessage: cls.MediaImage,
    #         AudioMessage: cls.MediaAudio,
    #         VideoMessage: cls.MediaVideo,
    #         DocumentMessage: cls.MediaDocument,
    #     }[get_message_type(message)]
    # @classmethod
    # def from_mime(cls, mime: str):
    #     return {
    #         "audio": cls.MediaAudio,
    #         "video": cls.MediaVideo,
    #         "image": cls.MediaImage,
    #     }.get(magic.from_buffer())


def download_media(
    client: NewClient,
    message: MessageProto,
    types: Iterable[Type[MessageType]] | Type[MessageType],
) -> bytes:
    media_message = get_message_type(message)
    if isinstance(types, type):
        types_tuple = (types,)
    else:
        types_tuple = tuple(types)
    if isinstance(media_message, types_tuple):
        return client.download_any(message)
    else:
        quoted = get_message_type(media_message.contextInfo.quotedMessage)
        if isinstance(quoted, types_tuple):
            return client.download_any(media_message.contextInfo.quotedMessage)


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])
