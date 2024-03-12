from neonize.proto.Neonize_pb2 import Message
from neonize.client import NewClient, MediaType
import magic
from neonize.utils.ffmpeg import FFmpeg
from thundra.agents import agent, tool, ExtendedTextMessage
from neonize.proto.def_pb2 import AudioMessage, VideoMessage
from thundra.utils import download_media, get_user_id
from thundra.storage.file import storage
import json
from shazamio import Shazam
import json
import asyncio


async def main(data: bytes):
    shazam = Shazam()
    return await shazam.recognize_song(data)


@agent.tool(str, ExtendedTextMessage, AudioMessage, VideoMessage)
def ShazamAudioIdentifier(client: NewClient, message: Message):
    @tool("audioIndentifier")
    def imageAnswering(query: str):
        'Empower to Identify the music, query input must be json format with keys file_id(from VideoMessage or AudioMessage) and question, file_id will "" if no media corelation context previous message'
        buf_file = None
        query_json = json.loads(query)
        try:
            buf_file = download_media(
                client, message.Message, (AudioMessage, VideoMessage)
            )
        except Exception as e:
            file_id = query_json.get("file_id")
            user_id = get_user_id(message)
            if file_id:
                file = storage.get_file(user_id, file_id)
                if file.type is VideoMessage:
                    buf_file = file.download(client, MediaType.MediaVideo)
                    with FFmpeg(buf_file) as ffmpeg:
                        buf_file = ffmpeg.to_mp3()
                else:
                    buf_file = file.download(client, MediaType.MediaAudio)
            else:
                for file in storage.get_files_by_type(
                    user_id, (VideoMessage, AudioMessage)
                ):
                    if file:
                        buf_file = file.download(
                            client,
                            MediaType.MediaAudio
                            if file.type is AudioMessage
                            else MediaType.MediaVideo,
                        )
                        if file.type is VideoMessage:
                            with FFmpeg(buf_file) as ffmpeg:
                                buf_file = ffmpeg.to_mp3()
        if not buf_file:
            return "anda belum mengirimkan video/audio"
        r = asyncio.run(main(buf_file))
        if r.get("track"):
            return f"judul: {r['track']['title']}\nsubjudul:{r['track']['subtitle']}\ntype:{r['track']['type']}\n\nberitahu mereka apakah ingin mencarinya di youtube atau tidak?"
        else:
            return "judul lagu tidak ditemukan"

    return imageAnswering
