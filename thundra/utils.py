from sys import prefix
import tomllib
from typing import Any, Dict, Iterable, List, Optional, Type
from enum import Enum
from neonize import NewClient
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import ImageMessage, Message as MessageProto
from neonize.proto.Neonize_pb2 import Message
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    ExtendedTextMessage,
    VideoMessage,
)
from .types import MessageType, MediaMessageType
from dataclasses import dataclass
from pathlib import Path
from logging import getLogger
import tomli_w
import math
import os


log = getLogger("Thundra")
cwd = os.getcwd().split("/")
base_workdir = Path(__file__).parent


def hidder(parent: dict):
    """_summary_

    :param parent: _description_
    :type parent: dict
    :return: _description_
    :rtype: _type_
    """    
    for k, v in parent.items():
        if isinstance(v, dict):
            hidder(v)
        elif isinstance(v, list):
            v.clear()
        else:
            parent[k] = ""
    return parent



@dataclass
class ChainMessage:
    """
    Represents a chain message.

    :param message: The original message.
    :type message: MessageProto
    :param neonize_message: Optional neonize message.
    :type neonize_message: Optional[Message], optional
    """

    message: MessageProto
    neonize_message: Optional[Message] = None

    def to_json(self) -> Dict[str, Dict[str, Any]]:
        """
        Converts the chain message to a JSON representation.

        :return: JSON representation of the chain message.
        :rtype: Dict[str, Dict[str, Any]]
        """
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
    def type(self) -> str:
        """
        Returns the type of the message.

        :return: The type of the message.
        :rtype: str
        """
        for field_name, _ in self.message.ListFields():
            if field_name.name.endswith("Message"):
                return field_name.name
            elif field_name.name == "Conversation":
                return field_name.name
        return "text"

    @property
    def text(self) -> str:
        """
        Extracts the text from the message.

        :return: The extracted text.
        :rtype: str
        """
        return self.extract_text(self.message)

    @classmethod
    def extract_text(cls, message: MessageProto) -> str:
        """
        Extracts text from the message.

        :param message: The message.
        :type message: MessageProto
        :return: The extracted text.
        :rtype: str
        """
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


def get_tag(message: MessageProto) -> List[str]:
    """
    Gets the tag from the message.

    :param message: The message.
    :type message: MessageProto
    :return: The tag from the message.
    :rtype: List[str]
    """
    for _, value in message.ListFields():
        try:
            return value.contextInfo.mentionedJid
        except Exception:
            pass
    return []


def get_message_type(message: MessageProto) -> MessageType:
    """
    Gets the message type.

    :param message: The message.
    :type message: MessageProto
    :raises IndexError: If the message type cannot be determined.
    :return: The message type.
    :rtype: MessageType
    """
    for field_name, v in message.ListFields():
        if field_name.name.endswith("Message"):
            return v
        elif field_name.name == "conversation":
            return v
    raise IndexError()


def get_user_id(message: Message) -> str:
    """
    Gets the user ID from the message.

    :param message: The message.
    :type message: Message
    :return: The user ID from the message.
    :rtype: str
    """
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
) -> bytes | None:
    """
    Downloads media from a message if it matches the specified types.

    :param client: The client used for downloading.
    :type client: NewClient
    :param message: The message containing the media.
    :type message: MessageProto
    :param types: The types of media to download.
    :type types: Iterable[Type[MessageType]] | Type[MessageType]
    :return: The downloaded media, or None if no media of the specified types is found.
    :rtype: bytes | None
    """
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


def convert_size(size_bytes: int) -> str:
    """
    Converts a size in bytes to a human-readable string representation.

    :param size_bytes: The size in bytes to convert.
    :type size_bytes: int
    :return: The human-readable representation of the size.
    :rtype: str
    """    
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

