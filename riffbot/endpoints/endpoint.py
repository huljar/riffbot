from abc import ABC, abstractmethod
from typing import Generator, Optional


class InvalidEndpointError(Exception):
    pass


class Endpoint(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        pass

    @abstractmethod
    def stream_chunks(self) -> Generator[bytes, None, None]:
        pass

    @abstractmethod
    def get_song_description(self) -> str:
        pass

    @abstractmethod
    def get_bit_rate(self) -> Optional[int]:
        pass

    @abstractmethod
    def get_length(self) -> Optional[int]:
        """Get the length of the song in seconds"""
        pass
