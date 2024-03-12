from langchain.agents import initialize_agent
from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message
from .utils import get_message_type
from .agents import agent
from .core.llm import llm


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
