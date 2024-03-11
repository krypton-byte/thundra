from ..types import MediaMessageType
from typing import Iterable, Optional, Generator
from dataclasses import dataclass
from neonize.client import NewClient
from neonize.utils.enum import MediaType


@dataclass
class File:
    url: str
    mimetype: str
    fileSha256: bytes
    fileLength: int
    mediaKey: bytes
    fileEncSha256: bytes
    directPath: str
    mediaKeyTimestamp: int
    type: type
    viewOnce: Optional[bool] = None
    caption: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    seconds: Optional[int] = None
    ptt: Optional[bool] = None
    pageCount: Optional[int] = None
    isAnimated: Optional[bool] = None

    @classmethod
    def from_message(cls, message: MediaMessageType):
        return cls(
            **{
                attr: (getattr(message, attr) if hasattr(message, attr) else None)
                for attr in cls.__dataclass_fields__.keys()
                if hasattr(message, attr)
            },
            type=type(message),
        )

    def download(self, client: NewClient, mediatype: MediaType) -> bytes:
        return client.download_media_with_path(
            direct_path=self.directPath,
            enc_file_hash=self.fileEncSha256,
            file_hash=self.fileSha256,
            file_length=self.fileLength,
            media_key=self.mediaKey,
            media_type=mediatype,
            mms_type="",
        )


class FileRegistry(dict[str, File]):
    def update(self, id: str, data: File, max_data: int):  # type: ignore
        n = self.__len__() - max_data
        if n > 0:
            for _, k in zip(range(n), self.keys()):
                self.pop(k)
        super().update({id: data})


@dataclass
class StorageRegistry(dict[str, FileRegistry]):
    max_files: int = 10

    def save(self, user_id: str, file_id: str, file: File):
        get = self.get(user_id)
        if not get:
            self.update({user_id: FileRegistry()})
        self[user_id].update(file_id, file, self.max_files)

    def get_file(self, user_id: str, file_id: str) -> File:
        return self[user_id][file_id]

    def get_files(self, user_id: str) -> FileRegistry:
        return self[user_id]

    def get_files_by_type(
        self, user_id: str, types: Iterable[type]
    ) -> Generator[File, None, None]:
        files = self[user_id]
        for id_file in reversed(self[user_id]):
            file = files[id_file]
            if file.type in types:
                yield files[id_file]


storage = StorageRegistry(10)
