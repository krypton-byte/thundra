from thundra.command import command, Command, MessageType, Owner
from neonize import NewClient
from neonize.proto.Neonize_pb2 import Message
import time
from thundra.agents import agent
from thundra.middleware import middleware
from thundra.utils import ChainMessage, get_user_id
from thundra.storage import storage
import tempfile
import graphviz, os
from neonize.proto.def_pb2 import (
    ExtendedTextMessage,
)


@command.register(name="owner test", filter=Command("owner") & Owner())
def owner_test(client: NewClient, message: Message):
    client.reply_message("owner", message)


@command.register(
    name="ping", filter=Command("ping") & (MessageType(ExtendedTextMessage, str))
)
def ping(client: NewClient, message: Message):
    client.reply_message("pong", quoted=message)


@command.register(name="file", filter=Command("file"))
def my_file(client: NewClient, message: Message):
    client.reply_message(storage[get_user_id(message)].__str__(), message)


@command.register(name="debug", filter=Command("debug"))
def debug(client: NewClient, message: Message):
    client.reply_message(
        message.Message.extendedTextMessage.contextInfo.quotedMessage.__str__(), message
    )


@command.register(name="shell", filter=Command(">", prefix="") & Owner())
def evaluater(client: NewClient, message: Message):
    msg = ""
    try:
        msg += eval(ChainMessage.extract_text(message.Message)[1:].strip()).__str__()
    except Exception as e:
        msg += "Exception:" + e.__str__()
        raise e
    client.reply_message(msg, message)


@command.register(name="graph", filter=Command("graph"))
def graph(client: NewClient, message: Message):
    gv = command.combine_graph(middleware, command, agent)
    fname = tempfile.gettempdir() + "/" + time.time().__str__()
    outfile = tempfile.gettempdir() + "/" + time.time().__str__() + "_out.jpeg"
    with open(fname, "w") as file:
        file.write(gv)
    client.send_image(
        message.Info.MessageSource.Chat,
        graphviz.render("circo", "jpeg", fname, outfile=outfile),
    )
    os.remove(fname)
    os.remove(outfile)
