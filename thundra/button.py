from __future__ import annotations
from datetime import timedelta, datetime
from threading import Thread
import time
from types import NoneType
from typing import (
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    overload,
)
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    DeviceListMetadata,
    FutureProofMessage,
    InteractiveMessage,
    Message,
    MessageContextInfo,
)
from pydantic import BaseModel, Field
import json

_ParamsButtonEvent = TypeVar("_ParamsButtonEvent", bound=BaseModel)


class ButtonEventData(BaseModel, Generic[_ParamsButtonEvent]):
    id: str = Field()
    on_click: Callable[[_ParamsButtonEvent], None] | Callable[[], None] = Field()
    expiration: datetime = Field()
    params_type: Optional[Type[_ParamsButtonEvent]] = Field(default=None)

class QuickReply(BaseModel, Generic[_ParamsButtonEvent]):
    display_text: str = Field()
    params: Optional[_ParamsButtonEvent] = Field(default=None)
    on_click: Optional[Callable[[_ParamsButtonEvent], None] | Callable[[], None]] = (
        Field(default=None)
    )
    expiration: datetime = Field(default=timedelta())
    id: str = Field(default_factory=lambda: f"quickreply_{time.time()}")
    def create(self) -> InteractiveMessage.NativeFlowMessage.NativeFlowButton:
        return InteractiveMessage.NativeFlowMessage.NativeFlowButton(
            name="quick_reply",
            buttonParamsJSON=json.dumps(
                {
                    "display_text": self.display_text,
                    "params": {}
                    if self.params is None
                    else self.params.model_dump(),
                    "id":self.id
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

    def create(self, id: str, idx: int, expiration: datetime, on_click: Callable[[_ParamsButtonEvent], None] | None) -> Dict:
        if on_click:
            if idx == 0:
                button_registry.add(
                    ButtonEventData[type(self.params)]( # type: ignore
                        expiration=expiration,
                        id=id,
                        on_click=on_click, # type: ignore
                        params_type=type(self.params),
                    )
                )
        return {
            "header": self.title,
            "title": self.header,
            "description": self.description,
            "id":id,
            "params": {} if self.params is None else self.params.model_dump(),
        }


class Section(BaseModel, Generic[_ParamsButtonEvent]):
    id: str = Field(default_factory=lambda: f"row_{time.time()}")
    title: str = Field()
    rows: List[Row[_ParamsButtonEvent]] = Field()
    on_selected: Optional[Callable[[_ParamsButtonEvent], None]] = Field(default=None)
    expiration: datetime = Field(default=datetime.now() + timedelta(hours=1))
    highlight_label: str = Field()
    def create(self) -> Dict:
        return {
            "title": self.title,
            "highlight_label": self.highlight_label,
            "rows": [row.create(self.id, idx, self.expiration, self.on_selected) for idx, row in enumerate(self.rows)],
        }

    def add_option(self, *args: Row[_ParamsButtonEvent]):
        self.rows.extend(args)


class ListButton(BaseModel):
    title: str = Field()
    sections: List[Section] = Field()

    def create(self) -> InteractiveMessage.NativeFlowMessage.NativeFlowButton:
        return InteractiveMessage.NativeFlowMessage.NativeFlowButton(
            name="single_select", buttonParamsJSON=json.dumps({"title":self.title,"sections":[section.create() for section in self.sections]})
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


class ButtonContainer:
    def __init__(self) -> None:
        self.buttons = []


@overload
def create_button_message(
    interactive_message: InteractiveMessage,
    buttons: Iterable[QuickReply | ListButton | CopyButton],
    direct_send: Literal[True],
) -> Message: ...


@overload
def create_button_message(
    interactive_message: InteractiveMessage,
    buttons: Iterable[QuickReply | ListButton | CopyButton],
) -> Message: ...


@overload
def create_button_message(
    interactive_message: InteractiveMessage,
    buttons: Iterable[QuickReply | ListButton | CopyButton],
    direct_send: Literal[False],
) -> InteractiveMessage: ...


def create_button_message(
    interactive_message: InteractiveMessage,
    buttons: Iterable[QuickReply | ListButton | CopyButton],
    direct_send: bool = True,
) -> Message | InteractiveMessage:
    interactive_message.nativeFlowMessage.MergeFrom(
        InteractiveMessage.NativeFlowMessage(
            buttons=[button.create() for button in buttons]
        )
    )
    if direct_send:
        return Message(
            viewOnceMessage=FutureProofMessage(
                message=Message(
                    messageContextInfo=MessageContextInfo(
                        deviceListMetadata=DeviceListMetadata(),
                        deviceListMetadataVersion=2,
                    ),
                    interactiveMessage=interactive_message,
                )
            )
        )
    return interactive_message


class ButtonRegistry(Dict[str, ButtonEventData]):
    def __init__(self, worker: int = 5) -> None:
        self.worker = worker
        super().__init__()

    def expire_run(self):
        while True:
            timestamp = time.time()
            for k, v in self.items():
                if v.expiration.timestamp() < timestamp:
                    del self[k]
            time.sleep(1)
    def add(self, button: ButtonEventData):
        self[button.id] = button
    def click(self, message: Message):
        if message.interactiveResponseMessage:
            response = message.interactiveResponseMessage.nativeFlowResponseMessage
            if response and response.name == "menu_options":
                js = json.loads(response.paramsJSON)
                data = self[js['id']]
                for button in message.interactiveResponseMessage.contextInfo.quotedMessage.interactiveMessage.nativeFlowMessage.buttons:
                    if button.name == "single_select":
                        sections = json.loads(button.buttonParamsJSON)['sections']
                        if data.params_type in [None, NoneType]:
                            data.on_click() # type: ignore
                        else:
                            for section in sections:
                                for row in section['rows']:
                                    if row['id'] == js['id']:
                                        arg = data.params_type.model_validate(row['params']) # type: ignore
                                        data.on_click(arg) #type: ignore
        elif message.templateButtonReplyMessage:
            data = self[message.templateButtonReplyMessage.selectedID]
            for button in message.templateButtonReplyMessage.contextInfo.quotedMessage.interactiveMessage.nativeFlowMessage.buttons:
                if button.name == "quick_reply":
                    if data.params_type in [None, NoneType]:
                        data.on_click() # type: ignore
                    else:
                        js = json.loads(button.buttonParamsJSON)
                        if message.templateButtonReplyMessage.selectedID == js['id']:
                            data.on_click(data.params_type.model_validate(js['params'])) # type: ignore



button_registry = ButtonRegistry()
th = Thread(target=ButtonRegistry)
th.daemon = True
th.start()
