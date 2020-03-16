import logging
from typing import Generator, Optional

from gtts import gTTS
import requests

from .endpoint import Endpoint

_logger = logging.getLogger(__name__)


class TextToSpeechEndpoint(Endpoint):
    def __init__(self, text: str):
        _logger.debug("Initializing")
        self._text = text
        self._initialized = False

    def initialize(self):
        if not self._initialized:
            self._initialized = True
            self._gtts = gTTS(self._text, lang_check=False)

    def is_initialized(self):
        return self._initialized

    def stream_chunks(self) -> Generator[bytes, None, None]:
        if not self.is_initialized():
            self.initialize()

        with requests.Session() as session:
            for chunk_url in self._gtts.get_urls():
                yield session.get(chunk_url).content

    def get_song_description(self) -> str:
        return f"Text to speech: '{f'{self._text[:35]}…' if len(self._text) > 37 else self._text}'"

    def get_bit_rate(self) -> Optional[int]:
        return None

    def get_length(self) -> Optional[int]:
        return None
