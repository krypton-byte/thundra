from __future__ import annotations
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    Generator,
    Sequence,
    Optional,
    TypeVar,
    Type,
    Union,
)
from .core.graph import Graph
from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message
from .utils import ChainMessage, log
from .types import MessageType as IMessageType
from .workdir import workdir, config_toml


class Filter(ABC):
    invert = False
    def __or__(self, __value: Filterable) -> FilterOP:
        return FilterOP(left=self, op=OP.OR, right=__value, invert=self.invert)

    def __and__(self, __value: Filterable) -> FilterOP:
        return FilterOP(left=self, op=OP.AND, right=__value, invert=self.invert)

    def __invert__(self):
        self.invert = not self.invert
        return self

    @abstractmethod
    def filter(self, client: NewClient, message: Message) -> bool: ...

    def _filter(self, client: NewClient, message: Message):
        result = self.filter(client, message)
        if self.invert:
            return not result
        return result

    def __repr__(self):
        return self.__class__.__name__


@dataclass
class FilterOP(Filter):
    left: Filter
    op: OP
    right: Filter
    invert: bool

    def filter(self, client: NewClient, message: Message) -> bool:
        left = self.left._filter(client, message)
        if self.invert:
            left = not left
        if self.op == OP.OR and left:
            return True
        return getattr(left, self.op.value)(self.right._filter(client, message))

    def __repr__(self):
        if self.op == OP.AND:
            rep = f"{self.left} ^ {self.right}"
        else:
            rep = f"{self.left} | {self.right}"
        if self.invert:
            rep = f"~({rep})"
        return rep


Filterable = TypeVar("Filterable", Filter, FilterOP)


class OP(Enum):
    OR = "__or__"
    AND = "__and__"


@dataclass
class CommandFunc:
    """
    A class representing a command function with its associated metadata.

    Attributes:
        name (str): The name of the command.
        filter (Filter | FilterOP): The filter to determine when this command should be executed.
        description (str): A description of the command.
        func (Callable[[NewClient, Message]]): The function to execute for this command.
        category (Sequence[str]): Categories this command belongs to.
        allow_broadcast (bool): Whether this command can be used in broadcast messages.
        on_error (Optional[Union[str, Callable[[NewClient, Message, Exception], None]]]): Error handler for the command.
    """
    name: str
    filter: Filter | FilterOP
    description: str
    func: Callable[[NewClient, Message]]
    category: Sequence[str]
    allow_broadcast: bool
    on_error: Optional[Union[str, Callable[[NewClient, Message, Exception], None]]] = None


class GlobalCommand(dict[str, CommandFunc], Graph):
    """
    A class representing a global command registry that integrates with a graph.
    Commands are stored in a dictionary with their names as keys, and can be executed
    based on incoming messages.

    Attributes:
        start_point (int): The starting point for generating command names.

    """
    start_point: int = 1

    def get_all_names(self) -> Generator[str, None, None]:
        """
        Generate the names of all commands in the registry.

        :yield: The name of each command.
        :rtype: Generator[str, None, None]
        """
        for command in self.values():
            yield command.name

    @classmethod
    def generate_name(cls, start_point: int) -> str:
        """
        Generate a unique name based on the start point.

        :param start_point: The starting point for generating the name.
        :type start_point: int
        :return: The generated unique name.
        :rtype: str
        """
        point = start_point
        uid = ""
        while point > 0:
            r = point % 26
            uid += chr(97 + r)
            point = point // 26
        return uid[::-1]

    def add(self, command: CommandFunc):
        """
        Add a command to the registry.

        :param command: The command function to be added.
        :type command: CommandFunc
        """
        self.update({self.generate_name(self.start_point): command})
        self.start_point += 1

    def execute(self, client: NewClient, message: Message) -> bool:
        """
        Execute the appropriate command based on the given message.

        :param client: The client instance to use for executing the command.
        :type client: NewClient
        :param message: The message to process and execute the command.
        :type message: Message
        :raises e: If an error occurs during command execution and no error handler is provided.
        :return: True if a command is executed successfully, otherwise False.
        :rtype: bool
        """
        for v in self.values():
            if (
                v.allow_broadcast
                or not message.Info.MessageSource.Chat.User == "broadcast"
            ):
                if v.filter.filter(client, message):
                    try:
                        v.func(client, message)
                    except Exception as e:
                        if isinstance(v.on_error, str):
                            client.reply_message(message.Message, message)
                        elif v.on_error and callable(v.on_error):
                            v.on_error(client, message, e)
                        else:
                            raise e
                    return True
        return False

    def register(
        self,
        filter: Filterable,
        name: str = "",
        description: str = "",
        category: Sequence[str] = ["all"],
        allow_broadcast: bool = False,
        on_error: Optional[Union[str, Callable[[NewClient, Message, Exception], None]]] = None,
    ) -> Callable[[Callable[[NewClient, Message], Any]], Callable[[NewClient, Message], Any]]:
        """
        Register a new command with the provided parameters.

        :param filter: The filter to apply to messages for this command.
        :type filter: Filterable
        :param name: The name of the command, defaults to the function name if not provided.
        :type name: str, optional
        :param description: A description of the command, defaults to an empty string.
        :type description: str, optional
        :param category: The categories this command belongs to, defaults to ["all"].
        :type category: Sequence[str], optional
        :param allow_broadcast: Whether this command can be used in broadcast messages, defaults to False.
        :type allow_broadcast: bool, optional
        :param on_error: An error handler for this command, defaults to None.
        :type on_error: Optional[Union[str, Callable[[NewClient, Message, Exception], None]]], optional
        :return: A decorator that registers the command.
        :rtype: Callable[[Callable[[NewClient, Message], Any]], Callable[[NewClient, Message], Any]]
        """
        def command(f: Callable[[NewClient, Message], Any]) -> Callable[[NewClient, Message], Any]:
            log.debug(f"{name} command loaded")
            self.add(
                CommandFunc(
                    name=name or f.__name__,
                    filter=filter,
                    description=description,
                    func=f,
                    category=category,
                    allow_broadcast=allow_broadcast,
                    on_error=on_error,
                )
            )
            return f

        return command



command = GlobalCommand()


class Command(Filter):
    def __init__(
        self,
        command: str,
        prefix: Optional[str] = None,
        space_detection: bool = False
    ) -> None:
        """
        Initializes a Command instance.

        :param command: The command that this instance will represent.
        :type command: str
        :param prefix: An optional prefix for the command, defaults to None. If no prefix is provided, the prefix from the global config will be used.
        :type prefix: Optional[str], optional
        :param space_detection: A flag indicating whether to append a space to the command, defaults to False.
        :type space_detection: bool, optional
        """
        self.command = command + (" " if space_detection else "")
        self.alt_prefix = prefix
        super().__init__()

    def filter(self, client: NewClient, message: Message) -> bool:
        """
        Checks whether the provided message starts with the command this instance represents.

        :param client: The client that received the message.
        :type client: NewClient
        :param message: The message to check.
        :type message: Message
        :return: True if the message starts with the command, False otherwise.
        :rtype: bool
        """
        text = ChainMessage.extract_text(message.Message)
        matched = re.match(workdir.get_config().prefix if self.alt_prefix is None else self.alt_prefix, text)
        if matched:
            _, end = matched.span(0)
            return text[end:].startswith(self.command)
        return False

    def __repr__(self):
        return (
            f"<prefix>{self.command}"
        )


class MessageType(Filter):
    def __init__(self, *types: Type[IMessageType]) -> None:
        """Initialize MessageType filter with specified message types.

        :param types: Types of messages to be filtered.
        :type types: Type[IMessageType]
        """
        self.types = types

    def filter(self, client: NewClient, message: Message) -> bool:
        """Filter messages based on their types.

        :param client: The client object.
        :type client: NewClient
        :param message: The message object.
        :type message: Message
        :return: True if the message type matches any of the specified types, False otherwise.
        :rtype: bool
        """
        for _, v in message.Message.ListFields():
            if v.__class__ in self.types:
                return True
        return False

    def __repr__(self) -> str:
        """Representation of MessageType filter.

        :return: String representation of the filter.
        :rtype: str
        """
        types = " | ".join(map(lambda x: x.__name__, self.types))
        if self.types.__len__() > 1:
            return f"({types})"
        return types


class Owner(Filter):
    def filter(self,client: NewClient, message: Message) -> bool:
        """Filter messages based on whether the sender is the owner.

        :param client: The client object.
        :type client: NewClient
        :param message: The message object.
        :type message: Message
        :return: True if the sender is the owner, False otherwise.
        :rtype: bool
        """
        return message.Info.MessageSource.Sender.User in workdir.get_config().owner
