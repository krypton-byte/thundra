from ..types import MediaMessageType
from typing import Iterable, Optional, Generator
from dataclasses import dataclass
from neonize.client import NewClient
from neonize.utils.enum import MediaType


@dataclass
class File:
    """
    A class representing a file with various attributes related to its metadata and content.

    Attributes:
        url (str): The URL of the file.
        mimetype (str): The MIME type of the file.
        fileSha256 (bytes): The SHA-256 hash of the file.
        fileLength (int): The length of the file in bytes.
        mediaKey (bytes): The media key for encryption.
        fileEncSha256 (bytes): The encrypted SHA-256 hash of the file.
        directPath (str): The direct path to the file.
        mediaKeyTimestamp (int): The timestamp for the media key.
        type (type): The type of the file.
        viewOnce (Optional[bool]): Indicates if the file is view-once media. Default is None.
        caption (Optional[str]): The caption of the file. Default is None.
        height (Optional[int]): The height of the media (if applicable). Default is None.
        width (Optional[int]): The width of the media (if applicable). Default is None.
        seconds (Optional[int]): The duration of the media in seconds (if applicable). Default is None.
        ptt (Optional[bool]): Indicates if the file is a push-to-talk audio. Default is None.
        pageCount (Optional[int]): The number of pages in the file (if applicable). Default is None.
        isAnimated (Optional[bool]): Indicates if the file is an animated media. Default is None.
    """
    URL: str
    mimetype: str
    fileSHA256: bytes
    fileLength: int
    mediaKey: bytes
    fileEncSHA256: bytes
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
    def from_message(cls, message: MediaMessageType) -> 'File':
        """
        Create a File instance from a MediaMessageType message.

        :param message: The message containing media information.
        :type message: MediaMessageType
        :return: An instance of the File class.
        :rtype: File
        """        
        return cls(
            **{
                attr: (getattr(message, attr) if hasattr(message, attr) else None)
                for attr in cls.__dataclass_fields__.keys()
                if hasattr(message, attr)
            },
            type=type(message),
        )

    def download(self, client: NewClient, mediatype: MediaType) -> bytes:
        """
        Download the file using the provided client and media type.

        :param client: The client to use for downloading the file.
        :type client: NewClient
        :param mediatype: The type of media being downloaded.
        :type mediatype: MediaType
        :return: The downloaded file as bytes.
        :rtype: bytes
        """        
        return client.download_media_with_path(
            direct_path=self.directPath,
            enc_file_hash=self.fileEncSHA256,
            file_hash=self.fileSHA256,
            file_length=self.fileLength,
            media_key=self.mediaKey,
            media_type=mediatype,
            mms_type="",
        )


class FileRegistry(dict[str, File]):
    """
    A registry to manage files, allowing updates while maintaining a maximum number of stored files.
    """

    def update(self, id: str, data: File, max_data: int):  # type: ignore
        """
        Update the registry with a new file, ensuring the number of files does not exceed `max_data`.

        :param id: The unique identifier for the file.
        :type id: str
        :param data: The file to be added or updated in the registry.
        :type data: File
        :param max_data: The maximum number of files allowed in the registry.
        :type max_data: int
        """        
        n = self.__len__() - max_data
        if n > 0:
            for _, k in zip(range(n), self.keys()):
                self.pop(k)
        super().update({id: data})


@dataclass
class StorageRegistry(dict[str, FileRegistry]):
    """
    A storage registry to manage user-specific file registries.

    Attributes:
        max_files (int): The maximum number of files allowed per user registry.
    """
    max_files: int = 10

    def save(self, user_id: str, file_id: str, file: File):
        """
        Save a file in the user's registry, ensuring the number of files does not exceed `max_files`.

        :param user_id: The unique identifier for the user.
        :type user_id: str
        :param file_id: The unique identifier for the file.
        :type file_id: str
        :param file: The file to be saved in the registry.
        :type file: File
        """        
        get = self.get(user_id)
        if not get:
            self.update({user_id: FileRegistry()})
        self[user_id].update(file_id, file, self.max_files)

    def get_file(self, user_id: str, file_id: str) -> File:
        """
        Retrieve a specific file from the user's registry.

        :param user_id: The unique identifier for the user.
        :type user_id: str
        :param file_id: The unique identifier for the file.
        :type file_id: str
        :return: The requested file.
        :rtype: File
        """        
        return self[user_id][file_id]

    def get_files(self, user_id: str) -> FileRegistry:
        """
        Retrieve all files from the user's registry.

        :param user_id: The unique identifier for the user.
        :type user_id: str
        :return: The registry of files for the user.
        :rtype: FileRegistry
        """        
        return self[user_id]

    def get_files_by_type(
        self, user_id: str, types: Iterable[type]
    ) -> Generator[File, None, None]:
        """
        Retrieve files of specific types from the user's registry.

        :param user_id: The unique identifier for the user.
        :type user_id: str
        :param types: The types of files to retrieve.
        :type types: Iterable[type]
        :yield: The files of the specified types.
        :rtype: Generator[File, None, None]
        """    
        files = self[user_id]
        for id_file in reversed(self[user_id]):
            file = files[id_file]
            if file.type in types:
                yield files[id_file]


storage = StorageRegistry(10)
