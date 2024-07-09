from __future__ import annotations
from abc import ABC, ABCMeta, abstractclassmethod, abstractmethod
import json
from typing import ClassVar, Dict, Generic, List, NewType, Self, Type, TypeVar
from neonize import NewClient
from neonize.proto.Neonize_pb2 import Message
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import InteractiveMessage
from pydantic import BaseModel, Field
from .types import _ParamsButtonEvent
import time

quick_reply: Dict[str, Type[QuickReplyV2]] = {}
list_button: Dict[str, Type[SectionV2]] = {}


class EmptyParams(BaseModel):
    pass


class EventType:
    def get_quickreply_models(self):
        pass


class QuickReplyV2(ABC, BaseModel, Generic[_ParamsButtonEvent], EventType):
    event_id: ClassVar[str]
    display_text: str = Field()
    params: _ParamsButtonEvent = Field(default=EmptyParams())

    @abstractmethod
    def on_click(
        self, client: NewClient, message: Message, params: _ParamsButtonEvent
    ) -> None: ...

    def __init_subclass__(cls) -> None:
        if cls.__module__ != __class__.__module__:
            quick_reply.update({cls.event_id: cls})

    def create(self):
        return InteractiveMessage.NativeFlowMessage.NativeFlowButton(
            name="quick_reply",
            buttonParamsJSON=json.dumps(
                {
                    "display_text": self.display_text,
                    "params": self.params.model_dump(),
                    "id": f"quickreplyv2_{self.event_id}",
                }
            ),
        )


class RowV2(BaseModel, Generic[_ParamsButtonEvent]):
    id: str = Field(default="")
    header: str = Field()
    title: str = Field()
    description: str = Field()
    params: _ParamsButtonEvent = Field(default=EmptyParams())

    def create(self, event_id: str):
        return {
            "header": self.header,
            "title": self.title,
            "description": self.description,
            "id": f"rowv2_{event_id}_{time.time()}",
            "params": self.params.model_dump(),
        }


class SectionV2(ABC, BaseModel, Generic[_ParamsButtonEvent], EventType):
    event_id: ClassVar[str]
    title: str = Field()
    rows: List[RowV2[_ParamsButtonEvent]] = Field()
    highlight_label: str = Field()

    @abstractmethod
    def on_click(self, client: NewClient, message: Message, param: _ParamsButtonEvent):
        raise NotImplementedError()

    def __init_subclass__(cls) -> None:
        if cls.__module__ != __class__.__module__:
            list_button.update({cls.event_id: cls})

    def create(self):
        return {
            "title": self.title,
            "highlight_label": self.highlight_label,
            "rows": [row.create(self.event_id) for row in self.rows],
        }


# T = TypeVar('T',bound=SectionV2)


class ListButtonV2(BaseModel):
    title: str = Field()
    sections: List[SectionV2] = Field()

    def create(self) -> InteractiveMessage.NativeFlowMessage.NativeFlowButton:
        return InteractiveMessage.NativeFlowMessage.NativeFlowButton(
            name="single_select",
            buttonParamsJSON=json.dumps(
                {
                    "title": self.title,
                    "sections": [section.create() for section in self.sections],
                }
            ),
        )
