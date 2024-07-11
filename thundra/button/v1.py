from __future__ import annotations
from datetime import timedelta, datetime
import time
import secrets
from typing import (
    Callable,
    Dict,
    Generic,
    List,
    Optional,
)
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    InteractiveMessage,
)
from pydantic import BaseModel, Field
import json
from .registry import button_registry, ButtonEventData
from .types import _ParamsButtonEvent


class EmptyParams(BaseModel):
    pass


class QuickReply(BaseModel, Generic[_ParamsButtonEvent]):
    display_text: str = Field()
    params: _ParamsButtonEvent = Field(default=EmptyParams())
    on_click: Callable[[_ParamsButtonEvent], None] | Callable[[], None]
    expiration: datetime = Field(
        default_factory=lambda: datetime.now() + timedelta(hours=1)
    )
    id: str = Field(default_factory=lambda: f"quickreplyv1_{time.time()}")

    def create(self) -> InteractiveMessage.NativeFlowMessage.NativeFlowButton:
        button_registry.add(
            ButtonEventData[_ParamsButtonEvent](
                expiration=self.expiration,
                id=self.id,
                on_click=self.on_click,
                params_type=self.params.__class__ if self.params else None,
            )
        )
        return InteractiveMessage.NativeFlowMessage.NativeFlowButton(
            name="quick_reply",
            buttonParamsJSON=json.dumps(
                {
                    "display_text": self.display_text,
                    "params": {} if self.params is None else self.params.model_dump(),
                    "id": self.id,
                }
            ),
        )

    def create_event(self):
        if self.on_click:
            return ButtonEventData(
                id=self.id,
                expiration=self.expiration,
                params_type=self.params.__class__ if self.params else None,
                on_click=self.on_click,
            )


class Row(BaseModel, Generic[_ParamsButtonEvent]):
    header: str = Field()
    title: str = Field()
    description: str = Field()
    params: Optional[_ParamsButtonEvent] = Field(default=None)

    def create(
        self,
        id: str,
        idx: int,
        expiration: datetime,
        on_click: Callable[[_ParamsButtonEvent], None],
    ) -> Dict:
        if on_click:
            if idx == 0:
                button_registry.add(
                    ButtonEventData[type(self.params)](  # type: ignore
                        expiration=expiration,
                        id=id,
                        on_click=on_click,
                        params_type=type(self.params),
                    )
                )
        return {
            "header": self.title,
            "title": self.header,
            "description": self.description,
            "id": f"rowv1_{id}_{time.time()}",
            "params": {} if self.params is None else self.params.model_dump(),
        }


class Section(BaseModel, Generic[_ParamsButtonEvent]):
    id: str = Field(default_factory=lambda: secrets.token_hex(10))
    title: str = Field()
    rows: List[Row[_ParamsButtonEvent]] = Field()
    on_selected: Optional[Callable[[_ParamsButtonEvent], None]] = Field(default=None)
    expiration: datetime = Field(default_factory=lambda :datetime.now() + timedelta(hours=1))
    highlight_label: str = Field()

    def create(self) -> Dict:
        return {
            "title": self.title,
            "highlight_label": self.highlight_label,
            "rows": [
                row.create(self.id, idx, self.expiration, self.on_selected)
                for idx, row in enumerate(self.rows)
            ],
        }

    def add_option(self, *args: Row[_ParamsButtonEvent]):
        self.rows.extend(args)


class ListButton(BaseModel):
    title: str = Field()
    sections: List[Section] = Field()

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


class CopyButton(BaseModel):
    display_text: str = Field()
    copy_code: str = Field()

    def create(self) -> InteractiveMessage.NativeFlowMessage.NativeFlowButton:
        return InteractiveMessage.NativeFlowMessage.NativeFlowButton(
            name="cta_copy",
            buttonParamsJSON='{"display_text":%r,"copy_code":%r}'
            % (self.display_text, self.copy_code),
        )
