from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI
import os
from ..config import config_toml
from thundra.config import config_toml
from threading import Event


class LLM:
    chat_models: BaseChatModel

    def __init__(self) -> None:
        self.llm_available = Event()

    @property
    def llm(self) -> BaseChatModel:
        if not self.llm_available.is_set():
            self.llm_available.wait()
        return self.chat_models

    @llm.setter
    def llm(self, llm: BaseChatModel):
        self.llm_available.set()
        self.chat_models = llm

    @property
    def available(self) -> bool:
        return self.llm_available.is_set()

    def remove_llm(self):
        del self.chat_models
        self.llm_available = Event()


chat_model = LLM()
