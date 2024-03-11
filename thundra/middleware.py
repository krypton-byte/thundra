from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message
from .utils import log
from typing import Generator, Type, Optional
from .core.graph import Graph
from abc import ABC, abstractmethod


class Middleware(ABC):
    stop: bool = True
    name: Optional[str] = None

    def __init__(self):
        if not self.name:
            self.name = self.__class__.__name__

    @abstractmethod
    def run(
        self, client: NewClient, message: Message
    ) -> (
        None | bool
    ):  # None -> continue, False -> global command will run after Middleware, True -> global command never execute
        ...


class MiddlewareRegister(list[Middleware], Graph):
    def add(self, middleware: Middleware | Type[Middleware]):
        if isinstance(middleware, type):
            self.append(middleware())
        else:
            self.append(middleware)
        log.debug(f"{middleware.name} middleware loaded")

    def get_all_names(self) -> Generator[str, None, None]:
        for middleware in self:
            yield middleware.name.__str__()

    def execute(self, client: NewClient, message: Message) -> None | Middleware:
        for middleware in self:
            status = middleware.run(client, message)
            if status and middleware.stop:
                return middleware


middleware = MiddlewareRegister()
