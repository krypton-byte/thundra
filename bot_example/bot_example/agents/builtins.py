from thundra.agents import agent
from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message
from neonize.proto.def_pb2 import (
    ExtendedTextMessage,
    ImageMessage,
    VideoMessage,
    StickerMessage,
)
from thundra.utils import download_media, get_user_id
from neonize.utils.enum import MediaType
from thundra.storage import storage
from thundra.core import llm, memory
from langchain.tools import tool
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate


@agent.tool(str, ExtendedTextMessage, ImageMessage, VideoMessage)
def sticker(client: NewClient, message: Message):
    @tool("stickerMaker", return_direct=True)
    def sticker(file_id: str):
        'usefull to create sticker from Image, query input must be file_id from last of message or "" if not have'
        buf_file = None
        try:
            buf_file = download_media(
                client, message.Message, (ImageMessage, VideoMessage, StickerMessage)
            )
        except Exception as e:
            user_id = get_user_id(message)
            if file_id:
                buf_file = storage.get_file(user_id, file_id).download(
                    client, MediaType.MediaImage
                )
            else:
                for file in storage.get_files_by_type(
                    user_id, (ImageMessage, VideoMessage, StickerMessage)
                ):
                    if file:
                        buf_file = file.download(
                            client,
                            (
                                MediaType.MediaImage
                                if file.type in [ImageMessage, StickerMessage]
                                else MediaType.MediaVideo
                            ),
                        )
        if not buf_file:
            return "anda belum mengirimkan gambar/video"
        if buf_file:
            client.send_sticker(message.Info.MessageSource.Chat, buf_file)
            return "Sticker Berhasil Di Upload"
        else:
            return "File Tidak ditemukan"

    return sticker


@agent.tool()
def remove_context(client: NewClient, message: Message):
    @tool("ResetChat")
    def execute(query: str):
        'ResetChat empowers you to reset your ongoing conversation or seamlessly transition to a new topic., query input must be new topik or "" if not have'
        user_id = get_user_id(message)
        memory.clear_history(user_id)
        if query:
            return LLMChain(
                llm=llm,
                prompt=PromptTemplate(
                    template="mari kita bahas {question}", input_variables=["question"]
                ),
            ).invoke({"question": query})["text"]
        return "oke mau bahas apa?"

    return execute
