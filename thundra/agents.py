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
