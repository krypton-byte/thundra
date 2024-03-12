from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message

from typing import Callable, Any, Type, Generator, Sequence
from dataclasses import dataclass

from .core.graph import Graph
from .types import MessageType
from .utils import log


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
