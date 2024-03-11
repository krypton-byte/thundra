from thundra.middleware import Middleware, middleware
from neonize import NewClient
from neonize.proto.Neonize_pb2 import Message
from thundra.storage.file import File
from thundra.utils import get_message_type, get_user_id
from thundra.storage import storage, File
from thundra.types import MediaMessageType


class SaveMediaMessage(Middleware):
    def run(self, client: NewClient, message: Message):
        msg = get_message_type(message.Message)
        if isinstance(msg, MediaMessageType):
            storage.save(
                get_user_id(message),
                message.Info.ID,
                File.from_message(msg),
            )


middleware.add(SaveMediaMessage)
