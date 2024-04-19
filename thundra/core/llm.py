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
    @property
    def available(self) -> bool:
        return hasattr(self, 'chat_models')

    @llm.setter
    def set_llm(self, llm: BaseChatModel):
        self.chat_models = llm


chat_model = LLM()
