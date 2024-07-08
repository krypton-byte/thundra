from langchain_core.language_models.chat_models import BaseChatModel
from threading import Event


class LLM:
    """
    A class to manage the lifecycle and availability of a language model (LLM) for chat.

    Attributes:
        chat_models (BaseChatModel): The chat model to be used.
        llm_available (Event): An event to signal the availability of the LLM.
    """

    chat_models: BaseChatModel

    def __init__(self) -> None:
        """
        Initialize the LLM class with an event to track the availability of the language model.
        """
        self.llm_available = Event()

    @property
    def llm(self) -> BaseChatModel:
        """
        Get the currently set language model. Waits if the model is not yet set.

        :return: The currently set language model.
        :rtype: BaseChatModel
        """
        if not self.llm_available.is_set():
            self.llm_available.wait()
        return self.chat_models

    @llm.setter
    def llm(self, llm: BaseChatModel):
        """
        Set the language model and signal its availability.

        :param llm: The language model to be set.
        :type llm: BaseChatModel
        """
        self.llm_available.set()
        self.chat_models = llm

    @property
    def available(self) -> bool:
        """
        Check if the language model is available.

        :return: True if the language model is available, False otherwise.
        :rtype: bool
        """
        return self.llm_available.is_set()

    def remove_llm(self):
        """
        Remove the currently set language model and reset its availability.
        """
        del self.chat_models
        self.llm_available = Event()


# Initialize the LLM instance
chat_model = LLM()
