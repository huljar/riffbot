from abc import ABC, abstractmethod
from typing import Generator


class InvalidEndpointError(Exception):
    pass


class Endpoint(ABC):
    @abstractmethod
    def stream_chunks(self) -> Generator[bytes, None, None]:
        pass

    @abstractmethod
    def get_preferred_chunk_size(self) -> int:
        pass

    @abstractmethod
    def get_song_description(self) -> str:
        pass

    @abstractmethod
    def get_bit_rate(self) -> int:
        pass

    @abstractmethod
    def get_length(self) -> int:
        """Get the length of the song in seconds"""
        pass
