from langchain.agents import AgentExecutor, initialize_agent
from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message
from .utils import get_message_type
from .agents import agent
from .core.llm import chat_model


def execute_agent(memory, client: NewClient, message: Message) -> AgentExecutor:
    """
    Execute an agent based on the incoming message.

    This function initializes and executes an agent based on the provided message and client.

    :param memory: Memory object for the agent execution.
    :type memory: Any
    :param client: Client object for communication.
    :type client: NewClient
    :param message: Incoming message to process.
    :type message: Message
    :return: AgentExecutor object for the executed agent.
    :rtype: AgentExecutor
    """
    tools = [
        tool.agent(client, message)
        for tool in agent.filter_tools(get_message_type(message.Message).__class__)
    ]
    return initialize_agent(
        agent="chat-conversational-react-description",
        tools=tools,
        llm=chat_model.llm,
        verbose=True,
        max_iterations=3,
        early_stopping_method="generate",
        memory=memory,
    )
