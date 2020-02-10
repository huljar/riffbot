from abc import ABC, abstractmethod
from typing import Generator


class Endpoint(ABC):
    @abstractmethod
    def stream_chunks(self) -> Generator[bytes, None, None]:
        pass

    @abstractmethod
    def get_chunk_size(self) -> int:
        pass

    @abstractmethod
    def get_song_description(self) -> str:
        pass
