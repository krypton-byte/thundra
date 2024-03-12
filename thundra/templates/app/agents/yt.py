from pytube import YouTube, Search
from thundra.agents import agent, tool, ExtendedTextMessage
from neonize.utils.ffmpeg import FFmpeg
from thundra.utils import convert_size
from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message
from pytube import Search, YouTube, Stream
import os
import tempfile


def parse_duration(time: int):
    hours = time // 60**2
    minutes = (time - hours * 60**2) // 60
    duration = time % 60
    return f"{hours:02}:{minutes:02}:{duration:02}"


def search_music_yt(query: str) -> str:
    data = 'anda harus mengirimkannya secara eksplisit dan keseluruhan tidak hanya official saja dan tambahkan pesan "jika ingin mendownload anda bisa mereply sesuai nomer yg ingin di download"\n\n'
    video: YouTube
    for index, video in enumerate(Search(query).results, 1):
        data += f"""{index}. {video.title}\n  author: {video.author}\n  durasi: {parse_duration(video.length)}\n  link: {video.watch_url}\n"""
    return data


@agent.tool(str, ExtendedTextMessage)
def SearchYT(client: NewClient, message: Message):
    @tool("SearchMusicFromYT")
    def youtube_search(query: str):
        "Empower to search music from youtube"
        return search_music_yt(query)

    return youtube_search


@agent.tool(str, ExtendedTextMessage)
def YoutubeMusicDownloader(client: NewClient, message: Message):
    @tool("YoutubeMusicDownloader")
    def youtube_music_downloader(url: str):
        "Empower to download music from youtube by youtube url"
        selected: Stream = YouTube(url).streams.filter(type="audio").order_by("abr")[0]
        file = selected.download(tempfile.gettempdir())
        print("file: ", file)
        with FFmpeg(file) as music:
            audio = music.to_mp3()
            client.send_audio(
                message.Info.MessageSource.Chat, file=audio, quoted=message
            )
        os.remove(file)
        return f"{selected.title}\nukuran: {convert_size(len(audio))}\ntype:{selected.type}"

    return youtube_music_downloader
