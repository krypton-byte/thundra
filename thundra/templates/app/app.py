from pathlib import Path
from langchain_openai import ChatOpenAI
from neonize.client import DeviceProps, NewClient
from neonize.events import MessageEv, ConnectedEv
import yaml
from neonize.utils.jid import Jid2String, JIDToNonAD
from thundra.chain import execute_agent
from thundra.storage import storage, File
from thundra.profiler import Profile, Profiler
from thundra.types import MediaMessageType, MessageWithContextInfoType
from thundra.core.memory import memory
from thundra.utils import ChainMessage, get_tag, get_user_id, get_message_type
from thundra.middleware import middleware
from thundra.core import chat_model
from thundra.button import button_registry
from neonize.events import event
import signal

# evaluate all module
from thundra.evaluater import evaluate_module

evaluate_module(Path(__file__).parent / "commands")
evaluate_module(Path(__file__).parent / "middleware")
evaluate_module(Path(__file__).parent / "agents")
from thundra.command import command
from thundra.workdir import workdir, config_toml

app = NewClient(
    config_toml["thundra"]["db"],
    props=DeviceProps(
        os=config_toml["thundra"]["name"], platformType=DeviceProps.PlatformType.SAFARI
    ),
)

signal.signal(signal.SIGINT, lambda *_: event.set())

# set your llm here
# example:
# chat_model.llm = ChatOpenAI(model="", api_key="")


@app.event(ConnectedEv)
def connected(client: NewClient, connect: ConnectedEv):
    me = app.get_me()
    me_jid = me.JID
    if workdir.workspace_dir.__str__() == workdir.db.__str__():
        Profiler.add_profile(
            Profile(
                workspace=workdir.workspace_dir.__str__(),
                phonenumber=me_jid.User,
                pushname=me.PushName,
            )
        )
    setattr(client, "my_tag", Jid2String(JIDToNonAD(me_jid)))
    setattr(client, "my_number", me_jid.User)


def save_to_storage(message: MessageEv):
    try:
        msg = get_message_type(message.Message)
        if isinstance(msg, MessageWithContextInfoType):
            get_msg_type = get_message_type(msg.contextInfo.quotedMessage)
            if isinstance(get_msg_type, MediaMessageType):
                storage.save(
                    get_user_id(message),
                    message.Info.ID,
                    File.from_message(get_msg_type),
                )
    except IndexError:
        return


@app.event(MessageEv)
def on_message(client: NewClient, message: MessageEv):
    r = middleware.execute(client, message)
    if r in [False, None]:
        cmd = command.execute(client, message)
        if not cmd:
            button_registry.click(client, message)
        if not cmd and chat_model.available:
            save_to_storage(message)
            chat = message.Info.MessageSource.Chat
            sender = message.Info.MessageSource.Sender
            context = memory.get_memory(get_user_id(message))
            if sender.User == chat.User:
                yamlx = yaml.dump(ChainMessage(message.Message, message).to_json())
                client.send_message(
                    chat,
                    execute_agent(context, client, message).invoke(yamlx)["output"],
                )
            elif client.my_tag in get_tag(message.Message):
                save_to_storage(message)
                yamlx = yaml.dump(
                    ChainMessage(message.Message, message).to_json()
                ).replace(f"@{client.my_number}".strip(), "")
                client.reply_message(
                    execute_agent(context, client, message).invoke(yamlx)["output"],
                    quoted=message,
                )


if __name__ == "__main__":
    app.connect()
