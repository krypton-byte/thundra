from typing import Dict
from dataclasses import dataclass
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.schema import SystemMessage
from langchain_community.chat_message_histories.in_memory import ChatMessageHistory
from ..workdir import workdir, config_toml

import re


def build_system_message() -> str:
    """
    Builds the system message by replacing placeholders in the base system message
    with corresponding values from the configuration.

    :return: The formatted system message.
    :rtype: str
    """
    pattern = r"\{([^}]*)\}"
    base_system_message = config_toml["openai"]["agent"]["system_message"]
    matches = re.finditer(pattern, config_toml["openai"]["agent"]["system_message"])
    system_message_format = ""
    end_index = 0
    config_format_json = workdir.config_format(config_toml)
    for match in matches:
        start_index = match.start()
        system_message_format += base_system_message[end_index:start_index]
        end_index = match.end()
        system_message_format += config_format_json.get(
            base_system_message[start_index + 1 : end_index - 1], ""
        )
    system_message_format += base_system_message[end_index:]
    return system_message_format


@dataclass
class UserMemory:
    """
    Represents the memory for a user, including the system message and a conversation buffer.

    :param system_message: The initial system message.
    :type system_message: SystemMessage
    :param k: The size of the conversation buffer.
    :type k: int
    :param memory: The conversation buffer memory.
    :type memory: ConversationBufferWindowMemory
    """

    system_message: SystemMessage
    k: int
    memory: ConversationBufferWindowMemory

    @classmethod
    def create_ai_instance(cls, k: int) -> "UserMemory":
        """
        Creates an instance of UserMemory with the specified buffer size.

        :param k: The size of the conversation buffer.
        :type k: int
        :return: A new instance of UserMemory.
        :rtype: UserMemory
        """
        system_message = SystemMessage(content=build_system_message())
        return cls(
            system_message=system_message,
            k=k,
            memory=ConversationBufferWindowMemory(
                memory_key="chat_history",
                k=k,
                return_messages=True,
                chat_memory=ChatMessageHistory(messages=[system_message]),
            ),
        )

    def clear_history(self):
        """
        Clears the chat history while retaining the initial system message.
        """
        self.memory.chat_memory.messages.clear()
        self.memory.chat_memory.messages.append(self.system_message)

    def get_memory(self) -> ConversationBufferWindowMemory:
        """
        Retrieves the current conversation buffer memory, ensuring its size does not exceed 2*k messages.

        :return: The conversation buffer memory.
        :rtype: ConversationBufferWindowMemory
        """
        if self.memory.chat_memory.messages.__len__() > self.k * 2 - 1:
            self.memory.chat_memory.messages = [
                self.system_message,
                *self.memory.chat_memory.messages[: -self.k * 2],
            ]
        return self.memory


class AIMemory:
    """
    Manages the memory for multiple users, each with their own conversation buffer.

    :param k: The default size of the conversation buffer.
    :type k: int, optional, default=13
    """

    def __init__(self, k: int = 13):
        self.k = k
        self.memory: Dict[str, UserMemory] = {}

    def get_memory(self, id: str) -> ConversationBufferWindowMemory:
        """
        Retrieves the memory for a given user. If the user does not have memory initialized,
        it creates a new instance.

        :param id: The identifier for the user.
        :type id: str
        :return: The user's conversation buffer memory.
        :rtype: ConversationBufferWindowMemory
        """
        memoize = self.memory.get(id)
        if not memoize:
            memoize = UserMemory.create_ai_instance(
                config_toml["openai"]["agent"]["memory_size"]
            )
            self.memory[id] = memoize
        return memoize.memory

    def delete_memory(self, id: str):
        """
        Deletes the memory for a given user.

        :param id: The identifier for the user.
        :type id: str
        """
        if self.memory.get(id):
            del self.memory[id]

    def clear_history(self, id: str):
        """
        Clears the chat history for a given user while retaining their initial system message.

        :param id: The identifier for the user.
        :type id: str
        """
        if self.memory.get(id):
            self.memory[id].clear_history()


memory = AIMemory()
