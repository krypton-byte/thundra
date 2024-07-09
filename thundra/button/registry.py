from datetime import datetime
import re
from threading import Thread
from types import NoneType
import json
import time
from typing import (
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
)

from neonize import NewClient
from neonize.proto.Neonize_pb2 import Message
from pydantic import BaseModel, Field
from .types import _ParamsButtonEvent

from .v2 import SectionV2, quick_reply, list_button


class ButtonEventData(BaseModel, Generic[_ParamsButtonEvent]):
    id: str = Field()
    on_click: Callable[[_ParamsButtonEvent], None] = Field()
    expiration: datetime = Field()
    params_type: Optional[Type[_ParamsButtonEvent]] = Field(default=None)


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

    def click(self, client: NewClient, from_message: Message):
        message = from_message.Message
        if message.HasField("interactiveResponseMessage"):
            response = message.interactiveResponseMessage.nativeFlowResponseMessage
            if response and response.name == "menu_options":
                js = json.loads(response.paramsJSON)
                if js["id"].startswith("rowv1"):
                    matched: List[Tuple] = re.findall(
                        r"rowv1_(.*)_([\d\.]+)$", js["id"]
                    )
                    if not matched:
                        return
                    selected: Tuple[str, str] = matched[0]
                    id, _ = selected
                    data = self[id]
                    for button in message.interactiveResponseMessage.contextInfo.quotedMessage.interactiveMessage.nativeFlowMessage.buttons:
                        if button.name == "single_select":
                            if data.params_type in [None, NoneType]:
                                data.on_click()  # type: ignore
                            else:
                                sections = json.loads(button.buttonParamsJSON)[
                                    "sections"
                                ]
                                for section in sections:
                                    for row in section["rows"]:
                                        if row["id"] == js["id"]:
                                            arg = data.params_type.model_validate(
                                                row["params"]
                                            )  # type: ignore
                                            data.on_click(arg)  # type: ignore
                                            return
                elif js["id"].startswith("rowv2"):
                    matched = re.findall(r"rowv2_(.*)_([\d\.]+)$", js["id"])
                    if not matched:
                        return
                    selected: Tuple[str, str] = matched[0]
                    event_id, timestamp = selected
                    section_class = list_button[event_id]
                    sections_data: List[SectionV2] = []
                    for button in message.interactiveResponseMessage.contextInfo.quotedMessage.interactiveMessage.nativeFlowMessage.buttons:
                        if button.name == "single_select":
                            sections = json.loads(button.buttonParamsJSON)["sections"]
                            for i, section in enumerate(sections):
                                try:
                                    sections_data.append(
                                        section_class.model_validate(section)
                                    )
                                    if (
                                        i == 0
                                        and sections_data[0].rows
                                        and not sections_data[0]
                                        .rows[0]
                                        .id.startswith(f"rowv2_{event_id}_")
                                    ):
                                        del sections_data[-1]
                                        break
                                except Exception:
                                    continue
                            for section in sections_data:
                                for row in section.rows:
                                    if row.id == js["id"]:
                                        section.on_click(
                                            client, from_message, row.params
                                        )
        elif message.HasField("templateButtonReplyMessage"):
            if message.templateButtonReplyMessage.selectedID.startswith("quickreplyv2"):
                selected: dict = json.loads(
                    message.templateButtonReplyMessage.contextInfo.quotedMessage.interactiveMessage.nativeFlowMessage.buttons[
                        message.templateButtonReplyMessage.selectedIndex
                    ].buttonParamsJSON
                )
                selected.update(
                    {
                        "display_text": message.templateButtonReplyMessage.selectedDisplayText
                    }
                )
                model = quick_reply[selected["id"].split("_", 1)[1]].model_validate(
                    selected
                )
                model.on_click(client, from_message, model.params)
            elif message.templateButtonReplyMessage.selectedID.startswith(
                "quickreplyv1"
            ):
                selected: dict = json.loads(
                    message.templateButtonReplyMessage.contextInfo.quotedMessage.interactiveMessage.nativeFlowMessage.buttons[
                        message.templateButtonReplyMessage.selectedIndex
                    ].buttonParamsJSON
                )
                button_class = self[selected["id"]]
                if button_class.params_type in [None, NoneType]:
                    button_class.on_click()
                else:
                    params = button_class.params_type.model_validate(selected["params"])
                    button_class.on_click(params)


button_registry = ButtonRegistry()
th = Thread(target=ButtonRegistry)
th.daemon = True
th.start()
