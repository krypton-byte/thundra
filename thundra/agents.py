from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message

from typing import Callable, Any, Type, Generator, Sequence
from dataclasses import dataclass

from .core.graph import Graph
from .types import MessageType
from .utils import log


@dataclass
class Agent:
    """
    A class representing an agent with specific message types and a callable agent function.

    Attributes:
        message_types (Sequence[Type[MessageType]]): The message types that the agent can handle.
        agent (Callable[[NewClient, Message], Any]): The function to be executed by the agent.
    """
    message_types: Sequence[Type[MessageType]]
    agent: Callable[[NewClient, Message], Any]


class AgentRegister(list[Agent], Graph):
    """
    A registry for agents, allowing filtering and management of agents.

    Methods:
        get_all_names():
            Generate the names of all agents in the register.
        filter_tools(message_type: Type[MessageType]):
            Generate agents that can handle the given message type.
        tool(*message_types: Type[MessageType]):
            Decorator to register an agent with specific message types.
    """
    def get_all_names(self) -> Generator[str, None, None]:
        """
        Generate the names of all agents in the register.

        :yield: The name of each agent.
        :rtype: Generator[str, None, None]
        """        
        for agent in self:
            yield agent.agent.__qualname__

    def filter_tools(
        self, message_type: Type[MessageType]
    ) -> Generator[Agent, None, None]:
        """
        Generate agents that can handle the given message type.

        :param message_type: The type of message to filter agents by.
        :type message_type: Type[MessageType]
        :yield: Agents that can handle the given message type.
        :rtype: Generator[Agent, None, None]
        """    
        for tool in self:
            if message_type in tool.message_types or not tool.message_types:
                yield tool

    def tool(self, *message_types: Type[MessageType]) -> Callable[[Callable[[NewClient, Message], Callable[[str], str]]], None]:
        """
        Decorator to register an agent with specific message types.

        :param message_types: The message types the agent can handle.
        :type message_types: Type[MessageType]
        :return: A decorator to register the agent function.
        :rtype: Callable[[Callable[[NewClient, Message], Callable[[str], str]]], None]
        """        
        def tool_agent(f: Callable[[NewClient, Message], Callable[[str], str]]) -> None:
            log.debug(f"{f.__name__} agent loaded")
            self.append(Agent(message_types=message_types, agent=f))

        return tool_agent


agent = AgentRegister()
