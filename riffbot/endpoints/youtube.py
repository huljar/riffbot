import logging
import pafy
import requests
from typing import Generator, Union
import re

from .endpoint import Endpoint, InvalidEndpointError

_logger = logging.getLogger(__name__)

_range_variants = {
    "&range={}-{}": re.compile("^https://.*\\.googlevideo\\.com/videoplayback\\?([^/]+=[^/]*&)*[^/]+=[^/]*$"),
    "range/{}-{}/": re.compile("^https://.*\\.googlevideo\\.com/videoplayback/([^&=?]+/)+$")
}


class YouTubeEndpoint(Endpoint):
    def __init__(self, url_or_pafy: Union[str, pafy.pafy.Pafy]):
        self._video = pafy.new(url_or_pafy) if type(url_or_pafy) is str else url_or_pafy
        _logger.debug(f"Constructing: {self._video.title}")
        self._initialized = False

    def initialize(self):
        self._stream = self._video.getbestaudio(preftype="m4a")
        self._initialized = True

    def is_initialized(self):
        return self._initialized

    def stream_chunks(self, chunk_size: int) -> Generator[bytes, None, None]:
        if not self.is_initialized():
            self.initialize()

        url = self._stream.url_https
        template = self._get_url_variant(url)
        file_size = self._stream.get_filesize()
        with requests.Session() as session:
            for i in range(0, file_size, chunk_size):
                chunk_url = url + template.format(i, min(i + chunk_size - 1, file_size - 1))
                response = session.get(chunk_url)
                yield response.content

    def get_preferred_chunk_size(self) -> int:
        return 65536  # 64 KB

    def get_song_description(self) -> str:
        return self._video.title

    def get_bit_rate(self) -> int:
        if not self.is_initialized():
            self.initialize()

        return self._stream.rawbitrate

    def get_length(self) -> int:
        return self._video.length

    def get_youtube_id(self) -> str:
        return self._video.videoid

    def _get_url_variant(self, url: str) -> str:
        for template, regex in _range_variants.items():
            if regex.match(url) is not None:
                return template
        raise InvalidEndpointError()
