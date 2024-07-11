from pathlib import Path
from neonize.client import NewClient
from neonize.proto.Neonize_pb2 import Message
from neonize.types import InteractiveMessage
from pydantic import BaseModel, Field
from thundra.button import create_button_message, ListButtonV2, RowV2, create_carousel_message
from thundra.command import Command, command
from thundra.utils import ChainMessage
from thundra.button.v2 import ListButtonV2, QuickReplyV2, RowV2, SectionV2
from concurrent.futures import ThreadPoolExecutor
from pytube import Search, YouTube
import sys
sys.path.insert(0, Path(__file__).parent.parent.__str__())
from agents.yt import convert_size, parse_duration


class AudioYT(BaseModel):
    mime_type: str = Field()
    abr: int = Field()
    url: str = Field()


class VideoYT(BaseModel):
    fps: int = Field()
    vcodec: str = Field()
    res: str = Field()
    mime_type: str = Field()
    url: str = Field()


class AudioSection(SectionV2[AudioYT]):
    event_id = "audio_section"

    def on_click(self, client: NewClient, message: Message, param: AudioYT):
        client.send_audio(message.Info.MessageSource.Chat, param.url)


class VideoSection(SectionV2[VideoYT]):
    event_id = "video_section"

    def on_click(self, client: NewClient, message: Message, param: VideoYT):
        client.send_video(message.Info.MessageSource.Chat, param.url)

def send_video_download_list(client: NewClient, message: Message, url: str):
    yt = YouTube(url)
    stream = yt.streams
    audio_button = [
        RowV2[AudioYT](
            title=i.subtype,
            header=i.bitrate.__str__(),
            description=convert_size(i.filesize_approx),
            params=AudioYT(mime_type=i.mime_type, abr=i.bitrate, url=i.url),
        )
        for i in stream.filter(type="audio")
    ]
    video_button = [
        RowV2[VideoYT](
            header=i.resolution.__str__(),
            title=i.fps.__str__(),
            description=convert_size(i.filesize_approx),
            params=VideoYT(
                fps=i.fps,
                vcodec=i.video_codec,
                mime_type=i.mime_type,
                res=i.resolution,
                url=i.url,
            ),
        )
        for i in stream.filter(type="video")
    ]
    msg = client.build_image_message(yt.thumbnail_url)
    client.send_message(
        message.Info.MessageSource.Chat,
        create_button_message(
            InteractiveMessage(
                body=InteractiveMessage.Body(
                    text=f"Duration: {parse_duration(yt.length)}\nViews: {yt.views}\n\n{yt.description or ''}"
                ),
                header=InteractiveMessage.Header(
                    title=yt.title,
                    imageMessage=msg.imageMessage,
                    hasMediaAttachment=True,
                ),
                footer=InteractiveMessage.Footer(text="@thundra-ai"),
            ),
            buttons=[
                ListButtonV2(
                    title="Download",
                    sections=[
                        VideoSection(
                            title="Video", highlight_label="Video", rows=video_button
                        ),
                        AudioSection(
                            title="Audio", highlight_label="Audio", rows=audio_button
                        ),
                    ],
                )
            ],
        ),
    )
@command.register(Command("yt"))
def yt(client: NewClient, message: Message):
    url = ChainMessage.extract_text(message.Message)[3:].strip()
    send_video_download_list(client, message, url)


class VideoMetadata(BaseModel):
    url: str = Field()

class GetItem(QuickReplyV2[VideoMetadata]):
    event_id= "get_video"
    def on_click(self, client: NewClient, message: Message, params: VideoMetadata) -> None:
        send_video_download_list(
            client, message, params.url
        )



@command.register(Command("ytsearch"))
def yt_search(client: NewClient, message: Message):
    query = ChainMessage.extract_text(message.Message)[9:].strip()
    search = Search(query)
    def create_card(yt: YouTube):
        return create_button_message(
            InteractiveMessage(
                header=InteractiveMessage.Header(
                    imageMessage=client.build_image_message(yt.thumbnail_url).imageMessage,
                    title=yt.title,
                    subtitle='',
                    hasMediaAttachment=True
                ),
                body=InteractiveMessage.Body(text=f"{yt.title}\nduration: {parse_duration(yt.length)}\ndescription: {yt.description}"),
                footer=InteractiveMessage.Footer(text=yt.author)
            ),
            [
                GetItem(
                    display_text="Download",
                    params=VideoMetadata(
                        url=yt.watch_url
                    )
                )
            ],
            direct_send=False
        )
    cards = []
    results = search.results
    if results:
        with ThreadPoolExecutor(max_workers=5) as th:
            for item in th.map(create_card, results[:5]):
                cards.append(
                    item
                )
        client.send_message(
            message.Info.MessageSource.Chat,
            create_carousel_message(
                InteractiveMessage(
                    body=InteractiveMessage.Body(text="hasil pencarian youtube dengan query %r" % query)
                ),
                cards=cards
            )
        )
    else:
        client.reply_message(
            "Video tidak ditemukan",
            message
        )
