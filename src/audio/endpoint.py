from abc import ABC, abstractmethod
from typing import Generator


class Endpoint(ABC):
    @abstractmethod
    def stream_chunks(self, chunk_size: int) -> Generator[bytes, None, None]:
        pass
