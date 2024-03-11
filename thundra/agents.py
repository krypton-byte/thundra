from langchain.tools import tool, StructuredTool
from langchain.agents import initialize_agent
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message
from neonize.proto.def_pb2 import (
    ImageMessage,
    Conversation,
    ExtendedTextMessage,
    VideoMessage,
    StickerMessage,
)
from neonize.utils.enum import MediaType
from typing import Callable, Any, Literal, Type, Generator, Sequence, Optional
from dataclasses import dataclass

from .core.graph import Graph
from .types import MessageType, TextMessageType, MediaMessageType
from io import BytesIO
from .utils import get_message_type, get_user_id, MediaTypeToMMS, log, download_media
from .storage.file import storage
from .core.memory import memory
from .core.llm import llm
import json


@dataclass
class Agent:
    message_types: Sequence[Type[MessageType]]
    agent: Callable[[NewClient, Message], Any]


class AgentRegister(list[Agent], Graph):
    def get_all_names(self) -> Generator[str, None, None]:
        for agent in self:
            yield agent.agent.__qualname__

    def filter_tools(
        self, message_type: Type[MessageType]
    ) -> Generator[Agent, None, None]:
        for tool in self:
            if message_type in tool.message_types or not tool.message_types:
                yield tool
        yield from []

    def tool(self, *message_types: Type[MessageType]):
        def tool_agent(f: Callable[[NewClient, Message], Callable[[str], str]]):
            log.debug(f"{f.__name__} agent loaded")
            self.append(Agent(message_types=message_types, agent=f))

        return tool_agent


agent = AgentRegister()


@agent.tool(str, ExtendedTextMessage, ImageMessage, VideoMessage)
def sticker(client: NewClient, message: Message):
    @tool("stickerMaker", return_direct=True)
    def sticker(file_id: str):
        'usefull to create sticker from Image, query input must be file_id from last of message or "" if not have'
        buf_file = None
        try:
            buf_file = download_media(
                client, message.Message, (ImageMessage, VideoMessage, StickerMessage)
            )
        except Exception as e:
            user_id = get_user_id(message)
            if file_id:
                buf_file = storage.get_file(user_id, file_id).download(
                    client, MediaType.MediaImage
                )
            else:
                for file in storage.get_files_by_type(
                    user_id, (ImageMessage, VideoMessage, StickerMessage)
                ):
                    if file:
                        buf_file = file.download(
                            client,
                            (
                                MediaType.MediaImage
                                if file.type in [ImageMessage, StickerMessage]
                                else MediaType.MediaVideo
                            ),
                        )
        if not buf_file:
            return "anda belum mengirimkan gambar/video"
        if buf_file:
            client.send_sticker(message.Info.MessageSource.Chat, buf_file)
            return "Sticker Berhasil Di Upload"
        else:
            return "File Tidak ditemukan"

    return sticker


# @agent.tool()
# def remove_context(client: NewClient, message: Message):
#     @tool("nevermind")
#     def execute(query: str):
#         'usefull for change topik, query input must be new topik or "" if not have'
#         user_id = get_user_id(message)
#         memory.clear_history(user_id)
#         tools = [
#             tool.agent(client, message)
#             for tool in agent.filter_tools(get_message_type(message.Message).__class__)
#         ]
#         if query:
#             return LLMChain(
#                 llm=llm,
#                 prompt=PromptTemplate(
#                     template="jelaskan {question} ?", input_variables=["question"]
#                 ),
#             ).invoke(query)["text"]
#         return "oke mau bahas apa?"

#     return execute
