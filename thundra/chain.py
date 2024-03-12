from langchain_community.tools.wolfram_alpha import WolframAlphaQueryRun
from langchain_community.utilities.wolfram_alpha import WolframAlphaAPIWrapper
from langchain.agents import (
    initialize_agent,
    create_json_chat_agent,
    create_structured_chat_agent,
    AgentExecutor,
)
from langchain.prompts.chat import ChatPromptTemplate
from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message
from .utils import ChainMessage, get_message_type
from .agents import agent, tool
from .core.llm import llm
import os
# from .agents import Knowledge
# os.environ['wolfram_alpha_appid'] = "9YG4YH-JUT4XLVWQ8"


def execute_agent(memory, client: NewClient, message: Message):
    tools = [
        tool.agent(client, message)
        for tool in agent.filter_tools(get_message_type(message.Message).__class__)
    ]
    return initialize_agent(
        agent="chat-conversational-react-description",
        tools=tools,
        llm=llm,
        verbose=True,
        max_iterations=3,
        early_stopping_method="generate",
        memory=memory,
    )
